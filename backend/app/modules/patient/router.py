import uuid
from typing import List
from fastapi import APIRouter, Depends, Request, status, Query
from sqlalchemy.orm import Session as DBSession

from app.db.session import get_db
from app.core.utils import parse_uuid
from app.modules.patient.service import PatientService
from app.modules.patient.schemas import (
    PatientCreateRequest,
    PatientResponse,
    PatientSessionSummaryItem,
    DoctorPatientSearchResult,
    DoctorPatientFullHistory,
)

router = APIRouter()
patient_service = PatientService()


# ============================================
# Patient Portal Endpoints
# ============================================

@router.post(
    "/patients",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or Retrieve Existing Patient Record",
    tags=["Patient Portal & History"],
)
def create_or_get_patient_endpoint(
    payload: PatientCreateRequest,
    request: Request,
    db: DBSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    patient = patient_service.create_or_get_patient(db=db, payload=payload, request_id=request_id)
    return PatientResponse(
        id=str(patient.id),
        national_health_id=patient.national_health_id,
        first_name=patient.first_name,
        last_name=patient.last_name,
        dob=patient.dob,
        gender=patient.gender,
        contact_number=patient.contact_number,
        created_at=patient.created_at,
    )


@router.get(
    "/patients/{patient_id}",
    response_model=PatientResponse,
    summary="Get Patient Demographic Details",
    tags=["Patient Portal & History"],
)
def get_patient_endpoint(
    patient_id: str,
    db: DBSession = Depends(get_db),
):
    parsed_patient_id = parse_uuid(patient_id)
    patient = patient_service.get_patient(db=db, patient_id=parsed_patient_id)
    return PatientResponse(
        id=str(patient.id),
        national_health_id=patient.national_health_id,
        first_name=patient.first_name,
        last_name=patient.last_name,
        dob=patient.dob,
        gender=patient.gender,
        contact_number=patient.contact_number,
        created_at=patient.created_at,
    )


@router.get(
    "/patients/{patient_id}/sessions",
    response_model=List[PatientSessionSummaryItem],
    summary="Get Past Consultation Session History for Returning Patient",
    tags=["Patient Portal & History"],
)
def get_patient_sessions_endpoint(
    patient_id: str,
    db: DBSession = Depends(get_db),
):
    parsed_patient_id = parse_uuid(patient_id)
    return patient_service.get_patient_sessions(db=db, patient_id=parsed_patient_id)


# ============================================
# Doctor Portal Endpoints
# ============================================

@router.get(
    "/doctors/patients/search",
    response_model=List[DoctorPatientSearchResult],
    summary="Search Patients by ABHA ID, UUID, Phone, or Name",
    tags=["Doctor Portal & Search"],
)
def search_patients_endpoint(
    query: str = Query(..., min_length=1, description="Search query string (ABHA, Phone, UUID, or Name)"),
    request: Request = None,
    db: DBSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None) if request else None
    return patient_service.search_patients_for_doctor(db=db, query=query, request_id=request_id)


@router.get(
    "/doctors/patients/{patient_id}/full-history",
    response_model=DoctorPatientFullHistory,
    summary="Get Full Longitudinal Clinical History for Doctor Review",
    tags=["Doctor Portal & Search"],
)
def get_doctor_patient_full_history_endpoint(
    patient_id: str,
    request: Request = None,
    db: DBSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None) if request else None
    parsed_patient_id = parse_uuid(patient_id)
    return patient_service.get_full_patient_history(db=db, patient_id=parsed_patient_id, request_id=request_id)
