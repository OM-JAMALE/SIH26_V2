"""Extracted Entity repository for entity management operations."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models import ExtractedEntity
from app.db.repositories.base import BaseRepository


class ExtractedEntityRepository(BaseRepository[ExtractedEntity]):
    """Repository for ExtractedEntity model."""

    def __init__(self, db: Session):
        """Initialize extracted entity repository.
        
        Args:
            db: Database session
        """
        super().__init__(ExtractedEntity, db)

    def create_entity(
        self,
        session_id: UUID,
        entity_type: str,
        entity_name: str,
        value: str,
        document_id: Optional[UUID] = None,
        numeric_value: Optional[float] = None,
        unit: Optional[str] = None,
        reference_range: Optional[str] = None,
        is_abnormal: bool = False,
        confidence_score: float = 1.0,
        metadata_json: Optional[dict] = None
    ) -> ExtractedEntity:
        """Create a new extracted entity.
        
        Args:
            session_id: Session UUID
            entity_type: LAB_RESULT, MEDICATION, DIAGNOSIS, VITAL, or SYMPTOM
            entity_name: Entity name
            value: String value
            document_id: Document UUID if from document (optional)
            numeric_value: Numeric value if applicable (optional)
            unit: Unit of measurement (optional)
            reference_range: Reference range (optional)
            is_abnormal: Whether value is abnormal
            confidence_score: Confidence (0-1)
            metadata_json: Additional metadata (optional)
            
        Returns:
            Created ExtractedEntity instance
        """
        return self.create(
            session_id=session_id,
            entity_type=entity_type,
            entity_name=entity_name,
            value=value,
            document_id=document_id,
            numeric_value=numeric_value,
            unit=unit,
            reference_range=reference_range,
            is_abnormal=is_abnormal,
            confidence_score=confidence_score,
            metadata_json=metadata_json or {}
        )

    def get_entity(self, entity_id: UUID) -> Optional[ExtractedEntity]:
        """Get entity by ID.
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            ExtractedEntity instance or None
        """
        return self.get(entity_id)

    def get_entities_by_session(self, session_id: UUID) -> List[ExtractedEntity]:
        """Get all entities for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            List of ExtractedEntity instances
        """
        return self.filter(session_id=session_id)

    def get_entities_by_document(self, document_id: UUID) -> List[ExtractedEntity]:
        """Get all entities from a document.
        
        Args:
            document_id: Document UUID
            
        Returns:
            List of ExtractedEntity instances
        """
        return self.filter(document_id=document_id)

    def get_entities_by_type(
        self,
        session_id: UUID,
        entity_type: str
    ) -> List[ExtractedEntity]:
        """Get entities of specific type.
        
        Args:
            session_id: Session UUID
            entity_type: LAB_RESULT, MEDICATION, DIAGNOSIS, VITAL, or SYMPTOM
            
        Returns:
            List of ExtractedEntity instances
        """
        return self.db.query(ExtractedEntity).filter(
            ExtractedEntity.session_id == session_id,
            ExtractedEntity.entity_type == entity_type
        ).all()

    def get_abnormal_entities(self, session_id: UUID) -> List[ExtractedEntity]:
        """Get all abnormal entities in a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            List of abnormal ExtractedEntity instances
        """
        return self.db.query(ExtractedEntity).filter(
            ExtractedEntity.session_id == session_id,
            ExtractedEntity.is_abnormal == True
        ).all()

    def get_lab_results(self, session_id: UUID) -> List[ExtractedEntity]:
        """Get all lab results for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            List of lab result ExtractedEntity instances
        """
        return self.get_entities_by_type(session_id, "LAB_RESULT")

    def get_medications(self, session_id: UUID) -> List[ExtractedEntity]:
        """Get all medications for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            List of medication ExtractedEntity instances
        """
        return self.get_entities_by_type(session_id, "MEDICATION")

    def get_symptoms(self, session_id: UUID) -> List[ExtractedEntity]:
        """Get all symptoms for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            List of symptom ExtractedEntity instances
        """
        return self.get_entities_by_type(session_id, "SYMPTOM")

    def get_entity_by_name(
        self,
        session_id: UUID,
        entity_name: str,
        entity_type: Optional[str] = None
    ) -> Optional[ExtractedEntity]:
        """Get entity by name (optionally filtered by type).
        
        Args:
            session_id: Session UUID
            entity_name: Entity name
            entity_type: Entity type filter (optional)
            
        Returns:
            ExtractedEntity instance or None
        """
        query = self.db.query(ExtractedEntity).filter(
            ExtractedEntity.session_id == session_id,
            ExtractedEntity.entity_name.ilike(entity_name)
        )
        if entity_type:
            query = query.filter(ExtractedEntity.entity_type == entity_type)
        return query.first()

    def update_entity(
        self,
        entity_id: UUID,
        **kwargs
    ) -> Optional[ExtractedEntity]:
        """Update entity information.
        
        Args:
            entity_id: Entity UUID
            **kwargs: Fields to update
            
        Returns:
            Updated ExtractedEntity instance or None
        """
        return self.update(entity_id, **kwargs)

    def update_abnormality(
        self,
        entity_id: UUID,
        is_abnormal: bool
    ) -> Optional[ExtractedEntity]:
        """Update abnormality status.
        
        Args:
            entity_id: Entity UUID
            is_abnormal: Abnormality status
            
        Returns:
            Updated ExtractedEntity instance or None
        """
        return self.update(entity_id, is_abnormal=is_abnormal)

    def delete_entity(self, entity_id: UUID) -> bool:
        """Delete entity.
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            True if deleted
        """
        return self.delete(entity_id)

    def delete_entities_by_document(self, document_id: UUID) -> int:
        """Delete all entities from a document.
        
        Args:
            document_id: Document UUID
            
        Returns:
            Number of deleted entities
        """
        return self.delete_all(document_id=document_id)

    def entity_exists(self, entity_id: UUID) -> bool:
        """Check if entity exists.
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            True if exists
        """
        return self.exists(id=entity_id)

    def count_entities_by_session(self, session_id: UUID) -> int:
        """Count entities in a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Number of entities
        """
        return self.count(session_id=session_id)

    def count_abnormal_entities(self, session_id: UUID) -> int:
        """Count abnormal entities in a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Number of abnormal entities
        """
        return self.db.query(ExtractedEntity).filter(
            ExtractedEntity.session_id == session_id,
            ExtractedEntity.is_abnormal == True
        ).count()

    def get_entity_summary(self, session_id: UUID) -> dict:
        """Get summary of entities in a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Dictionary with entity statistics
        """
        entities = self.get_entities_by_session(session_id)
        if not entities:
            return {"session_id": str(session_id), "total_count": 0}
        
        abnormal_count = len([e for e in entities if e.is_abnormal])
        
        type_counts = {}
        for entity in entities:
            type_counts[entity.entity_type] = type_counts.get(entity.entity_type, 0) + 1
        
        avg_confidence = sum(e.confidence_score for e in entities) / len(entities)
        
        return {
            "session_id": str(session_id),
            "total_count": len(entities),
            "abnormal_count": abnormal_count,
            "normal_count": len(entities) - abnormal_count,
            "by_type": type_counts,
            "avg_confidence": round(avg_confidence, 2)
        }

    def get_high_confidence_entities(
        self,
        session_id: UUID,
        min_confidence: float = 0.8
    ) -> List[ExtractedEntity]:
        """Get entities with high confidence scores.
        
        Args:
            session_id: Session UUID
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of high-confidence ExtractedEntity instances
        """
        return self.db.query(ExtractedEntity).filter(
            ExtractedEntity.session_id == session_id,
            ExtractedEntity.confidence_score >= min_confidence
        ).all()
