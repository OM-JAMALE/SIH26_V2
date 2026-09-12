"""Unit tests for DocumentService (Module B)."""

import pytest
import uuid
import io
from fastapi import UploadFile, HTTPException
from starlette.datastructures import Headers
from app.modules.documents.service import DocumentService
from app.db.models.patient import Patient
from app.db.models.session import Session


@pytest.fixture
def test_session(db_session):
    """Fixture creating a test patient and session."""
    patient = Patient(
        id=uuid.uuid4(),
        first_name="Doc",
        last_name="Patient",
        gender="Female",
        dob="1980-01-01",
    )
    db_session.add(patient)
    db_session.commit()

    session = Session(
        id=uuid.uuid4(),
        patient_id=patient.id,
        mode="MODERN",
        disclaimer_acknowledged=True,
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.mark.anyio
async def test_upload_pdf(db_session, test_session):
    """Verify uploading a valid PDF document."""
    service = DocumentService("mock")
    content = b"%PDF-1.4 header content for testing lab report"
    upload_file = UploadFile(
        filename="report.pdf",
        file=io.BytesIO(content),
        headers=Headers({"content-type": "application/pdf"})
    )

    doc = await service.upload_and_process_document(
        session_id=test_session.id,
        file=upload_file,
        db=db_session
    )

    assert doc.id is not None
    assert doc.filename == "report.pdf"
    assert doc.mime_type == "application/pdf"
    assert doc.processing_status == "EXTRACTED"


@pytest.mark.anyio
async def test_upload_image(db_session, test_session):
    """Verify uploading valid PNG image."""
    service = DocumentService("mock")
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    upload_png = UploadFile(
        filename="scan.png",
        file=io.BytesIO(png_bytes),
        headers=Headers({"content-type": "image/png"})
    )

    doc_png = await service.upload_and_process_document(
        session_id=test_session.id,
        file=upload_png,
        db=db_session
    )
    assert doc_png.mime_type == "image/png"


@pytest.mark.anyio
async def test_reject_invalid_type(db_session, test_session):
    """Verify rejecting disallowed extension."""
    service = DocumentService("mock")
    invalid_bytes = b"unsupported binary content"
    upload_invalid = UploadFile(
        filename="malicious.exe",
        file=io.BytesIO(invalid_bytes),
        headers=Headers({"content-type": "application/x-msdownload"})
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.upload_and_process_document(
            session_id=test_session.id,
            file=upload_invalid,
            db=db_session
        )
    assert exc_info.value.status_code == 415


@pytest.mark.anyio
async def test_reject_oversized(db_session, test_session):
    """Verify rejecting files exceeding size limit."""
    service = DocumentService()
    large_bytes = b"A" * (26 * 1024 * 1024)
    upload_large = UploadFile(
        filename="big_report.pdf",
        file=io.BytesIO(large_bytes),
        headers=Headers({"content-type": "application/pdf"})
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.upload_and_process_document(
            session_id=test_session.id,
            file=upload_large,
            db=db_session
        )
    assert exc_info.value.status_code == 413
