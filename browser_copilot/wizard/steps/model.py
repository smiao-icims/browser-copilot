"""Model selection step for the configuration wizard."""

from typing import Any

import questionary
from questionary import Choice

from browser_copilot.wizard.base import WizardStep
from browser_copilot.wizard.state import WizardState
from browser_copilot.wizard.styles import BROWSER_PILOT_STYLE
from browser_copilot.wizard.types import StepResult, WizardAction


class ModelSelectionStep(WizardStep):
    """Handle model selection based on chosen provider."""

    # Default models for each provider
    PROVIDER_MODELS = {
        "github_copilot": [
            {
                "name": "gpt-4o",
                "description": "Recommended - Best performance",
                "context": "128k",
            },
            {"name": "gpt-4", "description": "Previous generation", "context": "8k"},
            {
                "name": "gpt-3.5-turbo",
                "description": "Faster, lower cost",
                "context": "16k",
            },
            {
                "name": "claude-3-sonnet",
                "description": "Alternative model",
                "context": "200k",
            },
        ],
        "openai": [
            {
                "name": "gpt-4o",
                "description": "Latest and most capable",
                "context": "128k",
            },
            {
                "name": "gpt-4-turbo",
                "description": "High performance",
                "context": "128k",
            },
            {"name": "gpt-4", "description": "Stable version", "context": "8k"},
            {
                "name": "gpt-3.5-turbo",
                "description": "Fast and cost-effective",
                "context": "16k",
            },
        ],
        "anthropic": [
            {
                "name": "claude-3-opus-20240229",
                "description": "Most capable",
                "context": "200k",
            },
            {
                "name": "claude-3-sonnet-20240229",
                "description": "Balanced performance",
                "context": "200k",
            },
            {
                "name": "claude-3-haiku-20240307",
                "description": "Fast and efficient",
                "context": "200k",
            },
        ],
        "google": [
            {
                "name": "gemini-1.5-pro",
                "description": "Latest Gemini model",
                "context": "1M",
            },
            {
                "name": "gemini-1.5-flash",
                "description": "Fast variant",
                "context": "1M",
            },
            {
                "name": "gemini-pro",
                "description": "Previous generation",
                "context": "32k",
            },
        ],
        "azure": [
            {"name": "gpt-4", "description": "GPT-4 on Azure", "context": "8k"},
            {
                "name": "gpt-35-turbo",
                "description": "GPT-3.5 on Azure",
                "context": "16k",
            },
        ],
        "local": [
            {"name": "llama3:latest", "description": "Meta Llama 3", "context": "8k"},
            {"name": "mistral:latest", "description": "Mistral 7B", "context": "32k"},
            {"name": "codellama:latest", "description": "Code Llama", "context": "16k"},
        ],
    }

    async def execute(self, state: WizardState) -> StepResult:
        """Execute model selection."""
        if not state.provider:
            return StepResult(
                action=WizardAction.BACK, data={}, error="No provider selected"
            )

        print(f"\n🤖 Select Model for {state.provider}\n")

        try:
            # Try to get models from ModelForge
            models = await self._get_models_from_modelforge(state.provider)
        except Exception as e:
            print(f"⚠️  Using default model list: {e}")
            models = self._get_fallback_models(state.provider)

        if not models:
            # Manual entry if no models available
            model_name = await questionary.text(
                f"No models found for {state.provider}. Enter model name:",
                style=BROWSER_PILOT_STYLE,
            ).unsafe_ask_async()

            if model_name is None:
                return StepResult(action=WizardAction.BACK, data={})

            return StepResult(action=WizardAction.CONTINUE, data={"model": model_name})

        # Create choices with descriptions
        choices = []
        for model in models:
            label = f"{model['name']:<25}"

            # Add status indicators
            if model.get("is_current", False):
                label += " ★"  # Star for current model
            elif model.get("configured", False):
                label += " ✓"  # Check for configured model
            else:
                label += "  "  # Spaces for alignment

            if model.get("description"):
                label += f" ({model['description']}"
                if model.get("context"):
                    label += f", {model['context']} context"
                label += ")"
            choices.append(Choice(title=label, value=model["name"]))

        # Show selection prompt
        # Default to the first choice (which should be a configured model if any exist)
        default_choice = choices[0].value if choices else None

        selected = await questionary.select(
            f"Select model for {state.provider}:",
            choices=choices,
            default=default_choice,
            use_shortcuts=True,
            use_arrow_keys=True,
            style=BROWSER_PILOT_STYLE,
        ).unsafe_ask_async()

        if selected is None:
            return StepResult(action=WizardAction.BACK, data={})

        return StepResult(action=WizardAction.CONTINUE, data={"model": selected})

    async def _get_models_from_modelforge(self, provider: str) -> list[dict[str, Any]]:
        """Get available models from ModelForge using v2.2.2+ APIs."""
        try:
            from modelforge import config as mf_config
            from modelforge.registry import ModelForgeRegistry

            registry = ModelForgeRegistry()
            models = []

            # Get the current model to prioritize it
            current_model_info = mf_config.get_current_model()
            current_model_name = None
            if current_model_info and current_model_info.get("provider") == provider:
                current_model_name = current_model_info.get("model")

            # Normalize provider name for models.dev API
            # ModelForge uses underscores, models.dev uses hyphens
            api_provider = provider.replace("_", "-")

            # Get all available models for this provider
            available_models = registry.get_available_models(provider=api_provider)

            # Get configured models for comparison
            configured_models: dict[str, object] = {}
            if registry.is_provider_configured(provider):
                configured_models = registry.get_configured_models(provider) or {}

            # Build model list
            for model_info in available_models:
                # ModelForge v2.2.2 uses 'id' field for model name
                name = model_info.get("id", model_info.get("name", ""))
                if not name:
                    continue

                # Extract useful information
                context_length = model_info.get("context_length", 0)
                context_str = f"{context_length:,}" if context_length else "Unknown"

                # Build description
                description_parts = []
                if model_info.get("display_name"):
                    description_parts.append(model_info["display_name"])
                if model_info.get("description"):
                    description_parts.append(model_info["description"])

                # Check if configured
                is_configured = name in configured_models

                models.append(
                    {
                        "name": name,
                        "description": " - ".join(description_parts)
                        if description_parts
                        else "",
                        "context": context_str,
                        "configured": is_configured,
                        "is_current": name == current_model_name,
                        "supports_vision": model_info.get("supports_vision", False),
                        "supports_function_calling": model_info.get(
                            "supports_function_calling", False
                        ),
                    }
                )

            # If no models found, use fallback
            if not models:
                print(f"⚠️  No models found for {provider}, using defaults")
                return self._get_fallback_models(provider)

            # Sort to put current model first, then configured models, then others
            models.sort(
                key=lambda m: (
                    not m.get("is_current", False),  # Current model first
                    not m.get("configured", False),  # Then configured models
                    m["name"],  # Then alphabetically
                )
            )

            return models

        except AttributeError:
            # ModelForge doesn't have the new APIs yet
            print("⚠️  ModelForge v2.2.2+ required for model discovery")
            return self._get_fallback_models(provider)
        except Exception as e:
            print(f"⚠️  ModelForge model lookup error: {e}")
            return self._get_fallback_models(provider)

    def _get_fallback_models(self, provider: str) -> list[dict[str, Any]]:
        """Get fallback list of models for provider."""
        return self.PROVIDER_MODELS.get(provider, [])

    def can_skip(self, state: WizardState) -> bool:
        """Model selection cannot be skipped if provider is selected."""
        return state.provider is None
