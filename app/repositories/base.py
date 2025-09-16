"""
Base repository implementation with SQLAlchemy providing generic CRUD operations.
"""
import logging
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import DatabaseError, NotFoundError, TransactionError, ValidationError
from app.models.base import BaseModel
from app.repositories.interfaces.base import IBaseRepository

# Generic type for model classes
ModelType = TypeVar("ModelType", bound=BaseModel)

logger = logging.getLogger(__name__)


class BaseRepository(IBaseRepository[ModelType], Generic[ModelType]):
    """
    Base repository implementation providing generic CRUD operations with SQLAlchemy.
    
    This class implements the IBaseRepository interface and provides:
    - Generic CRUD operations with proper error handling
    - Pagination and filtering utilities
    - Transaction management and rollback handling
    - Soft delete support
    - Bulk operations for performance
    """

    def __init__(self, db: Session, model: type[ModelType]) -> None:
        """
        Initialize repository with database session and model type.
        
        Args:
            db: SQLAlchemy database session
            model: Model class for this repository
        """
        self.db = db
        self.model = model
        self._in_transaction = False

    # Basic CRUD Operations
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
        try:
            # Create new instance
            db_obj = self.model(**obj_in)
            
            # Add to session and flush to get ID
            self.db.add(db_obj)
            await self.flush()
            
            # Refresh to get all computed fields
            await self.refresh(db_obj)
            
            logger.debug(f"Created {self.model.__name__} with ID: {db_obj.id}")
            return db_obj
            
        except IntegrityError as e:
            await self.rollback_transaction()
            logger.error(f"Integrity error creating {self.model.__name__}: {e}")
            raise ValidationError(
                f"Data integrity violation: {str(e)}",
                error_code="INTEGRITY_ERROR",
                details={"model": self.model.__name__, "data": obj_in}
            )
        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise DatabaseError(
                f"Failed to create {self.model.__name__}",
                error_code="CREATE_ERROR",
                details={"model": self.model.__name__, "error": str(e)}
            )

    async def get(self, id: UUID) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Model instance if found, None otherwise
        """
        try:
            query = self.db.query(self.model).filter(
                and_(
                    self.model.id == id,
                    self.model.is_deleted == False
                )
            )
            result = query.first()
            
            if result:
                logger.debug(f"Found {self.model.__name__} with ID: {id}")
            else:
                logger.debug(f"{self.model.__name__} not found with ID: {id}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by ID {id}: {e}")
            raise DatabaseError(
                f"Failed to get {self.model.__name__}",
                error_code="GET_ERROR",
                details={"model": self.model.__name__, "id": str(id), "error": str(e)}
            )

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
        try:
            query = self.db.query(self.model)
            
            # Apply soft delete filter
            if not include_deleted:
                query = query.filter(self.model.is_deleted == False)
            
            # Apply custom filters
            if filters:
                query = self._apply_filters(query, filters)
            
            # Apply ordering
            if order_by:
                query = self._apply_ordering(query, order_by)
            else:
                # Default ordering by created_at descending
                query = query.order_by(desc(self.model.created_at))
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            results = query.all()
            
            logger.debug(
                f"Retrieved {len(results)} {self.model.__name__} records "
                f"(skip={skip}, limit={limit})"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting multiple {self.model.__name__}: {e}")
            raise DatabaseError(
                f"Failed to get multiple {self.model.__name__}",
                error_code="GET_MULTI_ERROR",
                details={
                    "model": self.model.__name__,
                    "filters": filters,
                    "error": str(e)
                }
            )

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
        try:
            # Get existing record
            db_obj = await self.get(id)
            if not db_obj:
                return None
            
            # Update fields
            db_obj.update_from_dict(obj_in)
            
            # Flush changes and refresh
            await self.flush()
            await self.refresh(db_obj)
            
            logger.debug(f"Updated {self.model.__name__} with ID: {id}")
            return db_obj
            
        except IntegrityError as e:
            await self.rollback_transaction()
            logger.error(f"Integrity error updating {self.model.__name__}: {e}")
            raise ValidationError(
                f"Data integrity violation: {str(e)}",
                error_code="INTEGRITY_ERROR",
                details={"model": self.model.__name__, "id": str(id), "data": obj_in}
            )
        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"Error updating {self.model.__name__} {id}: {e}")
            raise DatabaseError(
                f"Failed to update {self.model.__name__}",
                error_code="UPDATE_ERROR",
                details={"model": self.model.__name__, "id": str(id), "error": str(e)}
            )

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
        try:
            # Get existing record
            db_obj = await self.get(id)
            if not db_obj:
                return False
            
            if soft:
                # Soft delete
                db_obj.soft_delete()
                await self.flush()
                logger.debug(f"Soft deleted {self.model.__name__} with ID: {id}")
            else:
                # Hard delete
                self.db.delete(db_obj)
                await self.flush()
                logger.debug(f"Hard deleted {self.model.__name__} with ID: {id}")
            
            return True
            
        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"Error deleting {self.model.__name__} {id}: {e}")
            raise DatabaseError(
                f"Failed to delete {self.model.__name__}",
                error_code="DELETE_ERROR",
                details={"model": self.model.__name__, "id": str(id), "error": str(e)}
            )

    async def restore(self, id: UUID) -> Optional[ModelType]:
        """
        Restore a soft-deleted record.
        
        Args:
            id: Record ID
            
        Returns:
            Restored model instance if found, None otherwise
        """
        try:
            # Get record including deleted ones
            query = self.db.query(self.model).filter(
                and_(
                    self.model.id == id,
                    self.model.is_deleted == True
                )
            )
            db_obj = query.first()
            
            if not db_obj:
                return None
            
            # Restore the record
            db_obj.restore()
            await self.flush()
            await self.refresh(db_obj)
            
            logger.debug(f"Restored {self.model.__name__} with ID: {id}")
            return db_obj
            
        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"Error restoring {self.model.__name__} {id}: {e}")
            raise DatabaseError(
                f"Failed to restore {self.model.__name__}",
                error_code="RESTORE_ERROR",
                details={"model": self.model.__name__, "id": str(id), "error": str(e)}
            )

    # Advanced Query Operations
    async def exists(self, id: UUID) -> bool:
        """
        Check if a record exists.
        
        Args:
            id: Record ID
            
        Returns:
            True if record exists, False otherwise
        """
        try:
            query = self.db.query(self.model.id).filter(
                and_(
                    self.model.id == id,
                    self.model.is_deleted == False
                )
            )
            result = query.first()
            return result is not None
            
        except Exception as e:
            logger.error(f"Error checking existence of {self.model.__name__} {id}: {e}")
            raise DatabaseError(
                f"Failed to check existence of {self.model.__name__}",
                error_code="EXISTS_ERROR",
                details={"model": self.model.__name__, "id": str(id), "error": str(e)}
            )

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
        try:
            query = self.db.query(func.count(self.model.id))
            
            # Apply soft delete filter
            if not include_deleted:
                query = query.filter(self.model.is_deleted == False)
            
            # Apply custom filters
            if filters:
                query = self._apply_filters(query, filters)
            
            result = query.scalar()
            
            logger.debug(f"Counted {result} {self.model.__name__} records")
            return result or 0
            
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise DatabaseError(
                f"Failed to count {self.model.__name__}",
                error_code="COUNT_ERROR",
                details={"model": self.model.__name__, "filters": filters, "error": str(e)}
            )

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
        try:
            query = self.db.query(self.model)
            
            # Apply soft delete filter
            if not include_deleted:
                query = query.filter(self.model.is_deleted == False)
            
            # Apply custom filters
            query = self._apply_filters(query, filters)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            results = query.all()
            
            logger.debug(f"Found {len(results)} {self.model.__name__} records by filters")
            return results
            
        except Exception as e:
            logger.error(f"Error finding {self.model.__name__} by filters: {e}")
            raise DatabaseError(
                f"Failed to find {self.model.__name__} by filters",
                error_code="FIND_BY_ERROR",
                details={"model": self.model.__name__, "filters": filters, "error": str(e)}
            )

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
        try:
            results = await self.find_by(filters, limit=1, include_deleted=include_deleted)
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"Error finding one {self.model.__name__} by filters: {e}")
            raise DatabaseError(
                f"Failed to find one {self.model.__name__} by filters",
                error_code="FIND_ONE_BY_ERROR",
                details={"model": self.model.__name__, "filters": filters, "error": str(e)}
            )

    # Bulk Operations
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
        if not objects_in:
            return []
        
        try:
            # Create instances
            db_objects = [self.model(**obj_data) for obj_data in objects_in]
            
            # Add all to session
            self.db.add_all(db_objects)
            await self.flush()
            
            # Refresh all instances
            for db_obj in db_objects:
                await self.refresh(db_obj)
            
            logger.debug(f"Bulk created {len(db_objects)} {self.model.__name__} records")
            return db_objects
            
        except IntegrityError as e:
            await self.rollback_transaction()
            logger.error(f"Integrity error bulk creating {self.model.__name__}: {e}")
            raise ValidationError(
                f"Data integrity violation in bulk create: {str(e)}",
                error_code="BULK_INTEGRITY_ERROR",
                details={"model": self.model.__name__, "count": len(objects_in)}
            )
        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"Error bulk creating {self.model.__name__}: {e}")
            raise DatabaseError(
                f"Failed to bulk create {self.model.__name__}",
                error_code="BULK_CREATE_ERROR",
                details={"model": self.model.__name__, "count": len(objects_in), "error": str(e)}
            )

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
        if not updates:
            return []
        
        try:
            updated_objects = []
            
            for update_data in updates:
                if id_field not in update_data:
                    raise ValidationError(
                        f"Missing {id_field} in update data",
                        error_code="MISSING_ID_FIELD"
                    )
                
                record_id = update_data.pop(id_field)
                db_obj = await self.get(record_id)
                
                if db_obj:
                    db_obj.update_from_dict(update_data)
                    updated_objects.append(db_obj)
            
            # Flush all changes
            await self.flush()
            
            # Refresh all instances
            for db_obj in updated_objects:
                await self.refresh(db_obj)
            
            logger.debug(f"Bulk updated {len(updated_objects)} {self.model.__name__} records")
            return updated_objects
            
        except IntegrityError as e:
            await self.rollback_transaction()
            logger.error(f"Integrity error bulk updating {self.model.__name__}: {e}")
            raise ValidationError(
                f"Data integrity violation in bulk update: {str(e)}",
                error_code="BULK_UPDATE_INTEGRITY_ERROR",
                details={"model": self.model.__name__, "count": len(updates)}
            )
        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"Error bulk updating {self.model.__name__}: {e}")
            raise DatabaseError(
                f"Failed to bulk update {self.model.__name__}",
                error_code="BULK_UPDATE_ERROR",
                details={"model": self.model.__name__, "count": len(updates), "error": str(e)}
            )

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
        if not ids:
            return 0
        
        try:
            deleted_count = 0
            
            if soft:
                # Soft delete - update records
                query = self.db.query(self.model).filter(
                    and_(
                        self.model.id.in_(ids),
                        self.model.is_deleted == False
                    )
                )
                
                records = query.all()
                for record in records:
                    record.soft_delete()
                    deleted_count += 1
                    
            else:
                # Hard delete
                query = self.db.query(self.model).filter(self.model.id.in_(ids))
                deleted_count = query.delete(synchronize_session=False)
            
            await self.flush()
            
            logger.debug(f"Bulk deleted {deleted_count} {self.model.__name__} records")
            return deleted_count
            
        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"Error bulk deleting {self.model.__name__}: {e}")
            raise DatabaseError(
                f"Failed to bulk delete {self.model.__name__}",
                error_code="BULK_DELETE_ERROR",
                details={"model": self.model.__name__, "count": len(ids), "error": str(e)}
            )

    # Transaction Management
    async def begin_transaction(self) -> None:
        """
        Begin a new database transaction.
        
        Raises:
            DatabaseError: If transaction cannot be started
        """
        try:
            if not self._in_transaction:
                self.db.begin()
                self._in_transaction = True
                logger.debug("Database transaction started")
            
        except Exception as e:
            logger.error(f"Error starting transaction: {e}")
            raise TransactionError(
                "Failed to start transaction",
                error_code="TRANSACTION_START_ERROR",
                details={"error": str(e)}
            )

    async def commit_transaction(self) -> None:
        """
        Commit the current transaction.
        
        Raises:
            DatabaseError: If transaction cannot be committed
        """
        try:
            if self._in_transaction:
                self.db.commit()
                self._in_transaction = False
                logger.debug("Database transaction committed")
            
        except Exception as e:
            await self.rollback_transaction()
            logger.error(f"Error committing transaction: {e}")
            raise TransactionError(
                "Failed to commit transaction",
                error_code="TRANSACTION_COMMIT_ERROR",
                details={"error": str(e)}
            )

    async def rollback_transaction(self) -> None:
        """
        Rollback the current transaction.
        
        Raises:
            DatabaseError: If transaction cannot be rolled back
        """
        try:
            if self._in_transaction:
                self.db.rollback()
                self._in_transaction = False
                logger.debug("Database transaction rolled back")
            
        except Exception as e:
            logger.error(f"Error rolling back transaction: {e}")
            raise TransactionError(
                "Failed to rollback transaction",
                error_code="TRANSACTION_ROLLBACK_ERROR",
                details={"error": str(e)}
            )

    # Utility Methods
    def get_session(self) -> Session:
        """
        Get the current database session.
        
        Returns:
            SQLAlchemy session instance
        """
        return self.db

    async def refresh(self, instance: ModelType) -> ModelType:
        """
        Refresh a model instance from the database.
        
        Args:
            instance: Model instance to refresh
            
        Returns:
            Refreshed model instance
        """
        try:
            self.db.refresh(instance)
            return instance
            
        except Exception as e:
            logger.error(f"Error refreshing {self.model.__name__} instance: {e}")
            raise DatabaseError(
                f"Failed to refresh {self.model.__name__} instance",
                error_code="REFRESH_ERROR",
                details={"model": self.model.__name__, "error": str(e)}
            )

    async def flush(self) -> None:
        """
        Flush pending changes to the database without committing.
        
        Raises:
            DatabaseError: If flush operation fails
        """
        try:
            self.db.flush()
            
        except Exception as e:
            logger.error(f"Error flushing database session: {e}")
            raise DatabaseError(
                "Failed to flush database session",
                error_code="FLUSH_ERROR",
                details={"error": str(e)}
            )

    # Private Helper Methods
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """
        Apply filters to a SQLAlchemy query.
        
        Args:
            query: SQLAlchemy query object
            filters: Dictionary of field filters
            
        Returns:
            Modified query with filters applied
        """
        for field, value in filters.items():
            if not hasattr(self.model, field):
                continue
                
            column = getattr(self.model, field)
            
            # Handle different filter types
            if isinstance(value, dict):
                # Complex filters like {"gte": 10, "lte": 20}
                for operator, filter_value in value.items():
                    if operator == "gte":
                        query = query.filter(column >= filter_value)
                    elif operator == "lte":
                        query = query.filter(column <= filter_value)
                    elif operator == "gt":
                        query = query.filter(column > filter_value)
                    elif operator == "lt":
                        query = query.filter(column < filter_value)
                    elif operator == "ne":
                        query = query.filter(column != filter_value)
                    elif operator == "in":
                        query = query.filter(column.in_(filter_value))
                    elif operator == "not_in":
                        query = query.filter(~column.in_(filter_value))
                    elif operator == "like":
                        query = query.filter(column.like(f"%{filter_value}%"))
                    elif operator == "ilike":
                        query = query.filter(column.ilike(f"%{filter_value}%"))
                        
            elif isinstance(value, list):
                # List means "in" filter
                query = query.filter(column.in_(value))
                
            else:
                # Simple equality filter
                query = query.filter(column == value)
        
        return query

    def _apply_ordering(self, query, order_by: str):
        """
        Apply ordering to a SQLAlchemy query.
        
        Args:
            query: SQLAlchemy query object
            order_by: Field name to order by (prefix with '-' for descending)
            
        Returns:
            Modified query with ordering applied
        """
        # Handle descending order (prefix with '-')
        if order_by.startswith('-'):
            field_name = order_by[1:]
            descending = True
        else:
            field_name = order_by
            descending = False
        
        # Check if field exists on model
        if not hasattr(self.model, field_name):
            logger.warning(f"Invalid order field: {field_name}")
            return query
        
        column = getattr(self.model, field_name)
        
        if descending:
            query = query.order_by(desc(column))
        else:
            query = query.order_by(column)
        
        return query