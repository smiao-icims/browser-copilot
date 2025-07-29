"""
Tests for LLMManager component
"""

from unittest.mock import MagicMock, patch

import pytest
from modelforge.exceptions import ConfigurationError as ModelForgeConfigError
from modelforge.exceptions import ModelNotFoundError, ProviderError

from browser_copilot.components.exceptions import ConfigurationError
from browser_copilot.components.llm_manager import LLMManager
from browser_copilot.components.models import ModelMetadata
from browser_copilot.config_manager import ConfigManager


class TestLLMManager:
    """Test cases for LLMManager"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock ConfigManager"""
        config = MagicMock(spec=ConfigManager)
        config.get.return_value = None
        config.get_model_config.return_value = {
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        return config

    @pytest.fixture
    def mock_registry(self):
        """Create a mock ModelForgeRegistry"""
        with patch("browser_copilot.components.llm_manager.ModelForgeRegistry") as mock:
            yield mock

    def test_init_creates_registry(self, mock_config, mock_registry):
        """Test that LLMManager initializes with registry"""
        # Act
        manager = LLMManager("openai", "gpt-4", mock_config)

        # Assert
        assert manager.provider == "openai"
        assert manager.model == "gpt-4"
        assert manager.config == mock_config
        mock_registry.assert_called_once()

    def test_create_llm_success(self, mock_config, mock_registry):
        """Test successful LLM creation"""
        # Arrange
        mock_llm = MagicMock()
        mock_llm.temperature = None
        mock_llm.max_tokens = None
        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.get_llm.return_value = mock_llm

        callbacks = [MagicMock()]
        manager = LLMManager("openai", "gpt-4", mock_config)

        # Act
        llm = manager.create_llm(callbacks)

        # Assert
        assert llm == mock_llm
        mock_registry_instance.get_llm.assert_called_once_with(
            provider_name="openai",
            model_alias="gpt-4",
            callbacks=callbacks,
            enhanced=True,
        )
        assert mock_llm.temperature == 0.7
        assert mock_llm.max_tokens == 4096

    def test_create_llm_provider_error(self, mock_config, mock_registry):
        """Test LLM creation with provider error"""
        # Arrange
        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.get_llm.side_effect = ProviderError("Invalid provider")

        manager = LLMManager("invalid", "model", mock_config)

        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            manager.create_llm([])
        assert "Failed to load LLM: Invalid provider" in str(exc_info.value)

    def test_create_llm_model_not_found(self, mock_config, mock_registry):
        """Test LLM creation with model not found"""
        # Arrange
        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.get_llm.side_effect = ModelNotFoundError("openai", "invalid-model")

        manager = LLMManager("openai", "invalid-model", mock_config)

        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            manager.create_llm([])
        assert "Failed to load LLM:" in str(exc_info.value)

    def test_create_llm_configuration_error(self, mock_config, mock_registry):
        """Test LLM creation with configuration error"""
        # Arrange
        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.get_llm.side_effect = ModelForgeConfigError("Bad config")

        manager = LLMManager("openai", "gpt-4", mock_config)

        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            manager.create_llm([])
        assert "Failed to load LLM: Bad config" in str(exc_info.value)

    def test_create_llm_without_temperature_support(self, mock_config, mock_registry):
        """Test LLM creation when model doesn't support temperature"""
        # Arrange
        mock_llm = MagicMock()
        # Remove temperature attribute
        del mock_llm.temperature
        mock_llm.max_tokens = None

        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.get_llm.return_value = mock_llm

        manager = LLMManager("openai", "gpt-4", mock_config)

        # Act
        llm = manager.create_llm([])

        # Assert
        assert llm == mock_llm
        assert not hasattr(llm, "temperature")
        assert mock_llm.max_tokens == 4096

    def test_get_model_metadata_from_llm_properties(self, mock_config, mock_registry):
        """Test getting model metadata from LLM properties"""
        # Arrange
        mock_llm = MagicMock()
        mock_llm.context_length = 128000
        mock_llm.model_info = {
            "limit": {"context": 200000},
            "pricing": {
                "prompt": 0.01,
                "completion": 0.03,
            },
        }

        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.get_llm.return_value = mock_llm

        manager = LLMManager("openai", "gpt-4", mock_config)
        manager.create_llm([])  # Initialize LLM

        # Act
        metadata = manager.get_model_metadata()

        # Assert
        assert isinstance(metadata, ModelMetadata)
        assert metadata.context_length == 128000  # Uses property over model_info
        assert metadata.cost_per_1k_prompt == 0.01
        assert metadata.cost_per_1k_completion == 0.03
        assert metadata.supports_streaming is True
        assert metadata.supports_tools is True

    def test_get_model_metadata_from_model_info(self, mock_config, mock_registry):
        """Test getting model metadata from model_info when property not available"""
        # Arrange
        mock_llm = MagicMock()
        mock_llm.context_length = None  # No property
        mock_llm.model_info = {
            "limit": {"context": 200000},
            "pricing": {
                "prompt": 0.005,
                "completion": 0.015,
            },
        }

        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.get_llm.return_value = mock_llm

        manager = LLMManager("openai", "gpt-4", mock_config)
        manager.create_llm([])

        # Act
        metadata = manager.get_model_metadata()

        # Assert
        assert metadata.context_length == 200000  # From model_info
        assert metadata.cost_per_1k_prompt == 0.005
        assert metadata.cost_per_1k_completion == 0.015

    def test_get_model_metadata_fallback(self, mock_config, mock_registry):
        """Test model metadata with fallback values"""
        # Arrange
        mock_llm = MagicMock()
        mock_llm.context_length = None
        mock_llm.model_info = None

        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.get_llm.return_value = mock_llm

        manager = LLMManager("github_copilot", "gpt-4o", mock_config)
        manager.create_llm([])

        # Act
        metadata = manager.get_model_metadata()

        # Assert
        assert metadata.context_length == 128000  # Fallback value
        assert metadata.cost_per_1k_prompt is None
        assert metadata.cost_per_1k_completion is None

    def test_get_model_metadata_no_llm(self, mock_config, mock_registry):
        """Test getting metadata before LLM is created"""
        # Arrange
        manager = LLMManager("openai", "gpt-4", mock_config)

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            manager.get_model_metadata()
        assert "LLM not initialized" in str(exc_info.value)

    def test_estimate_cost_with_pricing(self, mock_config, mock_registry):
        """Test cost estimation with pricing information"""
        # Arrange
        mock_llm = MagicMock()
        mock_llm.model_info = {
            "pricing": {
                "prompt": 0.01,  # $0.01 per 1k tokens
                "completion": 0.03,  # $0.03 per 1k tokens
            }
        }

        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.get_llm.return_value = mock_llm

        manager = LLMManager("openai", "gpt-4", mock_config)
        manager.create_llm([])

        # Act
        cost = manager.estimate_cost(prompt_tokens=2000, completion_tokens=500)

        # Assert
        expected_cost = (2000 / 1000 * 0.01) + (500 / 1000 * 0.03)
        assert cost == expected_cost
        assert cost == 0.035  # $0.02 + $0.015

    def test_estimate_cost_with_llm_method(self, mock_config, mock_registry):
        """Test cost estimation using LLM's estimate_cost method"""
        # Arrange
        mock_llm = MagicMock()
        mock_llm.model_info = None
        mock_llm.estimate_cost.return_value = 0.05

        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.get_llm.return_value = mock_llm

        manager = LLMManager("openai", "gpt-4", mock_config)
        manager.create_llm([])

        # Act
        cost = manager.estimate_cost(prompt_tokens=1000, completion_tokens=1000)

        # Assert
        assert cost == 0.05
        mock_llm.estimate_cost.assert_called_once_with(1000, 1000)

    def test_estimate_cost_no_pricing_info(self, mock_config, mock_registry):
        """Test cost estimation without pricing information"""
        # Arrange
        mock_llm = MagicMock()
        mock_llm.model_info = None
        # No estimate_cost method
        del mock_llm.estimate_cost

        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.get_llm.return_value = mock_llm

        manager = LLMManager("openai", "gpt-4", mock_config)
        manager.create_llm([])

        # Act
        cost = manager.estimate_cost(prompt_tokens=1000, completion_tokens=1000)

        # Assert
        assert cost is None

    def test_get_llm_returns_created_instance(self, mock_config, mock_registry):
        """Test get_llm returns the created LLM instance"""
        # Arrange
        mock_llm = MagicMock()
        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.get_llm.return_value = mock_llm

        manager = LLMManager("openai", "gpt-4", mock_config)
        created_llm = manager.create_llm([])

        # Act
        retrieved_llm = manager.get_llm()

        # Assert
        assert retrieved_llm is created_llm
        assert retrieved_llm is mock_llm

    def test_get_llm_before_creation(self, mock_config, mock_registry):
        """Test get_llm raises error before LLM is created"""
        # Arrange
        manager = LLMManager("openai", "gpt-4", mock_config)

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            manager.get_llm()
        assert "LLM not initialized" in str(exc_info.value)