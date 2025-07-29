"""
Serialization utilities for data models

Provides custom JSON encoder and serialization helpers.
"""

import dataclasses
import json
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

from .base import SerializableModel

T = TypeVar("T", bound=SerializableModel)


class ModelEncoder(json.JSONEncoder):
    """Custom JSON encoder for data models"""

    def default(self, obj: Any) -> Any:
        """
        Encode objects to JSON-serializable format

        Args:
            obj: Object to encode

        Returns:
            JSON-serializable representation
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return dataclasses.asdict(obj)
        return super().default(obj)


class ModelSerializer:
    """Serialization utilities for data models"""

    @staticmethod
    def to_json(model: SerializableModel, indent: int | None = 2) -> str:
        """
        Serialize model to JSON string

        Args:
            model: Model to serialize
            indent: JSON indentation (None for compact)

        Returns:
            JSON string representation
        """
        return json.dumps(model.to_dict(), cls=ModelEncoder, indent=indent)

    @staticmethod
    def from_json(json_str: str, model_class: type[T]) -> T:
        """
        Deserialize model from JSON string

        Args:
            json_str: JSON string to parse
            model_class: Class to deserialize to

        Returns:
            Deserialized model instance

        Raises:
            ValueError: If JSON is invalid or model validation fails
        """
        data = json.loads(json_str)
        return model_class.from_dict(data)
