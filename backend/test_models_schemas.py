"""Test script to verify all models and schemas are working."""

import sys
from datetime import datetime
import uuid

def test_imports():
    """Test all model and schema imports."""
    try:
        from app.db.models import (
            Patient, Session, ConversationTurn, Document,
            ExtractedEntity, Summary, Consent, AuditLog
        )
        print("[OK] All 8 ORM models import successfully")
    except Exception as e:
        print(f"[FAIL] Model import failed: {e}")
        return False

    try:
        from app.schemas import (
            PatientResponse, SessionResponse, ConversationTurnResponse,
            DocumentResponse, ExtractedEntityResponse, SummaryResponse,
            ConsentResponse, AuditLogResponse
        )
        print("[OK] All 8 Pydantic schemas import successfully")
    except Exception as e:
        print(f"[FAIL] Schema import failed: {e}")
        return False

    return True


def test_lab_abnormality():
    """Test lab abnormality detection."""
    try:
        from app.schemas.extracted_entity import detect_lab_abnormality

        # Test case 1: Low hemoglobin (abnormal)
        result1 = detect_lab_abnormality('hemoglobin', 10.5, '12-17 g/dL')
        assert result1.is_abnormal == True, "Should detect hemoglobin as abnormal"
        assert result1.severity in ['LOW', 'MEDIUM', 'HIGH'], "Severity must be valid"

        # Test case 2: Normal glucose
        result2 = detect_lab_abnormality('glucose', 95, '70-100 mg/dL')
        assert result2.is_abnormal == False, "Should detect glucose as normal"

        # Test case 3: High sodium (abnormal)
        result3 = detect_lab_abnormality('sodium', 150, '136-145 mEq/L')
        assert result3.is_abnormal == True, "Should detect sodium as abnormal"

        print("[OK] Lab abnormality detection working correctly")
        return True
    except Exception as e:
        print(f"[FAIL] Lab abnormality test failed: {e}")
        return False


def test_schema_validation():
    """Test schema validation."""
    try:
        from app.schemas import PatientCreate

        # Valid patient
        patient = PatientCreate(
            first_name="John",
            last_name="Doe",
            dob="1990-01-15",
            gender="MALE"
        )
        print("[OK] Schema validation working (valid input accepted)")

        # Invalid DOB should raise error
        try:
            invalid_patient = PatientCreate(
                first_name="Jane",
                last_name="Doe",
                dob="invalid-date",
                gender="FEMALE"
            )
            print("[FAIL] Schema validation failed (invalid DOB not rejected)")
            return False
        except Exception:
            print("[OK] Schema validation working (invalid input rejected)")

        return True
    except Exception as e:
        print(f"[FAIL] Schema validation test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("TESTING MODELS AND SCHEMAS")
    print("=" * 60)
    print()

    results = [
        test_imports(),
        test_lab_abnormality(),
        test_schema_validation(),
    ]

    print()
    print("=" * 60)
    if all(results):
        print("ALL TESTS PASSED [OK]")
        print("=" * 60)
        print()
        print("Summary:")
        print("- 8 ORM models working")
        print("- 8 Pydantic v2 schemas working")
        print("- Lab abnormality detection working")
        print("- Input validation working")
        print()
        print("Ready for next step: Alembic migrations")
        return 0
    else:
        print("SOME TESTS FAILED [FAIL]")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
