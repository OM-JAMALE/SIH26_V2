"""Base repository class with common CRUD operations."""

from typing import TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository for common CRUD operations."""

    def __init__(self, model: type[T], db: Session):
        """Initialize repository with model and database session.
        
        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    def create(self, **kwargs) -> T:
        """Create and persist a new record.
        
        Args:
            **kwargs: Model field values
            
        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def get(self, id: Any) -> Optional[T]:
        """Get record by ID.
        
        Args:
            id: Primary key value
            
        Returns:
            Model instance or None
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of model instances
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def update(self, id: Any, **kwargs) -> Optional[T]:
        """Update record by ID.
        
        Args:
            id: Primary key value
            **kwargs: Fields to update
            
        Returns:
            Updated model instance or None
        """
        instance = self.get(id)
        if not instance:
            return None
        
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, id: Any) -> bool:
        """Delete record by ID.
        
        Args:
            id: Primary key value
            
        Returns:
            True if deleted, False if not found
        """
        instance = self.get(id)
        if not instance:
            return False
        
        self.db.delete(instance)
        self.db.commit()
        return True

    def exists(self, **filters) -> bool:
        """Check if record exists matching filters.
        
        Args:
            **filters: Field filters
            
        Returns:
            True if exists, False otherwise
        """
        query = self.db.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.first() is not None

    def count(self, **filters) -> int:
        """Count records matching filters.
        
        Args:
            **filters: Field filters
            
        Returns:
            Count of matching records
        """
        query = self.db.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.count()

    def filter(self, **filters) -> List[T]:
        """Get records matching filters.
        
        Args:
            **filters: Field filters
            
        Returns:
            List of matching model instances
        """
        query = self.db.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.all()

    def filter_one(self, **filters) -> Optional[T]:
        """Get first record matching filters.
        
        Args:
            **filters: Field filters
            
        Returns:
            Model instance or None
        """
        query = self.db.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.first()

    def batch_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """Create multiple records in batch.
        
        Args:
            items: List of dictionaries with model field values
            
        Returns:
            List of created model instances
        """
        instances = [self.model(**item) for item in items]
        self.db.add_all(instances)
        self.db.commit()
        for instance in instances:
            self.db.refresh(instance)
        return instances

    def batch_update(self, updates: Dict[Any, Dict[str, Any]]) -> int:
        """Update multiple records in batch.
        
        Args:
            updates: Dict mapping IDs to update dictionaries
            
        Returns:
            Count of updated records
        """
        count = 0
        for id_val, update_dict in updates.items():
            if self.update(id_val, **update_dict):
                count += 1
        return count

    def delete_all(self, **filters) -> int:
        """Delete all records matching filters.
        
        Args:
            **filters: Field filters
            
        Returns:
            Count of deleted records
        """
        query = self.db.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        count = query.count()
        query.delete()
        self.db.commit()
        return count
