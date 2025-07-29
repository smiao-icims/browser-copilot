"""
Tests for base model classes
"""

import json
from dataclasses import dataclass
from typing import Any

import pytest

from browser_copilot.models.base import SerializableModel, ValidatedModel


class TestSerializableModel:
    """Test cases for SerializableModel"""

    def test_abstract_methods_must_be_implemented(self):
        """Test that abstract methods must be implemented"""
        with pytest.raises(TypeError):
            # Should fail because abstract methods not implemented
            SerializableModel()  # type: ignore

    def test_concrete_implementation(self):
        """Test concrete implementation of SerializableModel"""

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