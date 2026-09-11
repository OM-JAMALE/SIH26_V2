"""Patient repository for patient-related operations."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models import Patient
from app.db.repositories.base import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    """Repository for Patient model."""

    def __init__(self, db: Session):
        """Initialize patient repository.
        
        Args:
            db: Database session
        """
        super().__init__(Patient, db)

    def create_patient(
        self,
        first_name: str,
        last_name: str,
        dob: str,
        gender: str,
        national_health_id: Optional[str] = None,
        contact_number: Optional[str] = None
    ) -> Patient:
        """Create a new patient.
        
        Args:
            first_name: Patient first name
            last_name: Patient last name
            dob: Date of birth (ISO format YYYY-MM-DD)
            gender: Gender (MALE, FEMALE, OTHER)
            national_health_id: ABHA/National Health ID (optional)
            contact_number: Contact number (optional)
            
        Returns:
            Created Patient instance
        """
        return self.create(
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            gender=gender,
            national_health_id=national_health_id,
            contact_number=contact_number
        )

    def get_patient(self, patient_id: UUID) -> Optional[Patient]:
        """Get patient by ID.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            Patient instance or None
        """
        return self.get(patient_id)

    def get_patient_by_abha(self, abha_id: str) -> Optional[Patient]:
        """Get patient by national health ID.
        
        Args:
            abha_id: ABHA/National Health ID
            
        Returns:
            Patient instance or None
        """
        return self.filter_one(national_health_id=abha_id)

    def patient_exists(self, patient_id: UUID) -> bool:
        """Check if patient exists.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            True if exists
        """
        return self.exists(id=patient_id)

    def get_all_patients(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        """Get all patients with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of Patient instances
        """
        return self.get_all(skip=skip, limit=limit)

    def update_patient(
        self,
        patient_id: UUID,
        **kwargs
    ) -> Optional[Patient]:
        """Update patient information.
        
        Args:
            patient_id: Patient UUID
            **kwargs: Fields to update (first_name, last_name, contact_number, etc.)
            
        Returns:
            Updated Patient instance or None
        """
        return self.update(patient_id, **kwargs)

    def delete_patient(self, patient_id: UUID) -> bool:
        """Delete patient (cascades to sessions, consents, etc.).
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            True if deleted
        """
        return self.delete(patient_id)

    def count_patients(self) -> int:
        """Get total patient count.
        
        Returns:
            Number of patients
        """
        return self.count()

    def search_patients(self, name_fragment: str) -> List[Patient]:
        """Search patients by name (partial match).
        
        Args:
            name_fragment: Fragment of first or last name
            
        Returns:
            List of matching patients
        """
        return self.db.query(Patient).filter(
            (Patient.first_name.ilike(f"%{name_fragment}%")) |
            (Patient.last_name.ilike(f"%{name_fragment}%"))
        ).all()
