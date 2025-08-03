"""
Base class for standalone models that can operate without database connections.

This module provides the foundation for models that support both database-backed
and in-memory operation modes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
import uuid


class ModelMode(str, Enum):
    """Model operation modes."""
    DATABASE = "database"      # Full database functionality
    STANDALONE = "standalone"  # In-memory only, no database
    AUTO = "auto"             # Automatically detect best mode


class StandaloneModel(BaseModel):
    """
    Base class for models that can operate without database connections.
    
    This class provides:
    - Pydantic validation and serialization
    - Business logic methods that don't require database access
    - Mock implementations for database-dependent features
    - Consistent interface with database-backed models
    """
    
    model_config = ConfigDict(
        # Allow extra fields for flexibility
        extra="allow",
        # Use enum values for serialization
        use_enum_values=True,
        # Validate assignments
        validate_assignment=True,
        # Allow arbitrary types for complex fields
        arbitrary_types_allowed=True
    )
    
    # Common fields that most models will have
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Model ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    
    def __init__(self, **data):
        """Initialize the standalone model."""
        super().__init__(**data)
        self._mode = ModelMode.STANDALONE
        self._in_memory_storage = {}
    
    @property
    def mode(self) -> ModelMode:
        """Get the current model mode."""
        return self._mode
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary representation."""
        return self.model_dump()
    
    def to_json(self) -> str:
        """Convert model to JSON string."""
        return self.model_dump_json()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StandaloneModel":
        """Create model instance from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "StandaloneModel":
        """Create model instance from JSON string."""
        return cls.model_validate_json(json_str)
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)
    
    def get_age_seconds(self) -> float:
        """Get model age in seconds."""
        return (datetime.now(timezone.utc) - self.created_at).total_seconds()
    
    def get_age_minutes(self) -> float:
        """Get model age in minutes."""
        return self.get_age_seconds() / 60
    
    def get_age_hours(self) -> float:
        """Get model age in hours."""
        return self.get_age_minutes() / 60
    
    def get_age_days(self) -> float:
        """Get model age in days."""
        return self.get_age_hours() / 24
    
    # Mock database operations for testing
    async def save(self) -> "StandaloneModel":
        """
        Mock save operation for standalone models.
        
        In standalone mode, this just updates the timestamp and returns self.
        """
        self.update_timestamp()
        return self
    
    async def delete(self) -> None:
        """
        Mock delete operation for standalone models.
        
        In standalone mode, this is a no-op.
        """
        pass
    
    @classmethod
    async def find_one(cls, filter_dict: Dict[str, Any]) -> Optional["StandaloneModel"]:
        """
        Mock find_one operation for standalone models.
        
        In standalone mode, this returns None as there's no persistent storage.
        """
        return None
    
    @classmethod
    async def find_many(cls, filter_dict: Dict[str, Any], limit: Optional[int] = None) -> List["StandaloneModel"]:
        """
        Mock find_many operation for standalone models.
        
        In standalone mode, this returns an empty list as there's no persistent storage.
        """
        return []
    
    @classmethod
    async def count_documents(cls, filter_dict: Dict[str, Any]) -> int:
        """
        Mock count operation for standalone models.
        
        In standalone mode, this returns 0 as there's no persistent storage.
        """
        return 0
    
    def _store_in_memory(self, key: str, value: Any) -> None:
        """Store a value in the in-memory storage."""
        self._in_memory_storage[key] = value
    
    def _get_from_memory(self, key: str, default: Any = None) -> Any:
        """Get a value from the in-memory storage."""
        return self._in_memory_storage.get(key, default)
    
    def _clear_memory(self) -> None:
        """Clear the in-memory storage."""
        self._in_memory_storage.clear()
    
    def __str__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}(id={self.id}, mode={self.mode.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the model."""
        return f"{self.__class__.__name__}(id={self.id}, mode={self.mode.value}, created_at={self.created_at})"


class StandaloneDocument(StandaloneModel):
    """
    Alternative base class that mimics Beanie Document interface.
    
    This class provides a more Document-like interface for models that
    need to be compatible with existing Beanie-based code.
    """
    
    def __init__(self, **data):
        """Initialize the standalone document."""
        super().__init__(**data)
    
    @classmethod
    async def get(cls, document_id: str) -> Optional["StandaloneDocument"]:
        """Mock get operation by ID."""
        return None
    
    @classmethod
    async def find(cls, *args, **kwargs):
        """Mock find operation that returns a mock cursor."""
        return MockCursor([])
    
    @classmethod
    async def find_all(cls) -> List["StandaloneDocument"]:
        """Mock find_all operation."""
        return []
    
    @classmethod
    async def aggregate(cls, pipeline: List[Dict[str, Any]]):
        """Mock aggregate operation."""
        return MockCursor([])
    
    async def insert(self) -> "StandaloneDocument":
        """Mock insert operation."""
        self.update_timestamp()
        return self
    
    async def replace(self) -> "StandaloneDocument":
        """Mock replace operation."""
        self.update_timestamp()
        return self
    
    async def update(self, *args, **kwargs) -> "StandaloneDocument":
        """Mock update operation."""
        self.update_timestamp()
        return self


class MockCursor:
    """Mock cursor for database query results."""
    
    def __init__(self, results: List[Any]):
        """Initialize with mock results."""
        self.results = results
        self._limit = None
        self._sort_fields = []
    
    def limit(self, count: int) -> "MockCursor":
        """Mock limit operation."""
        self._limit = count
        return self
    
    def sort(self, *args, **kwargs) -> "MockCursor":
        """Mock sort operation."""
        self._sort_fields.extend(args)
        return self
    
    async def to_list(self, length: Optional[int] = None) -> List[Any]:
        """Convert cursor to list."""
        results = self.results
        
        # Apply limit if set
        if self._limit is not None:
            results = results[:self._limit]
        
        # Apply length limit if specified
        if length is not None:
            results = results[:length]
        
        return results
    
    def __aiter__(self):
        """Async iterator support."""
        return self
    
    async def __anext__(self):
        """Async iterator next."""
        if not self.results:
            raise StopAsyncIteration
        return self.results.pop(0)