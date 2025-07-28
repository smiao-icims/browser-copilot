"""Provider selection step for the configuration wizard."""

from typing import Any

import questionary
from questionary import Choice

from browser_copilot.wizard.base import WizardStep
from browser_copilot.wizard.state import WizardState
from browser_copilot.wizard.styles import BROWSER_PILOT_STYLE
from browser_copilot.wizard.types import StepResult, WizardAction


class ProviderSelectionStep(WizardStep):
    """Handle LLM provider selection with GitHub Copilot prioritized."""

    async def execute(self, state: WizardState) -> StepResult:
        """Execute provider selection."""
        print("\n📋 Select LLM Provider\n")

        try:
            # Try to get providers from ModelForge
            providers = await self._get_providers_from_modelforge()
        except Exception as e:
            print(f"⚠️  Could not load providers from ModelForge: {e}")
            providers = self._get_fallback_providers()

        # Sort providers with GitHub Copilot first
        sorted_providers = self._sort_providers(providers)

        # Create choices for Questionary
        choices = []
        for provider in sorted_providers:
            label = f"{provider['name']:<20}"

            # Add status indicators
            status_parts = []
            if provider.get("configured", False):
                status_parts.append("✓ Configured")

            if provider["name"] == "github_copilot":
                status_parts.append("Recommended - Uses device auth")
            elif provider.get("requires_api_key", True):
                status_parts.append("Requires API key")

            if status_parts:
                label += f" ({', '.join(status_parts)})"

            choices.append(Choice(title=label, value=provider["name"]))

        # Ensure we have choices
        if not choices:
            print("⚠️  No providers found. Using default list.")
            providers = self._get_fallback_providers()
            sorted_providers = self._sort_providers(providers)

            # Recreate choices
            for provider in sorted_providers:
                label = f"{provider['name']:<20}"
                if provider["name"] == "github_copilot":
                    label += " (Recommended - Uses device auth)"
                elif provider.get("requires_api_key", True):
                    label += " (Requires API key)"
                choices.append(Choice(title=label, value=provider["name"]))

        # Show selection prompt
        selected = await questionary.select(
            "Select your LLM provider:",
            choices=choices,
            use_shortcuts=True,
            use_arrow_keys=True,
            style=BROWSER_PILOT_STYLE,
        ).unsafe_ask_async()

        if selected is None:
            return StepResult(action=WizardAction.CANCEL, data={})

        return StepResult(action=WizardAction.CONTINUE, data={"provider": selected})

    async def _get_providers_from_modelforge(self) -> list[dict[str, Any]]:
        """Get available providers from ModelForge using v2.2.2+ APIs."""
        try:
            from modelforge.registry import ModelForgeRegistry

            registry = ModelForgeRegistry()
            providers = []

            # Get all available providers from models.dev
            available_providers = registry.get_available_providers()

            # Get configured providers
            configured_providers = registry.get_configured_providers()
            configured_names = set(configured_providers.keys())

            # Build provider list with configuration status
            for provider_info in available_providers:
                name = provider_info.get("name", "")

                # Skip if no name
                if not name:
                    continue

                # Determine if it's configured
                is_configured = name in configured_names

                # Determine if it requires API key
                auth_types = provider_info.get("auth_types", [])
                requires_api_key = "api_key" in auth_types

                # Normalize provider name for consistency
                # models.dev uses hyphens, ModelForge uses underscores
                normalized_name = name.replace("-", "_")

                # Check if configured using normalized name
                is_configured = normalized_name in configured_names

                providers.append(
                    {
                        "name": normalized_name,  # Use normalized name
                        "display_name": provider_info.get("display_name", name),
                        "description": provider_info.get("description", ""),
                        "requires_api_key": requires_api_key,
                        "configured": is_configured,
                        "auth_types": auth_types,
                    }
                )

            # If no providers found, use fallback
            if not providers:
                print("⚠️  No providers found from models.dev, using defaults")
                return self._get_fallback_providers()

            return providers

        except AttributeError:
            # ModelForge doesn't have the new APIs yet
            print("⚠️  ModelForge v2.2.2+ required for provider discovery")
            return self._get_fallback_providers()
        except Exception as e:
            print(f"⚠️  ModelForge integration error: {e}")
            # Fall back to static list
            return self._get_fallback_providers()

    def _get_fallback_providers(self) -> list[dict[str, Any]]:
        """Get fallback list of providers if ModelForge is unavailable."""
        return [
            {
                "name": "github_copilot",
                "display_name": "GitHub Copilot",
                "requires_api_key": False,
            },
            {"name": "openai", "display_name": "OpenAI", "requires_api_key": True},
            {
                "name": "anthropic",
                "display_name": "Anthropic",
                "requires_api_key": True,
            },
            {"name": "google", "display_name": "Google", "requires_api_key": True},
            {"name": "azure", "display_name": "Azure OpenAI", "requires_api_key": True},
            {"name": "local", "display_name": "Local Model", "requires_api_key": False},
        ]

    def _sort_providers(self, providers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sort providers with GitHub Copilot first."""
        github_copilot = None
        other_providers = []

        for provider in providers:
            if provider["name"] == "github_copilot":
                github_copilot = provider
            else:
                other_providers.append(provider)

        # Sort others alphabetically
        other_providers.sort(key=lambda p: p["name"])

        # Put GitHub Copilot first
        if github_copilot:
            return [github_copilot] + other_providers
        return other_providers

    def can_skip(self, state: WizardState) -> bool:
        """Provider selection cannot be skipped."""
        return False
