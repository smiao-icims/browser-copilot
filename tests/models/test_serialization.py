"""
Tests for model serialization utilities
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from browser_copilot.models.base import SerializableModel
from browser_copilot.models.serialization import ModelEncoder, ModelSerializer


class TestModelEncoder:
    """Test cases for ModelEncoder"""

    def test_datetime_encoding(self):
        """Test datetime objects are encoded to ISO format"""
        encoder = ModelEncoder()
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)

        # Direct encoding
        encoded = encoder.default(dt)
        assert encoded == "2024-01-15T10:30:45+00:00"

        # Through JSON
        json_str = json.dumps({"timestamp": dt}, cls=ModelEncoder)
        assert '"2024-01-15T10:30:45+00:00"' in json_str

    def test_path_encoding(self):
        """Test Path objects are encoded to strings"""
        encoder = ModelEncoder()

        # Unix-style path
        path = Path("/home/user/file.txt")
        # Use str(Path) for cross-platform compatibility
        assert encoder.default(path) == str(path)

        # Relative path
        rel_path = Path("data/test.json")
        # Encoder should return string representation of the path
        encoded = encoder.default(rel_path)
        assert isinstance(encoded, str)
        # Verify it represents the same path
        assert Path(encoded) == rel_path

    def test_serializable_model_encoding(self):
        """Test SerializableModel objects use to_dict method"""

        @dataclass
        class TestModel(SerializableModel):
            name: str
            value: int

            def to_dict(self) -> dict[str, Any]:
                return {"name": self.name, "value": self.value, "type": "test"}

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "TestModel":
                return cls(name=data["name"], value=data["value"])

        model = TestModel(name="test", value=42)
        encoder = ModelEncoder()

        # Should use to_dict method
        encoded = encoder.default(model)
        assert encoded == {"name": "test", "value": 42, "type": "test"}

    def test_dataclass_encoding(self):
        """Test regular dataclasses are encoded using asdict"""

        @dataclass
        class SimpleDataclass:
            field1: str
            field2: int
            field3: list[str]

        obj = SimpleDataclass(field1="test", field2=123, field3=["a", "b"])
        encoder = ModelEncoder()

        encoded = encoder.default(obj)
        assert encoded == {"field1": "test", "field2": 123, "field3": ["a", "b"]}

    def test_nested_encoding(self):
        """Test encoding of nested structures"""

        @dataclass
        class InnerModel(SerializableModel):
            value: int
            timestamp: datetime

            def to_dict(self) -> dict[str, Any]:
                return {"value": self.value, "timestamp": self.timestamp}

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "InnerModel":
                return cls(value=data["value"], timestamp=data["timestamp"])

        @dataclass
        class OuterModel(SerializableModel):
            name: str
            inner: InnerModel
            path: Path

            def to_dict(self) -> dict[str, Any]:
                return {
                    "name": self.name,
                    "inner": self.inner,
                    "path": self.path,
                }

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "OuterModel":
                return cls(
                    name=data["name"],
                    inner=InnerModel.from_dict(data["inner"]),
                    path=Path(data["path"]),
                )

        # Create nested structure
        dt = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)
        inner = InnerModel(value=42, timestamp=dt)
        outer = OuterModel(name="test", inner=inner, path=Path("/test/path"))

        # Encode to JSON
        json_str = json.dumps(outer, cls=ModelEncoder)
        data = json.loads(json_str)

        assert data["name"] == "test"
        assert data["inner"]["value"] == 42
        assert data["inner"]["timestamp"] == "2024-01-15T10:30:00+00:00"
        # Compare Path objects for cross-platform compatibility
        assert Path(data["path"]) == Path("/test/path")

    def test_fallback_to_default(self):
        """Test encoder falls back to default for unknown types"""
        encoder = ModelEncoder()

        # Should raise TypeError for unknown types
        with pytest.raises(TypeError):
            encoder.default(set([1, 2, 3]))


class TestModelSerializer:
    """Test cases for ModelSerializer"""

    def test_to_json_basic(self):
        """Test basic JSON serialization"""

        @dataclass
        class SimpleModel(SerializableModel):
            name: str
            value: int

            def to_dict(self) -> dict[str, Any]:
                return {"name": self.name, "value": self.value}

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "SimpleModel":
                return cls(name=data["name"], value=data["value"])

        model = SimpleModel(name="test", value=42)
        json_str = ModelSerializer.to_json(model)

        # Check JSON is valid and formatted
        data = json.loads(json_str)
        assert data["name"] == "test"
        assert data["value"] == 42
        assert "  " in json_str  # Check indentation

    def test_to_json_compact(self):
        """Test compact JSON serialization"""

        @dataclass
        class CompactModel(SerializableModel):
            field1: str
            field2: int

            def to_dict(self) -> dict[str, Any]:
                return {"field1": self.field1, "field2": self.field2}

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "CompactModel":
                return cls(field1=data["field1"], field2=data["field2"])

        model = CompactModel(field1="test", field2=123)
        json_str = ModelSerializer.to_json(model, indent=None)

        # Should be compact (no extra whitespace)
        assert json_str == '{"field1": "test", "field2": 123}'

    def test_from_json_basic(self):
        """Test basic JSON deserialization"""

        @dataclass
        class DeserializeModel(SerializableModel):
            name: str
            count: int
            active: bool

            def to_dict(self) -> dict[str, Any]:
                return {"name": self.name, "count": self.count, "active": self.active}

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "DeserializeModel":
                return cls(
                    name=data["name"],
                    count=data["count"],
                    active=data["active"],
                )

        json_str = '{"name": "test", "count": 42, "active": true}'
        model = ModelSerializer.from_json(json_str, DeserializeModel)

        assert model.name == "test"
        assert model.count == 42
        assert model.active is True

    def test_serialization_round_trip(self):
        """Test round-trip serialization/deserialization"""

        @dataclass
        class RoundTripModel(SerializableModel):
            id: int
            name: str
            values: list[float]
            metadata: dict[str, Any]

            def to_dict(self) -> dict[str, Any]:
                return {
                    "id": self.id,
                    "name": self.name,
                    "values": self.values,
                    "metadata": self.metadata,
                }

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "RoundTripModel":
                return cls(
                    id=data["id"],
                    name=data["name"],
                    values=data["values"],
                    metadata=data["metadata"],
                )

        # Create original model
        original = RoundTripModel(
            id=123,
            name="Test Model",
            values=[1.1, 2.2, 3.3],
            metadata={"key1": "value1", "key2": 42, "key3": True},
        )

        # Serialize and deserialize
        json_str = ModelSerializer.to_json(original)
        restored = ModelSerializer.from_json(json_str, RoundTripModel)

        # Verify all fields match
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.values == original.values
        assert restored.metadata == original.metadata

    def test_from_json_invalid_data(self):
        """Test deserialization with invalid JSON"""

        @dataclass
        class TestModel(SerializableModel):
            value: int

            def to_dict(self) -> dict[str, Any]:
                return {"value": self.value}

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "TestModel":
                return cls(value=data["value"])

        # Invalid JSON
        with pytest.raises(json.JSONDecodeError):
            ModelSerializer.from_json("not valid json", TestModel)

        # Missing required field
        with pytest.raises(KeyError):
            ModelSerializer.from_json('{"wrong_field": 42}', TestModel)

    def test_complex_type_preservation(self):
        """Test preservation of complex types through serialization"""

        @dataclass
        class ComplexModel(SerializableModel):
            timestamp: datetime
            path: Path
            nullable: str | None
            nested: dict[str, list[int]]

            def to_dict(self) -> dict[str, Any]:
                return {
                    "timestamp": self.timestamp,
                    "path": self.path,
                    "nullable": self.nullable,
                    "nested": self.nested,
                }

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "ComplexModel":
                return cls(
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    path=Path(data["path"]),
                    nullable=data.get("nullable"),
                    nested=data["nested"],
                )

        # Create model with complex types
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        model = ComplexModel(
            timestamp=dt,
            path=Path("/test/file.txt"),
            nullable=None,
            nested={"key1": [1, 2, 3], "key2": [4, 5, 6]},
        )

        # Serialize and deserialize
        json_str = ModelSerializer.to_json(model)
        restored = ModelSerializer.from_json(json_str, ComplexModel)

        # Verify types are preserved
        assert restored.timestamp == dt
        assert restored.path == Path("/test/file.txt")
        assert restored.nullable is None
        assert restored.nested == {"key1": [1, 2, 3], "key2": [4, 5, 6]}
