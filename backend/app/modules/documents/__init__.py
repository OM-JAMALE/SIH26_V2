from app.modules.documents.router import router
from app.modules.documents.service import DocumentService
from app.modules.documents.lab_rules import evaluate_lab_result

__all__ = ["router", "DocumentService", "evaluate_lab_result"]
