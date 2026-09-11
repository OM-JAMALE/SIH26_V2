import os
import uuid
import re
from typing import List, Optional, Dict, Any, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.logging import logger
from app.db.models.session import Session as SessionModel
from app.db.models.document import Document as DocumentModel
from app.db.models.extracted_entity import ExtractedEntity as ExtractedEntityModel
from app.db.models.audit_log import AuditLog as AuditLogModel
from app.ai.providers import get_llm_provider
from app.modules.documents.schemas import (
    DocumentExtractionSchema,
    DocumentUploadResponse,
    ExtractedEntityResponse,
    DocumentListResponse,
    EntityListResponse,
    DocumentDeleteResponse,
)
from app.modules.documents.lab_rules import evaluate_lab_result

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
}

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


class DocumentService:
    def __init__(self, provider_type: Optional[str] = None):
        self.llm_provider = get_llm_provider(provider_type)

    def _log_audit_event(
        self,
        db: DBSession,
        session_id: uuid.UUID,
        action: str,
        resource: str = "document",
        status_code: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        audit_log = AuditLogModel(
            session_id=session_id,
            user_id="system_document_pipeline",
            action=action,
            resource=resource,
            status=status_code,
            details=details or {},
            request_id=request_id or "document-service",
        )
        db.add(audit_log)
        db.commit()

    def _extract_raw_text(self, file_path: str, mime_type: str, raw_bytes: bytes) -> str:
        """Extracts text from file or returns text representation for OCR/vision."""
        # 1. Plain text extraction from PDF stream if possible
        if mime_type == "application/pdf":
            try:
                # Basic text extraction from PDF streams without external heavy dependencies
                text_chunks = []
                content_str = raw_bytes.decode("latin-1", errors="ignore")
                # Look for stream chunks in PDF
                for m in re.finditer(r"stream\r?\n(.*?)\r?\nendstream", content_str, re.DOTALL):
                    chunk = m.group(1)
                    # Extract printable characters
                    cleaned = "".join([c for c in chunk if 32 <= ord(c) <= 126 or c in "\n\r\t"])
                    if len(cleaned.strip()) > 10:
                        text_chunks.append(cleaned.strip())
                if text_chunks:
                    return "\n".join(text_chunks)
            except Exception as e:
                logger.warning(f"Failed basic PDF stream text extraction: {e}")

        # 2. Extract ASCII text strings from binary file (fallback extraction)
        try:
            printable_strings = re.findall(r"[A-Za-z0-9\s:,\.\-\<\>\/]{4,}", raw_bytes.decode("latin-1", errors="ignore"))
            candidate_text = " ".join(printable_strings)
            if len(candidate_text.strip()) > 30:
                return candidate_text[:4000]
        except Exception:
            pass

        return f"Medical document file: {os.path.basename(file_path)} (MIME: {mime_type})"

    async def upload_and_process_document(
        self,
        session_id: uuid.UUID,
        file: UploadFile,
        db: DBSession,
        request_id: Optional[str] = None,
    ) -> DocumentModel:
        # 1. Validate Session exists
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Session with ID '{session_id}' not found.", "code": "SESSION_NOT_FOUND"},
            )

        # 2. Validate MIME Type and Extension
        filename = file.filename or "unknown_document"
        ext = os.path.splitext(filename)[1].lower()
        content_type = (file.content_type or "").lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={
                    "error": f"Unsupported file extension '{ext}'. Allowed extensions are .pdf, .png, .jpg, and .jpeg.",
                    "code": "UNSUPPORTED_MEDIA_TYPE",
                    "allowed_types": ["application/pdf", "image/png", "image/jpeg"],
                },
            )

        if content_type and content_type not in ALLOWED_MIME_TYPES and content_type != "application/octet-stream":
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={
                    "error": f"Unsupported media type '{content_type}'. Allowed types are PDF, PNG, and JPEG.",
                    "code": "UNSUPPORTED_MEDIA_TYPE",
                    "allowed_types": ["application/pdf", "image/png", "image/jpeg"],
                },
            )

        # Normalize mime type
        normalized_mime = content_type if content_type in ALLOWED_MIME_TYPES else ("application/pdf" if ext == ".pdf" else "image/png")

        # 3. Read and Validate File Size
        content = await file.read()
        file_size = len(content)

        if file_size > settings.max_upload_size_bytes:
            max_mb = settings.max_upload_size_bytes // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": f"Uploaded file size ({file_size} bytes) exceeds maximum limit of {max_mb} MB.",
                    "code": "FILE_TOO_LARGE",
                    "max_size_bytes": settings.max_upload_size_bytes,
                },
            )

        # 4. Save file to disk safely
        doc_id = uuid.uuid4()
        safe_filename = re.sub(r"[^a-zA-Z0-9_\.-]", "_", filename)
        session_dir = os.path.join(settings.upload_dir, str(session_id))
        os.makedirs(session_dir, exist_ok=True)
        dest_path = os.path.join(session_dir, f"{doc_id}_{safe_filename}")

        with open(dest_path, "wb") as f:
            f.write(content)

        # 5. Persist Document entity with PENDING status
        doc = DocumentModel(
            id=doc_id,
            session_id=session_id,
            filename=safe_filename,
            file_path=dest_path,
            mime_type=normalized_mime,
            file_size=file_size,
            processing_status="PENDING",
            raw_text=None,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        self._log_audit_event(
            db=db,
            session_id=session_id,
            action="document_uploaded",
            resource=f"document:{doc.id}",
            details={"filename": safe_filename, "size": file_size, "mime": normalized_mime},
            request_id=request_id,
        )

        # 6. Extract Raw Text & Run Structured Extraction Pipeline
        try:
            raw_text = self._extract_raw_text(dest_path, normalized_mime, content)
            doc.raw_text = raw_text

            system_prompt = (
                "You are an expert clinical document digitization and structured information extraction engine.\n"
                "Your role is to extract all clinical findings, laboratory test results, medications, diagnoses, "
                "vital signs, and symptoms from medical records without speculation.\n"
                "Adhere strictly to the requested DocumentExtractionSchema schema."
            )
            user_prompt = (
                f"Extract structured clinical entities from this uploaded medical document ({safe_filename}).\n"
                f"Document text:\n{raw_text}"
            )

            extraction_result: DocumentExtractionSchema = self.llm_provider.generate_structured(
                prompt=user_prompt,
                system_prompt=system_prompt,
                schema_class=DocumentExtractionSchema,
            )

            # 7. Apply Deterministic Lab Abnormality Rules and Persist Entities
            created_entities = []
            for item in extraction_result.entities:
                is_abnormal = False
                ref_range = item.reference_range
                flag = None

                if item.entity_type == "LAB_RESULT":
                    is_abnormal, flag, ref_range = evaluate_lab_result(
                        test_name=item.entity_name,
                        raw_value=item.value,
                        numeric_value=item.numeric_value,
                        unit=item.unit,
                        reference_range=item.reference_range,
                    )

                meta = dict(item.metadata_json or {})
                if flag:
                    meta["deterministic_flag"] = flag
                    meta["rule"] = "is_abnormal = (value < low or value > high)"

                entity_model = ExtractedEntityModel(
                    id=uuid.uuid4(),
                    session_id=session_id,
                    document_id=doc.id,
                    entity_type=item.entity_type,
                    entity_name=item.entity_name,
                    value=item.value,
                    numeric_value=item.numeric_value,
                    unit=item.unit,
                    reference_range=ref_range,
                    is_abnormal=is_abnormal,
                    confidence_score=item.confidence_score,
                    metadata_json=meta,
                )
                db.add(entity_model)
                created_entities.append(entity_model)

            doc.processing_status = "EXTRACTED"
            db.commit()
            db.refresh(doc)

            self._log_audit_event(
                db=db,
                session_id=session_id,
                action="document_extracted",
                resource=f"document:{doc.id}",
                details={"entity_count": len(created_entities), "status": "EXTRACTED"},
                request_id=request_id,
            )

        except Exception as ex:
            logger.error(f"Error during document extraction for {doc.id}: {ex}")
            doc.processing_status = "FAILED"
            db.commit()
            db.refresh(doc)
            self._log_audit_event(
                db=db,
                session_id=session_id,
                action="document_extraction_failed",
                resource=f"document:{doc.id}",
                status_code="FAILED",
                details={"error": str(ex)},
                request_id=request_id,
            )

        return doc

    def list_session_documents(self, session_id: uuid.UUID, db: DBSession) -> List[DocumentModel]:
        from sqlalchemy.orm import joinedload
        return (
            db.query(DocumentModel)
            .options(joinedload(DocumentModel.extracted_entities))
            .filter(DocumentModel.session_id == session_id)
            .order_by(DocumentModel.created_at.desc())
            .all()
        )

    def get_document(self, session_id: uuid.UUID, document_id: uuid.UUID, db: DBSession) -> DocumentModel:
        from sqlalchemy.orm import joinedload
        doc = (
            db.query(DocumentModel)
            .options(joinedload(DocumentModel.extracted_entities))
            .filter(DocumentModel.session_id == session_id, DocumentModel.id == document_id)
            .first()
        )
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Document '{document_id}' not found in session '{session_id}'.", "code": "DOCUMENT_NOT_FOUND"},
            )
        return doc

    def list_session_entities(
        self,
        session_id: uuid.UUID,
        db: DBSession,
        abnormal_only: bool = False,
    ) -> List[ExtractedEntityModel]:
        query = db.query(ExtractedEntityModel).filter(ExtractedEntityModel.session_id == session_id)
        if abnormal_only:
            query = query.filter(ExtractedEntityModel.is_abnormal == True)
        return query.order_by(ExtractedEntityModel.created_at.asc()).all()

    def delete_document(
        self,
        session_id: uuid.UUID,
        document_id: uuid.UUID,
        db: DBSession,
        request_id: Optional[str] = None,
    ) -> DocumentDeleteResponse:
        doc = self.get_document(session_id, document_id, db)
        
        # Remove physical file if present
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except OSError as e:
                logger.warning(f"Could not remove file at {doc.file_path}: {e}")

        db.delete(doc)
        db.commit()

        self._log_audit_event(
            db=db,
            session_id=session_id,
            action="document_deleted",
            resource=f"document:{document_id}",
            request_id=request_id,
        )

        return DocumentDeleteResponse(
            success=True,
            message="Document and associated extracted entities deleted successfully.",
            document_id=document_id,
        )
