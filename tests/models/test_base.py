"""
Tests for base model classes
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest


class TestSerializableModel:
    """Test cases for SerializableModel"""

    def test_abstract_methods_must_be_implemented(self):
        """Test that abstract methods must be implemented"""
        # This will fail until we implement SerializableModel
        from browser_copilot.models.base import SerializableModel

        with pytest.raises(TypeError):
            # Should fail because abstract methods not implemented
            SerializableModel()  # type: ignore

    def test_concrete_implementation(self):
        """Test concrete implementation of SerializableModel"""
        from browser_copilot.models.base import SerializableModel

        @dataclass
        class ConcreteModel(SerializableModel):
            name: str
            value: int

            def to_dict(self) -> dict[str, Any]:
                return {"name": self.name, "value": self.value}

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "ConcreteModel":
                return cls(name=data["name"], value=data["value"])

        # Test creation and serialization
        model = ConcreteModel(name="test", value=42)
        assert model.name == "test"
        assert model.value == 42

        # Test to_dict
        data = model.to_dict()
        assert data == {"name": "test", "value": 42}

        # Test from_dict
        restored = ConcreteModel.from_dict(data)
        assert restored.name == "test"
        assert restored.value == 42


class TestValidatedModel:
    """Test cases for ValidatedModel"""

    def test_validation_called_on_init(self):
        """Test that validation is called during initialization"""
        from browser_copilot.models.base import ValidatedModel

        validation_called = False

        @dataclass
        class ValidatedTestModel(ValidatedModel):
            value: int

            def validate(self) -> None:
                nonlocal validation_called
                validation_called = True
                if self.value < 0:
                    raise ValueError("Value must be non-negative")

            def to_dict(self) -> dict[str, Any]:
                return {"value": self.value}

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "ValidatedTestModel":
                return cls(value=data["value"])

        # Valid case
        model = ValidatedTestModel(value=10)
        assert validation_called
        assert model.value == 10

        # Invalid case
        with pytest.raises(ValueError, match="Value must be non-negative"):
            ValidatedTestModel(value=-1)

    def test_complex_validation_rules(self):
        """Test complex validation scenarios"""
        from browser_copilot.models.base import ValidatedModel

        @dataclass
        class ComplexModel(ValidatedModel):
            name: str
            age: int
            email: str

            def validate(self) -> None:
                # Name validation
                if not self.name or len(self.name) < 2:
                    raise ValueError("Name must be at least 2 characters")

                # Age validation
                if not 0 <= self.age <= 150:
                    raise ValueError("Age must be between 0 and 150")

                # Email validation (simple check)
                if "@" not in self.email:
                    raise ValueError("Invalid email format")

            def to_dict(self) -> dict[str, Any]:
                return {"name": self.name, "age": self.age, "email": self.email}

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "ComplexModel":
                return cls(
                    name=data["name"],
                    age=data["age"],
                    email=data["email"],
                )

        # Valid model
        model = ComplexModel(name="John Doe", age=30, email="john@example.com")
        assert model.name == "John Doe"

        # Invalid name
        with pytest.raises(ValueError, match="Name must be at least 2 characters"):
            ComplexModel(name="J", age=30, email="john@example.com")

        # Invalid age
        with pytest.raises(ValueError, match="Age must be between 0 and 150"):
            ComplexModel(name="John", age=200, email="john@example.com")

        # Invalid email
        with pytest.raises(ValueError, match="Invalid email format"):
            ComplexModel(name="John", age=30, email="invalid-email")

    def test_validation_on_from_dict(self):
        """Test that validation occurs when creating from dict"""
        from browser_copilot.models.base import ValidatedModel

        @dataclass
        class StrictModel(ValidatedModel):
            positive_value: float

            def validate(self) -> None:
                if self.positive_value <= 0:
                    raise ValueError("Value must be positive")

            def to_dict(self) -> dict[str, Any]:
                return {"positive_value": self.positive_value}

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "StrictModel":
                return cls(positive_value=data["positive_value"])

        # Valid data
        model = StrictModel.from_dict({"positive_value": 1.5})
        assert model.positive_value == 1.5

        # Invalid data
        with pytest.raises(ValueError, match="Value must be positive"):
            StrictModel.from_dict({"positive_value": -1.0})

    def test_inheritance_chain(self):
        """Test that validation works through inheritance"""
        from browser_copilot.models.base import ValidatedModel

        @dataclass
        class BaseValidated(ValidatedModel):
            base_field: str

            def validate(self) -> None:
                if not self.base_field:
                    raise ValueError("Base field cannot be empty")

            def to_dict(self) -> dict[str, Any]:
                return {"base_field": self.base_field}

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "BaseValidated":
                return cls(base_field=data["base_field"])

        @dataclass
        class ExtendedValidated(BaseValidated):
            extended_field: int

            def validate(self) -> None:
                # Call parent validation
                super().validate()
                # Add own validation
                if self.extended_field < 0:
                    raise ValueError("Extended field must be non-negative")

            def to_dict(self) -> dict[str, Any]:
                data = super().to_dict()
                data["extended_field"] = self.extended_field
                return data

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "ExtendedValidated":
                return cls(
                    base_field=data["base_field"],
                    extended_field=data["extended_field"],
                )

        # Valid case
        model = ExtendedValidated(base_field="test", extended_field=5)
        assert model.base_field == "test"
        assert model.extended_field == 5

        # Invalid base field
        with pytest.raises(ValueError, match="Base field cannot be empty"):
            ExtendedValidated(base_field="", extended_field=5)

        # Invalid extended field
        with pytest.raises(ValueError, match="Extended field must be non-negative"):
            ExtendedValidated(base_field="test", extended_field=-1)

    def test_to_json_method(self):
        """Test JSON serialization through to_json method"""
        from browser_copilot.models.base import ValidatedModel

        @dataclass
        class JsonModel(ValidatedModel):
            name: str
            value: int

            def validate(self) -> None:
                pass  # No validation needed for this test

            def to_dict(self) -> dict[str, Any]:
                return {"name": self.name, "value": self.value}

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "JsonModel":
                return cls(name=data["name"], value=data["value"])

        model = JsonModel(name="test", value=42)
        json_str = model.to_json()

        assert json_str == '{"name": "test", "value": 42}'
        assert json.loads(json_str) == {"name": "test", "value": 42}

    def test_to_json_with_indent(self):
        """Test JSON serialization with indentation"""
        from browser_copilot.models.base import ValidatedModel

        @dataclass
        class JsonModel(ValidatedModel):
            name: str

            def validate(self) -> None:
                pass

            def to_dict(self) -> dict[str, Any]:
                return {"name": self.name}

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "JsonModel":
                return cls(name=data["name"])

        model = JsonModel(name="test")
        json_str = model.to_json(indent=2)

        expected = '{\n  "name": "test"\n}'
        assert json_str == expected


class TestModelJSONEncoder:
    """Test custom JSON encoder for special types"""

    def test_datetime_encoding(self):
        """Test datetime encoding to ISO format"""
        from browser_copilot.models.serialization import ModelJSONEncoder

        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        encoded = json.dumps({"timestamp": dt}, cls=ModelJSONEncoder)

        assert encoded == '{"timestamp": "2024-01-15T10:30:45+00:00"}'

    def test_path_encoding(self):
        """Test Path encoding to string"""
        from browser_copilot.models.serialization import ModelJSONEncoder

        path = Path("/home/user/file.txt")
        encoded = json.dumps({"path": path}, cls=ModelJSONEncoder)

        # Parse the JSON to check the value (handles platform-specific path separators)
        decoded = json.loads(encoded)
        assert "path" in decoded
        assert decoded["path"] == str(path)  # str(Path) handles platform differences

    def test_nested_encoding(self):
        """Test encoding of nested structures"""
        from browser_copilot.models.serialization import ModelJSONEncoder

        data = {
            "timestamp": datetime.now(UTC),
            "files": [Path("/file1.txt"), Path("/file2.txt")],
            "metadata": {
                "created": datetime(2024, 1, 1, tzinfo=UTC),
                "path": Path("/metadata"),
            },
        }

        # Should not raise any errors
        encoded = json.dumps(data, cls=ModelJSONEncoder)
        decoded = json.loads(encoded)

        # Check structure is preserved
        assert "timestamp" in decoded
        assert len(decoded["files"]) == 2
        # Use Path comparison for cross-platform compatibility
        assert Path(decoded["metadata"]["path"]) == Path("/metadata")

    def test_serializable_model_encoding(self):
        """Test encoding of SerializableModel instances"""
        from browser_copilot.models.base import SerializableModel
        from browser_copilot.models.serialization import ModelJSONEncoder

        @dataclass
        class TestModel(SerializableModel):
            name: str
            created: datetime

            def to_dict(self) -> dict[str, Any]:
                return {"name": self.name, "created": self.created}

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> "TestModel":
                return cls(name=data["name"], created=data["created"])

        model = TestModel(name="test", created=datetime(2024, 1, 1, tzinfo=UTC))

        # Model should have to_dict method recognized by encoder
        data = {"model": model, "timestamp": datetime.now(UTC)}
        encoded = json.dumps(data, cls=ModelJSONEncoder)
        decoded = json.loads(encoded)

        assert decoded["model"]["name"] == "test"
        assert "2024-01-01" in decoded["model"]["created"]


class TestSerializationHelpers:
    """Test serialization helper functions"""

    def test_serialize_datetime(self):
        """Test datetime serialization helper"""
        from browser_copilot.models.serialization import serialize_datetime

        # With timezone
        dt_utc = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        assert serialize_datetime(dt_utc) == "2024-01-15T10:30:45+00:00"

        # Without timezone (should add UTC)
        dt_naive = datetime(2024, 1, 15, 10, 30, 45)
        serialized = serialize_datetime(dt_naive)
        assert "+00:00" in serialized or "Z" in serialized

    def test_deserialize_datetime(self):
        """Test datetime deserialization helper"""
        from browser_copilot.models.serialization import deserialize_datetime

        # ISO format with timezone
        dt_str = "2024-01-15T10:30:45+00:00"
        dt = deserialize_datetime(dt_str)
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 10
        assert dt.minute == 30
        assert dt.second == 45
        assert dt.tzinfo is not None

        # ISO format with Z
        dt_str_z = "2024-01-15T10:30:45Z"
        dt_z = deserialize_datetime(dt_str_z)
        assert dt_z.tzinfo is not None

    def test_serialize_path(self):
        """Test Path serialization helper"""
        from browser_copilot.models.serialization import serialize_path

        # Absolute path
        path = Path("/home/user/file.txt")
        assert serialize_path(path) == str(path)

        # Relative path
        rel_path = Path("./relative/path.txt")
        # Path normalizes "./relative" to "relative"
        # Use Path object comparison to handle platform differences
        assert serialize_path(rel_path) == str(Path("relative/path.txt"))

        # Windows path (if on Windows)
        if Path("C:\\").exists():
            win_path = Path("C:\\Users\\file.txt")
            assert serialize_path(win_path) == "C:\\Users\\file.txt"

    def test_deserialize_path(self):
        """Test Path deserialization helper"""
        from browser_copilot.models.serialization import deserialize_path

        # String to Path
        path_str = "/home/user/file.txt"
        path = deserialize_path(path_str)
        assert isinstance(path, Path)
        # On Windows, forward slashes get converted to backslashes
        assert Path(str(path)) == Path(path_str)

        # Empty string
        empty_path = deserialize_path("")
        assert isinstance(empty_path, Path)
        assert str(empty_path) == "."
