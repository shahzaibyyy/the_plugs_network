"""
Base repository interface defining generic CRUD operations and patterns.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Sequence, TypeVar, Union
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.base import BaseModel

# Generic type for model classes
ModelType = TypeVar("ModelType", bound=BaseModel)


class IBaseRepository(ABC, Generic[ModelType]):
    """
    Abstract base repository interface defining generic CRUD operations.
    
    This interface provides a contract for all repository implementations,
    ensuring consistent data access patterns across the application.
    """

    @abstractmethod
    def __init__(self, db: Session, model: type[ModelType]) -> None:
        """
        Initialize repository with database session and model type.
        
        Args:
            db: SQLAlchemy database session
            model: Model class for this repository
        """
        pass

    # Basic CRUD Operations
    @abstractmethod
    async def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """
        Create a new record.
        
        Args:
            obj_in: Dictionary with field values for the new record
            
        Returns:
            Created model instance
            
        Raises:
            ValidationError: If input data is invalid
            DatabaseError: If database operation fails
        """
        pass

    @abstractmethod
    async def get(self, id: UUID) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Model instance if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[ModelType]:
        """
        Get multiple records with filtering, pagination, and sorting.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Dictionary of field filters
            order_by: Field name to order by (prefix with '-' for descending)
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            List of model instances
        """
        pass

    @abstractmethod
    async def update(self, id: UUID, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """
        Update an existing record.
        
        Args:
            id: Record ID
            obj_in: Dictionary with field values to update
            
        Returns:
            Updated model instance if found, None otherwise
            
        Raises:
            ValidationError: If input data is invalid
            DatabaseError: If database operation fails
        """
        pass

    @abstractmethod
    async def delete(self, id: UUID, soft: bool = True) -> bool:
        """
        Delete a record (soft delete by default).
        
        Args:
            id: Record ID
            soft: Whether to perform soft delete (True) or hard delete (False)
            
        Returns:
            True if record was deleted, False if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        pass

    @abstractmethod
    async def restore(self, id: UUID) -> Optional[ModelType]:
        """
        Restore a soft-deleted record.
        
        Args:
            id: Record ID
            
        Returns:
            Restored model instance if found, None otherwise
        """
        pass

    # Advanced Query Operations
    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        """
        Check if a record exists.
        
        Args:
            id: Record ID
            
        Returns:
            True if record exists, False otherwise
        """
        pass

    @abstractmethod
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False
    ) -> int:
        """
        Count records matching the given filters.
        
        Args:
            filters: Dictionary of field filters
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            Number of matching records
        """
        pass

    @abstractmethod
    async def find_by(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        include_deleted: bool = False
    ) -> List[ModelType]:
        """
        Find records by specific field values.
        
        Args:
            filters: Dictionary of field filters
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            List of matching model instances
        """
        pass

    @abstractmethod
    async def find_one_by(
        self,
        filters: Dict[str, Any],
        include_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        Find a single record by specific field values.
        
        Args:
            filters: Dictionary of field filters
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            First matching model instance or None
        """
        pass

    # Bulk Operations
    @abstractmethod
    async def bulk_create(self, objects_in: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in a single transaction.
        
        Args:
            objects_in: List of dictionaries with field values
            
        Returns:
            List of created model instances
            
        Raises:
            ValidationError: If any input data is invalid
            DatabaseError: If database operation fails
        """
        pass

    @abstractmethod
    async def bulk_update(
        self,
        updates: List[Dict[str, Any]],
        id_field: str = "id"
    ) -> List[ModelType]:
        """
        Update multiple records in a single transaction.
        
        Args:
            updates: List of dictionaries with id and field values to update
            id_field: Name of the ID field in the update dictionaries
            
        Returns:
            List of updated model instances
            
        Raises:
            ValidationError: If any input data is invalid
            DatabaseError: If database operation fails
        """
        pass

    @abstractmethod
    async def bulk_delete(
        self,
        ids: List[UUID],
        soft: bool = True
    ) -> int:
        """
        Delete multiple records in a single transaction.
        
        Args:
            ids: List of record IDs to delete
            soft: Whether to perform soft delete (True) or hard delete (False)
            
        Returns:
            Number of records deleted
            
        Raises:
            DatabaseError: If database operation fails
        """
        pass

    # Transaction Management
    @abstractmethod
    async def begin_transaction(self) -> None:
        """
        Begin a new database transaction.
        
        Raises:
            DatabaseError: If transaction cannot be started
        """
        pass

    @abstractmethod
    async def commit_transaction(self) -> None:
        """
        Commit the current transaction.
        
        Raises:
            DatabaseError: If transaction cannot be committed
        """
        pass

    @abstractmethod
    async def rollback_transaction(self) -> None:
        """
        Rollback the current transaction.
        
        Raises:
            DatabaseError: If transaction cannot be rolled back
        """
        pass

    # Utility Methods
    @abstractmethod
    def get_session(self) -> Session:
        """
        Get the current database session.
        
        Returns:
            SQLAlchemy session instance
        """
        pass

    @abstractmethod
    async def refresh(self, instance: ModelType) -> ModelType:
        """
        Refresh a model instance from the database.
        
        Args:
            instance: Model instance to refresh
            
        Returns:
            Refreshed model instance
        """
        pass

    @abstractmethod
    async def flush(self) -> None:
        """
        Flush pending changes to the database without committing.
        
        Raises:
            DatabaseError: If flush operation fails
        """
        pass