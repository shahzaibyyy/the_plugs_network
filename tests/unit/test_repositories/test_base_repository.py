"""
Unit tests for BaseRepository implementation.
"""
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import DatabaseError, ValidationError, TransactionError
from app.models.base import BaseModel
from app.repositories.base import BaseRepository


# Test model for repository testing
class TestModel(BaseModel):
    __tablename__ = "test_model"
    
    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestBaseRepository:
    """Test cases for BaseRepository."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = Mock(spec=Session)
        session.query.return_value = session
        session.filter.return_value = session
        session.first.return_value = None
        session.all.return_value = []
        session.scalar.return_value = 0
        session.add = Mock()
        session.add_all = Mock()
        session.delete = Mock()
        session.flush = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.refresh = Mock()
        session.begin = Mock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        """Create a BaseRepository instance for testing."""
        return BaseRepository(mock_session, TestModel)
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for testing."""
        return {
            "name": "Test Item",
            "description": "Test description",
            "value": 42
        }
    
    @pytest.fixture
    def sample_model(self):
        """Sample model instance for testing."""
        model = TestModel(
            name="Test Item",
            description="Test description",
            value=42
        )
        model.id = uuid4()
        model.created_at = datetime.utcnow()
        model.updated_at = datetime.utcnow()
        model.is_deleted = False
        model.deleted_at = None
        return model

    # Basic CRUD Operations Tests
    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_session, sample_data):
        """Test successful record creation."""
        # Setup
        mock_instance = TestModel(**sample_data)
        mock_instance.id = uuid4()
        
        with patch.object(TestModel, '__init__', return_value=None) as mock_init:
            mock_init.return_value = mock_instance
            
            # Execute
            result = await repository.create(sample_data)
            
            # Verify
            mock_session.add.assert_called_once()
            mock_session.flush.assert_called_once()
            mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_integrity_error(self, repository, mock_session, sample_data):
        """Test creation with integrity error."""
        # Setup
        mock_session.flush.side_effect = IntegrityError("statement", "params", "orig")
        
        # Execute & Verify
        with pytest.raises(ValidationError) as exc_info:
            await repository.create(sample_data)
        
        assert exc_info.value.error_code == "INTEGRITY_ERROR"
        mock_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_existing_record(self, repository, mock_session, sample_model):
        """Test getting an existing record."""
        # Setup
        test_id = sample_model.id
        mock_session.query.return_value.filter.return_value.first.return_value = sample_model
        
        # Execute
        result = await repository.get(test_id)
        
        # Verify
        assert result == sample_model
        mock_session.query.assert_called_with(TestModel)
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_record(self, repository, mock_session):
        """Test getting a non-existent record."""
        # Setup
        test_id = uuid4()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = await repository.get(test_id)
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_multi_with_pagination(self, repository, mock_session):
        """Test getting multiple records with pagination."""
        # Setup
        mock_records = [TestModel(name=f"Item {i}") for i in range(3)]
        mock_session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_records
        
        # Execute
        result = await repository.get_multi(skip=10, limit=20)
        
        # Verify
        assert len(result) == 3
        mock_session.query.assert_called_with(TestModel)
    
    @pytest.mark.asyncio
    async def test_update_existing_record(self, repository, mock_session, sample_model):
        """Test updating an existing record."""
        # Setup
        test_id = sample_model.id
        update_data = {"name": "Updated Name"}
        
        # Mock the get method to return the sample model
        with patch.object(repository, 'get', return_value=sample_model):
            with patch.object(sample_model, 'update_from_dict') as mock_update:
                # Execute
                result = await repository.update(test_id, update_data)
                
                # Verify
                assert result == sample_model
                mock_update.assert_called_once_with(update_data)
                mock_session.flush.assert_called_once()
                mock_session.refresh.assert_called_once_with(sample_model)
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_record(self, repository, mock_session):
        """Test updating a non-existent record."""
        # Setup
        test_id = uuid4()
        update_data = {"name": "Updated Name"}
        
        # Mock the get method to return None
        with patch.object(repository, 'get', return_value=None):
            # Execute
            result = await repository.update(test_id, update_data)
            
            # Verify
            assert result is None
    
    @pytest.mark.asyncio
    async def test_soft_delete_existing_record(self, repository, mock_session, sample_model):
        """Test soft deleting an existing record."""
        # Setup
        test_id = sample_model.id
        
        # Mock the get method to return the sample model
        with patch.object(repository, 'get', return_value=sample_model):
            with patch.object(sample_model, 'soft_delete') as mock_soft_delete:
                # Execute
                result = await repository.delete(test_id, soft=True)
                
                # Verify
                assert result is True
                mock_soft_delete.assert_called_once()
                mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_hard_delete_existing_record(self, repository, mock_session, sample_model):
        """Test hard deleting an existing record."""
        # Setup
        test_id = sample_model.id
        
        # Mock the get method to return the sample model
        with patch.object(repository, 'get', return_value=sample_model):
            # Execute
            result = await repository.delete(test_id, soft=False)
            
            # Verify
            assert result is True
            mock_session.delete.assert_called_once_with(sample_model)
            mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_record(self, repository, mock_session):
        """Test deleting a non-existent record."""
        # Setup
        test_id = uuid4()
        
        # Mock the get method to return None
        with patch.object(repository, 'get', return_value=None):
            # Execute
            result = await repository.delete(test_id)
            
            # Verify
            assert result is False

    # Advanced Query Operations Tests
    @pytest.mark.asyncio
    async def test_exists_true(self, repository, mock_session):
        """Test exists method when record exists."""
        # Setup
        test_id = uuid4()
        mock_session.query.return_value.filter.return_value.first.return_value = Mock()
        
        # Execute
        result = await repository.exists(test_id)
        
        # Verify
        assert result is True
    
    @pytest.mark.asyncio
    async def test_exists_false(self, repository, mock_session):
        """Test exists method when record doesn't exist."""
        # Setup
        test_id = uuid4()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = await repository.exists(test_id)
        
        # Verify
        assert result is False
    
    @pytest.mark.asyncio
    async def test_count_with_filters(self, repository, mock_session):
        """Test counting records with filters."""
        # Setup
        filters = {"name": "Test"}
        mock_session.query.return_value.filter.return_value.scalar.return_value = 5
        
        # Execute
        result = await repository.count(filters=filters)
        
        # Verify
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_find_by_filters(self, repository, mock_session):
        """Test finding records by filters."""
        # Setup
        filters = {"name": "Test"}
        mock_records = [TestModel(name="Test Item")]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_records
        
        # Execute
        result = await repository.find_by(filters)
        
        # Verify
        assert len(result) == 1
        assert result[0].name == "Test Item"
    
    @pytest.mark.asyncio
    async def test_find_one_by_filters(self, repository, mock_session):
        """Test finding one record by filters."""
        # Setup
        filters = {"name": "Test"}
        mock_record = TestModel(name="Test Item")
        
        with patch.object(repository, 'find_by', return_value=[mock_record]):
            # Execute
            result = await repository.find_one_by(filters)
            
            # Verify
            assert result == mock_record

    # Bulk Operations Tests
    @pytest.mark.asyncio
    async def test_bulk_create_success(self, repository, mock_session):
        """Test successful bulk creation."""
        # Setup
        objects_data = [
            {"name": "Item 1"},
            {"name": "Item 2"},
            {"name": "Item 3"}
        ]
        
        with patch.object(TestModel, '__init__', return_value=None):
            # Execute
            result = await repository.bulk_create(objects_data)
            
            # Verify
            mock_session.add_all.assert_called_once()
            mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_bulk_create_empty_list(self, repository, mock_session):
        """Test bulk creation with empty list."""
        # Execute
        result = await repository.bulk_create([])
        
        # Verify
        assert result == []
        mock_session.add_all.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_bulk_delete_soft(self, repository, mock_session):
        """Test bulk soft delete."""
        # Setup
        test_ids = [uuid4(), uuid4(), uuid4()]
        mock_records = [TestModel(name=f"Item {i}") for i in range(3)]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_records
        
        # Execute
        result = await repository.bulk_delete(test_ids, soft=True)
        
        # Verify
        assert result == 3
        mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_bulk_delete_hard(self, repository, mock_session):
        """Test bulk hard delete."""
        # Setup
        test_ids = [uuid4(), uuid4(), uuid4()]
        mock_session.query.return_value.filter.return_value.delete.return_value = 3
        
        # Execute
        result = await repository.bulk_delete(test_ids, soft=False)
        
        # Verify
        assert result == 3
        mock_session.flush.assert_called_once()

    # Transaction Management Tests
    @pytest.mark.asyncio
    async def test_begin_transaction(self, repository, mock_session):
        """Test beginning a transaction."""
        # Execute
        await repository.begin_transaction()
        
        # Verify
        mock_session.begin.assert_called_once()
        assert repository._in_transaction is True
    
    @pytest.mark.asyncio
    async def test_commit_transaction(self, repository, mock_session):
        """Test committing a transaction."""
        # Setup
        repository._in_transaction = True
        
        # Execute
        await repository.commit_transaction()
        
        # Verify
        mock_session.commit.assert_called_once()
        assert repository._in_transaction is False
    
    @pytest.mark.asyncio
    async def test_rollback_transaction(self, repository, mock_session):
        """Test rolling back a transaction."""
        # Setup
        repository._in_transaction = True
        
        # Execute
        await repository.rollback_transaction()
        
        # Verify
        mock_session.rollback.assert_called_once()
        assert repository._in_transaction is False

    # Utility Methods Tests
    def test_get_session(self, repository, mock_session):
        """Test getting the database session."""
        # Execute
        result = repository.get_session()
        
        # Verify
        assert result == mock_session
    
    @pytest.mark.asyncio
    async def test_refresh_instance(self, repository, mock_session, sample_model):
        """Test refreshing a model instance."""
        # Execute
        result = await repository.refresh(sample_model)
        
        # Verify
        assert result == sample_model
        mock_session.refresh.assert_called_once_with(sample_model)
    
    @pytest.mark.asyncio
    async def test_flush_session(self, repository, mock_session):
        """Test flushing the database session."""
        # Execute
        await repository.flush()
        
        # Verify
        mock_session.flush.assert_called_once()

    # Error Handling Tests
    @pytest.mark.asyncio
    async def test_database_error_handling(self, repository, mock_session):
        """Test database error handling."""
        # Setup
        mock_session.query.side_effect = Exception("Database connection failed")
        
        # Execute & Verify
        with pytest.raises(DatabaseError) as exc_info:
            await repository.get(uuid4())
        
        assert exc_info.value.error_code == "GET_ERROR"
    
    @pytest.mark.asyncio
    async def test_transaction_error_handling(self, repository, mock_session):
        """Test transaction error handling."""
        # Setup
        mock_session.begin.side_effect = Exception("Transaction failed")
        
        # Execute & Verify
        with pytest.raises(TransactionError) as exc_info:
            await repository.begin_transaction()
        
        assert exc_info.value.error_code == "TRANSACTION_START_ERROR"