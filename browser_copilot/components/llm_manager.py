"""
LLM Manager component for Browser Copilot

Handles LLM initialization, configuration, and metadata management.
"""

import logging
from typing import Any

from modelforge.exceptions import ConfigurationError as ModelForgeConfigError
from modelforge.exceptions import ModelNotFoundError, ProviderError
from modelforge.registry import ModelForgeRegistry

from ..config_manager import ConfigManager
from .exceptions import ConfigurationError
from .models import ModelMetadata

logger = logging.getLogger(__name__)


class LLMManager:
    """Manages LLM lifecycle and configuration"""

    # Fallback context limits when model metadata is unavailable
    FALLBACK_CONTEXT_LIMITS = {
        "github_copilot_gpt_4o": 128000,
        "openai_gpt_4o": 128000,
        "anthropic_claude_3_5_sonnet": 200000,
        "google_gemini_1_5_pro": 2000000,
    }

    def __init__(self, provider: str, model: str, config: ConfigManager):
        """
        Initialize LLM Manager

        Args:
            provider: LLM provider name (e.g., 'github_copilot', 'openai')
            model: Model name (e.g., 'gpt-4o', 'claude-3-opus')
            config: Configuration manager instance
        """
        self.provider = provider
        self.model = model
        self.config = config
        self.registry = ModelForgeRegistry()
        self._llm: Any | None = None

    def create_llm(self, callbacks: list[Any]) -> Any:
        """
        Create and configure LLM instance

        Args:
            callbacks: List of callbacks to attach to the LLM

        Returns:
            Configured LLM instance

        Raises:
            ConfigurationError: If LLM creation fails
        """
        try:
            # Initialize LLM with enhanced mode for metadata access
            self._llm = self.registry.get_llm(
                provider_name=self.provider,
                model_alias=self.model,
                callbacks=callbacks,
                enhanced=True,
            )

            # Apply model configuration if supported
            model_config = self.config.get_model_config()

            # Set temperature if supported
            if (
                hasattr(self._llm, "temperature")
                and model_config.get("temperature") is not None
            ):
                self._llm.temperature = model_config.get("temperature")

            # Set max_tokens if supported
            if (
                hasattr(self._llm, "max_tokens")
                and model_config.get("max_tokens") is not None
            ):
                self._llm.max_tokens = model_config.get("max_tokens")

            logger.debug(
                f"Created LLM: provider={self.provider}, model={self.model}, "
                f"enhanced=True, callbacks={len(callbacks)}"
            )

            return self._llm

        except (ProviderError, ModelNotFoundError, ModelForgeConfigError) as e:
            raise ConfigurationError(f"Failed to load LLM: {e}")

    def get_model_metadata(self) -> ModelMetadata:
        """
        Retrieve model capabilities and limits

        Returns:
            ModelMetadata with context length, pricing, and capabilities

        Raises:
            RuntimeError: If LLM is not initialized
        """
        if not self._llm:
            raise RuntimeError("LLM not initialized. Call create_llm() first.")

        # Extract context length
        context_length = None

        # Priority 1: Direct context_length property
        if hasattr(self._llm, "context_length") and self._llm.context_length:
            context_length = self._llm.context_length

        # Priority 2: Model info limit
        elif hasattr(self._llm, "model_info") and isinstance(
            self._llm.model_info, dict
        ):
            limit_info = self._llm.model_info.get("limit", {})
            if "context" in limit_info:
                context_length = limit_info["context"]

        # Priority 3: Fallback to hardcoded limits
        if not context_length:
            model_key = (
                f"{self.provider}_{self.model}".lower()
                .replace("-", "_")
                .replace(".", "_")
            )
            context_length = self.FALLBACK_CONTEXT_LIMITS.get(model_key)

            if not context_length:
                # Try to match by model name only
                for key, limit in self.FALLBACK_CONTEXT_LIMITS.items():
                    if self.model.lower().replace("-", "_").replace(".", "_") in key:
                        context_length = limit
                        break

        # Extract pricing information
        cost_per_1k_prompt = None
        cost_per_1k_completion = None

        if hasattr(self._llm, "model_info") and isinstance(self._llm.model_info, dict):
            pricing = self._llm.model_info.get("pricing", {})
            if "prompt" in pricing:
                cost_per_1k_prompt = pricing["prompt"]
            if "completion" in pricing:
                cost_per_1k_completion = pricing["completion"]

        return ModelMetadata(
            context_length=context_length or 128000,  # Default to 128k
            supports_streaming=True,
            supports_tools=True,
            cost_per_1k_prompt=cost_per_1k_prompt,
            cost_per_1k_completion=cost_per_1k_completion,
        )

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float | None:
        """
        Estimate token costs

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Estimated cost in USD, or None if pricing unavailable
        """
        if not self._llm:
            raise RuntimeError("LLM not initialized. Call create_llm() first.")

        # Try to get pricing from model info
        if hasattr(self._llm, "model_info") and isinstance(self._llm.model_info, dict):
            pricing = self._llm.model_info.get("pricing", {})
            if "prompt" in pricing and "completion" in pricing:
                prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
                completion_cost = (completion_tokens / 1000) * pricing["completion"]
                return prompt_cost + completion_cost

        # Fallback to LLM's estimate_cost method if available
        if hasattr(self._llm, "estimate_cost"):
            return self._llm.estimate_cost(prompt_tokens, completion_tokens)

        # No pricing information available
        return None

    def get_llm(self) -> Any:
        """
        Get the created LLM instance

        Returns:
            The LLM instance

        Raises:
            RuntimeError: If LLM is not initialized
        """
        if not self._llm:
            raise RuntimeError("LLM not initialized. Call create_llm() first.")
        return self._llm
