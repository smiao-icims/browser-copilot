"""
Base classes for Browser Copilot data models

Provides abstract base classes for serializable and validated models.
"""

import json
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

    def to_json(self, indent: int | None = None) -> str:
        """
        Convert the model to a JSON string.

        Args:
            indent: Number of spaces for indentation (None for compact)

        Returns:
            JSON string representation
        """
        from .serialization import ModelJSONEncoder

        return json.dumps(self.to_dict(), cls=ModelJSONEncoder, indent=indent)

    @classmethod
    def from_json(cls: type[T], json_str: str) -> T:
        """
        Create a model instance from a JSON string.

        Args:
            json_str: JSON string containing model data

        Returns:
            New instance of the model
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


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
