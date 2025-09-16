"""
Tests for base model and mixins functionality.
"""
import uuid
from datetime import datetime

import pytest
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.mixins import (
    AuditMixin,
    BaseEntityMixin,
    MetadataMixin,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class TestModel(BaseModel):
    """Test model for testing base functionality."""
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class TestModelWithMixins(BaseModel, BaseEntityMixin, AuditMixin, TenantMixin, MetadataMixin):
    """Test model with all mixins for comprehensive testing."""
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class TestBaseModel:
    """Test cases for BaseModel functionality."""
    
    def test_base_model_creation(self):
        """Test that base model can be instantiated with required fields."""
        model = TestModel(name="Test")
        
        # Check that UUID is generated
        assert isinstance(model.id, uuid.UUID)
        
        # Check that timestamps are set (will be None until saved to DB)
        assert hasattr(model, 'created_at')
        assert hasattr(model, 'updated_at')
        
        # Check soft delete fields
        assert model.is_deleted is False
        assert model.deleted_at is None
    
    def test_soft_delete_functionality(self):
        """Test soft delete functionality."""
        model = TestModel(name="Test")
        
        # Initially not deleted
        assert not model.is_deleted
        assert model.deleted_at is None
        
        # Soft delete
        model.soft_delete()
        assert model.is_deleted
        assert isinstance(model.deleted_at, datetime)
        
        # Restore
        model.restore()
        assert not model.is_deleted
        assert model.deleted_at is None
    
    def test_to_dict_conversion(self):
        """Test model to dictionary conversion."""
        model = TestModel(name="Test")
        model_dict = model.to_dict()
        
        assert 'id' in model_dict
        assert 'name' in model_dict
        assert 'created_at' in model_dict
        assert 'updated_at' in model_dict
        assert 'is_deleted' in model_dict
        assert model_dict['name'] == "Test"
        assert model_dict['is_deleted'] is False
    
    def test_to_dict_with_exclusions(self):
        """Test model to dictionary conversion with exclusions."""
        model = TestModel(name="Test")
        model_dict = model.to_dict(exclude={'created_at', 'updated_at'})
        
        assert 'id' in model_dict
        assert 'name' in model_dict
        assert 'created_at' not in model_dict
        assert 'updated_at' not in model_dict
    
    def test_update_from_dict(self):
        """Test updating model from dictionary."""
        model = TestModel(name="Original")
        
        # Update with new data
        model.update_from_dict({'name': 'Updated'})
        assert model.name == 'Updated'
        
        # Ensure protected fields are not updated
        original_id = model.id
        model.update_from_dict({'id': uuid.uuid4(), 'name': 'Updated Again'})
        assert model.id == original_id  # ID should not change
        assert model.name == 'Updated Again'
    
    def test_repr(self):
        """Test string representation."""
        model = TestModel(name="Test")
        repr_str = repr(model)
        assert "TestModel" in repr_str
        assert str(model.id) in repr_str


class TestMixins:
    """Test cases for model mixins."""
    
    def test_soft_delete_mixin(self):
        """Test SoftDeleteMixin functionality."""
        model = TestModelWithMixins(name="Test")
        
        # Test is_active property
        assert model.is_active
        
        # Test soft delete
        model.soft_delete()
        assert not model.is_active
        assert model.is_deleted
        
        # Test restore
        model.restore()
        assert model.is_active
        assert not model.is_deleted
    
    def test_audit_mixin(self):
        """Test AuditMixin functionality."""
        model = TestModelWithMixins(name="Test")
        user_id = uuid.uuid4()
        
        # Test setting created by
        model.set_created_by(user_id)
        assert model.created_by == user_id
        
        # Test setting updated by (should increment version)
        original_version = model.version
        model.set_updated_by(user_id)
        assert model.updated_by == user_id
        assert model.version == original_version + 1
    
    def test_tenant_mixin(self):
        """Test TenantMixin functionality."""
        model = TestModelWithMixins(name="Test")
        org_id = uuid.uuid4()
        
        # Initially not tenant scoped
        assert not model.is_tenant_scoped
        
        # Set organization
        model.set_organization(org_id)
        assert model.organization_id == org_id
        assert model.is_tenant_scoped
    
    def test_metadata_mixin(self):
        """Test MetadataMixin functionality."""
        model = TestModelWithMixins(name="Test")
        
        # Test adding tags
        model.add_tag("important")
        assert model.has_tag("important")
        assert "important" in model.get_tags()
        
        # Test adding multiple tags
        model.add_tag("urgent")
        tags = model.get_tags()
        assert "important" in tags
        assert "urgent" in tags
        assert len(tags) == 2
        
        # Test removing tag
        model.remove_tag("important")
        assert not model.has_tag("important")
        assert model.has_tag("urgent")
        
        # Test notes
        model.notes = "Test notes"
        assert model.notes == "Test notes"