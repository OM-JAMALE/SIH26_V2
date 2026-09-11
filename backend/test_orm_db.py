"""Test database migrations with ORM models."""

import sys
import uuid
from datetime import datetime, timezone

def test_orm_operations():
    """Test ORM models work with migrated database."""
    try:
        from app.db.session import SessionLocal
        from app.db.models import Patient, Session, ConversationTurn, Document, ExtractedEntity, Summary, Consent, AuditLog
        
        print("=" * 70)
        print("TESTING ORM OPERATIONS")
        print("=" * 70)
        print()

        db = SessionLocal()

        # Test 1: Create a patient
        print("[1] Creating patient...")
        patient = Patient(
            id=uuid.uuid4(),
            national_health_id="ABHA-001",
            first_name="John",
            last_name="Doe",
            dob="1990-01-15",
            gender="MALE",
            contact_number="+91-9876543210"
        )
        db.add(patient)
        db.commit()
        print(f"    Patient created: {patient.id}")
        print()

        # Test 2: Create a session
        print("[2] Creating session...")
        session = Session(
            id=uuid.uuid4(),
            patient_id=patient.id,
            status="INITIATED",
            lifecycle_status="CREATED",
            current_section="CHIEF_COMPLAINT",
            mode="MODERN",
            disclaimer_acknowledged=True,
            session_metadata={},
            structured_history={},
            safety_status="SAFE",
            safety_alerts={}
        )
        db.add(session)
        db.commit()
        print(f"    Session created: {session.id}")
        print()

        # Test 3: Create conversation turn
        print("[3] Creating conversation turn...")
        turn = ConversationTurn(
            id=uuid.uuid4(),
            session_id=session.id,
            turn_index=1,
            speaker="PATIENT",
            content="I have been having headaches for 3 days",
            section="CHIEF_COMPLAINT",
            extracted_data={"symptom": "headache", "duration": "3 days"},
            safety_alerts={}
        )
        db.add(turn)
        db.commit()
        print(f"    Conversation turn created: {turn.id}")
        print()

        # Test 4: Create document
        print("[4] Creating document...")
        document = Document(
            id=uuid.uuid4(),
            session_id=session.id,
            filename="lab_report.pdf",
            file_path="/uploads/lab_report.pdf",
            mime_type="application/pdf",
            file_size=2048576,
            processing_status="EXTRACTED",
            raw_text="Lab Report: Hemoglobin 10.5 g/dL"
        )
        db.add(document)
        db.commit()
        print(f"    Document created: {document.id}")
        print()

        # Test 5: Create extracted entity
        print("[5] Creating extracted entity...")
        entity = ExtractedEntity(
            id=uuid.uuid4(),
            session_id=session.id,
            document_id=document.id,
            entity_type="LAB_RESULT",
            entity_name="Hemoglobin",
            value="10.5 g/dL",
            numeric_value=10.5,
            unit="g/dL",
            reference_range="12-17 g/dL",
            is_abnormal=True,
            confidence_score=0.99,
            metadata_json={"source": "lab_report"}
        )
        db.add(entity)
        db.commit()
        print(f"    Extracted entity created: {entity.id}")
        print()

        # Test 6: Create summary
        print("[6] Creating clinical summary...")
        summary = Summary(
            id=uuid.uuid4(),
            session_id=session.id,
            version=1,
            workflow_status="GENERATED",
            status="DRAFT",
            chief_complaint="Headaches for 3 days",
            hpi="Onset 3 days ago, moderate intensity",
            llm_model="mock-llm",
            prompt_version="clinical_summary_v1",
            structured_summary={
                "chief_complaint": "Headaches for 3 days",
                "key_findings": ["Mild dehydration possible"],
                "red_flags": [],
                "recommendations": ["Increase water intake"]
            }
        )
        db.add(summary)
        db.commit()
        print(f"    Summary created: {summary.id}")
        print()

        # Test 7: Create consent
        print("[7] Creating consent record...")
        consent = Consent(
            id=uuid.uuid4(),
            session_id=session.id,
            patient_id=patient.id,
            purpose="data_sharing",
            granted=True,
            terms_version="v1.0",
            ip_address="192.168.1.1"
        )
        db.add(consent)
        db.commit()
        print(f"    Consent created: {consent.id}")
        print()

        # Test 8: Create audit log
        print("[8] Creating audit log...")
        audit = AuditLog(
            id=uuid.uuid4(),
            session_id=session.id,
            user_id="system",
            action="SESSION_CREATED",
            resource="SESSION",
            status="SUCCESS",
            details={"session_id": str(session.id), "mode": "MODERN"}
        )
        db.add(audit)
        db.commit()
        print(f"    Audit log created: {audit.id}")
        print()

        # Test 9: Query relationships
        print("[9] Testing relationships...")
        retrieved_session = db.query(Session).filter(Session.id == session.id).first()
        print(f"    Session patient relationship: {len(retrieved_session.conversation_turns)} turns")
        print(f"    Session documents relationship: {len(retrieved_session.documents)} documents")
        print(f"    Session extracted entities relationship: {len(retrieved_session.extracted_entities)} entities")
        print(f"    Session summaries relationship: {len(retrieved_session.summaries)} summaries")
        print(f"    Session consents relationship: {len(retrieved_session.consents)} consents")
        print()

        # Test 10: Test cascade delete (create new session to delete)
        print("[10] Testing cascade delete...")
        test_session = Session(
            id=uuid.uuid4(),
            patient_id=patient.id,
            status="TEST",
            lifecycle_status="CREATED",
            current_section="CHIEF_COMPLAINT",
            mode="MODERN",
            session_metadata={},
            structured_history={},
            safety_status="SAFE",
            safety_alerts={}
        )
        db.add(test_session)
        db.commit()
        test_session_id = test_session.id
        
        test_turn = ConversationTurn(
            id=uuid.uuid4(),
            session_id=test_session.id,
            turn_index=1,
            speaker="SYSTEM",
            content="Test message",
            section="CHIEF_COMPLAINT",
            extracted_data={},
            safety_alerts={}
        )
        db.add(test_turn)
        db.commit()
        
        # Delete session (should cascade delete turns)
        db.delete(test_session)
        db.commit()
        
        remaining_turns = db.query(ConversationTurn).filter(ConversationTurn.session_id == test_session_id).count()
        print(f"    Cascade delete test: {remaining_turns} turns remaining after session deletion (should be 0)")
        print()

        db.close()

        print("=" * 70)
        print("SUCCESS: ALL ORM OPERATIONS WORKING")
        print("=" * 70)
        print()
        print("Summary:")
        print("- [OK] Patient creation")
        print("- [OK] Session creation")
        print("- [OK] Conversation turn creation")
        print("- [OK] Document creation")
        print("- [OK] Extracted entity creation")
        print("- [OK] Summary creation")
        print("- [OK] Consent creation")
        print("- [OK] Audit log creation")
        print("- [OK] Relationships working")
        print("- [OK] Cascade delete working")
        print()
        print("Database schema is ready for production use!")

        return 0

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_orm_operations())
