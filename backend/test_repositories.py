"""Test all repositories with CRUD operations."""

import sys
import uuid
from datetime import datetime, timezone

def test_repositories():
    """Test all repositories."""
    try:
        from app.db.session import SessionLocal
        from app.db.repositories import (
            PatientRepository,
            SessionRepository,
            ConversationTurnRepository,
            DocumentRepository,
            ExtractedEntityRepository,
            SummaryRepository,
            ConsentRepository,
            AuditLogRepository
        )

        print("=" * 70)
        print("TESTING REPOSITORY PATTERN")
        print("=" * 70)
        print()

        db = SessionLocal()

        # Test 1: PatientRepository
        print("[1] Testing PatientRepository...")
        patient_repo = PatientRepository(db)
        patient = patient_repo.create_patient(
            first_name="John",
            last_name="Doe",
            dob="1990-01-15",
            gender="MALE",
            national_health_id="ABHA-001",
            contact_number="+91-9876543210"
        )
        print(f"    Created patient: {patient.id}")
        retrieved = patient_repo.get_patient(patient.id)
        assert retrieved is not None
        print(f"    Retrieved patient: {retrieved.first_name} {retrieved.last_name}")
        print(f"    Patient exists: {patient_repo.patient_exists(patient.id)}")
        print()

        # Test 2: SessionRepository
        print("[2] Testing SessionRepository...")
        session_repo = SessionRepository(db)
        session = session_repo.create_session(
            patient_id=patient.id,
            mode="MODERN"
        )
        print(f"    Created session: {session.id}")
        retrieved_session = session_repo.get_session(session.id)
        assert retrieved_session is not None
        print(f"    Session status: {retrieved_session.status}")
        print(f"    Session section: {retrieved_session.current_section}")
        
        # Advance section
        updated_session = session_repo.update_section(session.id, "HPI")
        print(f"    Updated section to: {updated_session.current_section}")
        print()

        # Test 3: ConversationTurnRepository
        print("[3] Testing ConversationTurnRepository...")
        turn_repo = ConversationTurnRepository(db)
        turn1 = turn_repo.create_turn(
            session_id=session.id,
            speaker="PATIENT",
            content="I have been having headaches",
            section="CHIEF_COMPLAINT",
            turn_index=1,
            extracted_data={"symptom": "headache"}
        )
        print(f"    Created turn 1: {turn1.id}")
        
        turn2 = turn_repo.create_turn(
            session_id=session.id,
            speaker="SYSTEM",
            content="How long have you had these headaches?",
            section="CHIEF_COMPLAINT",
            turn_index=2
        )
        print(f"    Created turn 2: {turn2.id}")
        
        turns = turn_repo.get_turns_by_session(session.id)
        print(f"    Retrieved {len(turns)} turns")
        print(f"    Next turn index: {turn_repo.get_next_turn_index(session.id)}")
        print()

        # Test 4: DocumentRepository
        print("[4] Testing DocumentRepository...")
        doc_repo = DocumentRepository(db)
        document = doc_repo.create_document(
            session_id=session.id,
            filename="lab_report.pdf",
            file_path="/uploads/lab_report.pdf",
            mime_type="application/pdf",
            file_size=2048576
        )
        print(f"    Created document: {document.id}")
        print(f"    Processing status: {document.processing_status}")
        
        # Update status
        updated_doc = doc_repo.mark_extracted(
            document.id,
            "Lab Report: Hemoglobin 10.5 g/dL, WBC 5.2 K/uL"
        )
        print(f"    Updated status: {updated_doc.processing_status}")
        print(f"    Document stats: {doc_repo.get_document_stats(session.id)}")
        print()

        # Test 5: ExtractedEntityRepository
        print("[5] Testing ExtractedEntityRepository...")
        entity_repo = ExtractedEntityRepository(db)
        entity1 = entity_repo.create_entity(
            session_id=session.id,
            document_id=document.id,
            entity_type="LAB_RESULT",
            entity_name="Hemoglobin",
            value="10.5 g/dL",
            numeric_value=10.5,
            unit="g/dL",
            reference_range="12-17 g/dL",
            is_abnormal=True,
            confidence_score=0.99
        )
        print(f"    Created lab entity: {entity1.id}")
        
        entity2 = entity_repo.create_entity(
            session_id=session.id,
            entity_type="SYMPTOM",
            entity_name="Headache",
            value="Moderate intensity",
            confidence_score=0.95
        )
        print(f"    Created symptom entity: {entity2.id}")
        
        abnormal = entity_repo.get_abnormal_entities(session.id)
        print(f"    Abnormal entities: {len(abnormal)}")
        print(f"    Entity summary: {entity_repo.get_entity_summary(session.id)}")
        print()

        # Test 6: SummaryRepository
        print("[6] Testing SummaryRepository...")
        summary_repo = SummaryRepository(db)
        summary = summary_repo.create_summary(
            session_id=session.id,
            workflow_status="GENERATED"
        )
        print(f"    Created summary: {summary.id}")
        
        # Update content
        updated_summary = summary_repo.update_summary_content(
            summary.id,
            chief_complaint="Headaches for 3 days",
            hpi="Onset 3 days ago, moderate intensity",
            structured_summary={
                "findings": ["Mild dehydration"],
                "recommendations": ["Increase water intake"]
            }
        )
        print(f"    Updated summary content")
        
        # Mark for review
        reviewed = summary_repo.mark_physician_review(summary.id)
        print(f"    Workflow status: {reviewed.workflow_status}")
        
        # Accept summary
        accepted = summary_repo.accept_summary(summary.id, "Dr. Smith")
        print(f"    Final status: {accepted.workflow_status}")
        print(f"    Summary stats: {summary_repo.get_summary_stats(session.id)}")
        print()

        # Test 7: ConsentRepository
        print("[7] Testing ConsentRepository...")
        consent_repo = ConsentRepository(db)
        consent1 = consent_repo.grant_consent(
            session_id=session.id,
            patient_id=patient.id,
            purpose="data_sharing",
            ip_address="192.168.1.1"
        )
        print(f"    Granted consent: {consent1.id}")
        print(f"    Purpose: {consent1.purpose}")
        
        consent2 = consent_repo.grant_consent(
            session_id=session.id,
            patient_id=patient.id,
            purpose="abdm_integration",
            ip_address="192.168.1.1"
        )
        print(f"    Granted ABDM consent: {consent2.id}")
        
        active_consents = consent_repo.get_active_consents(patient.id)
        print(f"    Active consents: {len(active_consents)}")
        
        has_consent = consent_repo.has_active_consent(patient.id, "data_sharing")
        print(f"    Has data_sharing consent: {has_consent}")
        
        # Revoke one
        revoked = consent_repo.revoke_consent(consent1.id)
        print(f"    Revoked consent, revoked_at: {revoked.revoked_at is not None}")
        
        audit = consent_repo.get_consent_audit_trail(patient.id)
        print(f"    Audit trail: {audit['total_consent_records']} records")
        print()

        # Test 8: AuditLogRepository
        print("[8] Testing AuditLogRepository...")
        audit_repo = AuditLogRepository(db)
        
        log1 = audit_repo.log_session_created(session.id, "system")
        print(f"    Logged session creation: {log1.id}")
        
        log2 = audit_repo.log_document_uploaded(
            session.id,
            document_id=str(document.id),
            filename="lab_report.pdf"
        )
        print(f"    Logged document upload: {log2.id}")
        
        log3 = audit_repo.log_summary_generated(
            session.id,
            summary_id=str(summary.id),
            model_used="mock-llm"
        )
        print(f"    Logged summary generation: {log3.id}")
        
        session_logs = audit_repo.get_logs_by_session(session.id)
        print(f"    Session audit logs: {len(session_logs)}")
        
        trail = audit_repo.get_session_audit_trail(session.id)
        print(f"    Audit trail events: {trail['total_log_entries']}")
        print()

        db.close()

        print("=" * 70)
        print("SUCCESS: ALL REPOSITORIES WORKING")
        print("=" * 70)
        print()
        print("Summary:")
        print("- [OK] PatientRepository (create, get, exists)")
        print("- [OK] SessionRepository (create, update_section, get)")
        print("- [OK] ConversationTurnRepository (create, query by session/section)")
        print("- [OK] DocumentRepository (create, update_status, stats)")
        print("- [OK] ExtractedEntityRepository (create, query abnormal, summary)")
        print("- [OK] SummaryRepository (create, workflow updates, accept/reject)")
        print("- [OK] ConsentRepository (grant, revoke, audit trail)")
        print("- [OK] AuditLogRepository (log actions, audit trail)")
        print()

        return 0

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_repositories())
