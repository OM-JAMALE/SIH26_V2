from fastapi import APIRouter
from app.api.v1.endpoints import health, summary
from app.modules.conversation.router import router as conversation_router
from app.modules.documents.router import router as documents_router
from app.modules.patient.router import router as patient_router

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["System Health"])
api_router.include_router(conversation_router, prefix="/sessions", tags=["Module A - Conversational History Engine"])
api_router.include_router(documents_router, prefix="/sessions", tags=["Module B - Medical Document Digitization"])
api_router.include_router(summary.router, prefix="/sessions", tags=["Module C - Clinical Summary"])
api_router.include_router(patient_router)

