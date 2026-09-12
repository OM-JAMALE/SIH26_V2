"""Healthcare Integrations and Consent Management package."""

from app.integrations.fhir_adapter import to_fhir_diagnostic_report, to_fhir_observation
from app.integrations.consent_manager import log_consent_action, get_audit_trail
from app.integrations.abdm_adapter import prepare_for_abdm

__all__ = [
    "to_fhir_diagnostic_report",
    "to_fhir_observation",
    "log_consent_action",
    "get_audit_trail",
    "prepare_for_abdm",
]
