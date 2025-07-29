"""
Base classes for Browser Copilot data models

Provides abstract base classes for serializable and validated models.
"""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

T = TypeVar("T", bound="SerializableModel")


class SerializableModel(ABC):
    """Base class for all serializable models"""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """
        Convert model to dictionary representation

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """
        Create instance from dictionary

        Args:
            data: Dictionary representation of the model

        Returns:
            New instance of the model

        Raises:
            ValueError: If data is invalid or missing required fields
        """
        pass


class ValidatedModel(SerializableModel):
    """Base class for models with validation"""

    def __post_init__(self) -> None:
        """Validate model after construction"""
        self.validate()

    @abstractmethod
    def validate(self) -> None:
        """
        Validate model constraints

        Raises:
            ValueError: If model data violates constraints
        """
        pass
