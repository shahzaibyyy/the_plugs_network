"""
Reusable model mixins for common functionality.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp fields.
    
    Provides automatic timestamp management for model creation and updates.
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Timestamp when the record was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
        doc="Timestamp when the record was last updated"
    )


class SoftDeleteMixin:
    """
    Mixin that adds soft delete functionality.
    
    Allows marking records as deleted without physically removing them from the database.
    """
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Flag indicating if the record is soft deleted"
    )
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Timestamp when the record was soft deleted"
    )
    
    def soft_delete(self) -> None:
        """Mark the record as deleted without removing it from the database."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
    
    @property
    def is_active(self) -> bool:
        """Check if the record is active (not soft deleted)."""
        return not self.is_deleted


class AuditMixin:
    """
    Mixin that adds audit trail functionality for tracking changes.
    
    Tracks who created and last modified the record, along with version control.
    """
    
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        doc="ID of the user who created the record"
    )
    
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        doc="ID of the user who last updated the record"
    )
    
    version: Mapped[int] = mapped_column(
        default=1,
        nullable=False,
        doc="Version number for optimistic locking"
    )
    
    def set_created_by(self, user_id: uuid.UUID) -> None:
        """Set the user who created this record."""
        self.created_by = user_id
    
    def set_updated_by(self, user_id: uuid.UUID) -> None:
        """Set the user who last updated this record."""
        self.updated_by = user_id
        self.version += 1


class TenantMixin:
    """
    Mixin that adds multi-tenant support.
    
    Provides organization-level data isolation for multi-tenant applications.
    """
    
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        doc="ID of the organization this record belongs to"
    )
    
    def set_organization(self, organization_id: uuid.UUID) -> None:
        """Set the organization this record belongs to."""
        self.organization_id = organization_id
    
    @property
    def is_tenant_scoped(self) -> bool:
        """Check if this record is scoped to a specific tenant."""
        return self.organization_id is not None


class MetadataMixin:
    """
    Mixin that adds metadata fields for additional context.
    
    Provides flexible metadata storage and tagging capabilities.
    """
    
    tags: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Comma-separated tags for categorization"
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        doc="Additional notes or comments"
    )
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the record."""
        if self.tags:
            existing_tags = set(self.tags.split(','))
            existing_tags.add(tag.strip())
            self.tags = ','.join(sorted(existing_tags))
        else:
            self.tags = tag.strip()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the record."""
        if self.tags:
            existing_tags = set(self.tags.split(','))
            existing_tags.discard(tag.strip())
            self.tags = ','.join(sorted(existing_tags)) if existing_tags else None
    
    def get_tags(self) -> list[str]:
        """Get list of tags."""
        return [tag.strip() for tag in self.tags.split(',')] if self.tags else []
    
    def has_tag(self, tag: str) -> bool:
        """Check if the record has a specific tag."""
        return tag.strip() in self.get_tags()


# Commonly used mixin combinations
class BaseEntityMixin(TimestampMixin, SoftDeleteMixin):
    """
    Base mixin combining timestamp and soft delete functionality.
    
    Most commonly used combination for standard entities.
    """
    pass


class AuditableEntityMixin(TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    Mixin for entities that require full audit trail.
    
    Combines timestamp, soft delete, and audit functionality.
    """
    pass


class TenantEntityMixin(TimestampMixin, SoftDeleteMixin, TenantMixin):
    """
    Mixin for multi-tenant entities.
    
    Combines timestamp, soft delete, and tenant isolation functionality.
    """
    pass


class FullEntityMixin(TimestampMixin, SoftDeleteMixin, AuditMixin, TenantMixin, MetadataMixin):
    """
    Complete mixin with all available functionality.
    
    Use for entities that need comprehensive tracking and metadata.
    """
    pass