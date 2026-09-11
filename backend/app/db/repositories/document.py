"""Document repository for document management operations."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models import Document
from app.db.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document model."""

    def __init__(self, db: Session):
        """Initialize document repository.
        
        Args:
            db: Database session
        """
        super().__init__(Document, db)

    def create_document(
        self,
        session_id: UUID,
        filename: str,
        file_path: str,
        mime_type: str,
        file_size: int
    ) -> Document:
        """Create a new document record.
        
        Args:
            session_id: Session UUID
            filename: Original filename
            file_path: Storage path
            mime_type: MIME type (application/pdf, image/png, image/jpeg)
            file_size: File size in bytes
            
        Returns:
            Created Document instance
        """
        return self.create(
            session_id=session_id,
            filename=filename,
            file_path=file_path,
            mime_type=mime_type,
            file_size=file_size,
            processing_status="PENDING"
        )

    def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID.
        
        Args:
            document_id: Document UUID
            
        Returns:
            Document instance or None
        """
        return self.get(document_id)

    def get_documents_by_session(self, session_id: UUID) -> List[Document]:
        """Get all documents for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            List of Document instances
        """
        return self.filter(session_id=session_id)

    def list_by_patient(self, patient_id: UUID) -> List[Document]:
        """Get all documents for a patient (across all sessions).
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            List of Document instances
        """
        from app.db.models import Session as SessionModel
        return self.db.query(Document).join(
            SessionModel, Document.session_id == SessionModel.id
        ).filter(SessionModel.patient_id == patient_id).all()

    def update_upload_status(
        self,
        document_id: UUID,
        processing_status: str,
        raw_text: Optional[str] = None
    ) -> Optional[Document]:
        """Update document processing status.
        
        Args:
            document_id: Document UUID
            processing_status: PENDING, EXTRACTED, or FAILED
            raw_text: Extracted text content (optional)
            
        Returns:
            Updated Document instance or None
        """
        update_dict = {"processing_status": processing_status}
        if raw_text is not None:
            update_dict["raw_text"] = raw_text
        return self.update(document_id, **update_dict)

    def mark_extracted(
        self,
        document_id: UUID,
        raw_text: str
    ) -> Optional[Document]:
        """Mark document as extracted.
        
        Args:
            document_id: Document UUID
            raw_text: Extracted text content
            
        Returns:
            Updated Document instance or None
        """
        return self.update_upload_status(document_id, "EXTRACTED", raw_text)

    def mark_failed(self, document_id: UUID) -> Optional[Document]:
        """Mark document extraction as failed.
        
        Args:
            document_id: Document UUID
            
        Returns:
            Updated Document instance or None
        """
        return self.update_upload_status(document_id, "FAILED")

    def get_pending_documents(self) -> List[Document]:
        """Get all documents pending extraction.
        
        Returns:
            List of Document instances with PENDING status
        """
        return self.filter(processing_status="PENDING")

    def get_extracted_documents(self, session_id: UUID) -> List[Document]:
        """Get all extracted documents for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            List of Document instances with EXTRACTED status
        """
        return self.db.query(Document).filter(
            Document.session_id == session_id,
            Document.processing_status == "EXTRACTED"
        ).all()

    def get_document_by_filename(
        self,
        session_id: UUID,
        filename: str
    ) -> Optional[Document]:
        """Get document by filename in session.
        
        Args:
            session_id: Session UUID
            filename: Document filename
            
        Returns:
            Document instance or None
        """
        return self.filter_one(session_id=session_id, filename=filename)

    def count_documents_by_session(self, session_id: UUID) -> int:
        """Get number of documents in a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Number of documents
        """
        return self.count(session_id=session_id)

    def count_documents_by_patient(self, patient_id: UUID) -> int:
        """Get total documents for a patient.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            Number of documents
        """
        from app.db.models import Session as SessionModel
        return self.db.query(Document).join(
            SessionModel, Document.session_id == SessionModel.id
        ).filter(SessionModel.patient_id == patient_id).count()

    def update_document(
        self,
        document_id: UUID,
        **kwargs
    ) -> Optional[Document]:
        """Update document information.
        
        Args:
            document_id: Document UUID
            **kwargs: Fields to update
            
        Returns:
            Updated Document instance or None
        """
        return self.update(document_id, **kwargs)

    def delete_document(self, document_id: UUID) -> bool:
        """Delete document (cascades to extracted entities).
        
        Args:
            document_id: Document UUID
            
        Returns:
            True if deleted
        """
        return self.delete(document_id)

    def document_exists(self, document_id: UUID) -> bool:
        """Check if document exists.
        
        Args:
            document_id: Document UUID
            
        Returns:
            True if exists
        """
        return self.exists(id=document_id)

    def get_total_file_size(self, session_id: UUID) -> int:
        """Get total file size for all documents in session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Total file size in bytes
        """
        documents = self.get_documents_by_session(session_id)
        return sum(doc.file_size for doc in documents)

    def get_documents_by_type(
        self,
        session_id: UUID,
        mime_type: str
    ) -> List[Document]:
        """Get documents by MIME type.
        
        Args:
            session_id: Session UUID
            mime_type: MIME type (application/pdf, image/png, image/jpeg)
            
        Returns:
            List of Document instances
        """
        return self.db.query(Document).filter(
            Document.session_id == session_id,
            Document.mime_type == mime_type
        ).all()

    def get_document_stats(self, session_id: UUID) -> dict:
        """Get document statistics for session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Dictionary with document statistics
        """
        documents = self.get_documents_by_session(session_id)
        if not documents:
            return {"session_id": str(session_id), "total_count": 0}
        
        extracted = [d for d in documents if d.processing_status == "EXTRACTED"]
        pending = [d for d in documents if d.processing_status == "PENDING"]
        failed = [d for d in documents if d.processing_status == "FAILED"]
        
        return {
            "session_id": str(session_id),
            "total_count": len(documents),
            "extracted_count": len(extracted),
            "pending_count": len(pending),
            "failed_count": len(failed),
            "total_size_bytes": sum(d.file_size for d in documents),
            "by_type": {
                "pdf": len([d for d in documents if d.mime_type == "application/pdf"]),
                "png": len([d for d in documents if d.mime_type == "image/png"]),
                "jpeg": len([d for d in documents if d.mime_type == "image/jpeg"])
            }
        }
