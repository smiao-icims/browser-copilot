"""Authentication step for the configuration wizard."""

import os

import questionary

from browser_copilot.wizard.base import WizardStep
from browser_copilot.wizard.state import WizardState
from browser_copilot.wizard.styles import BROWSER_PILOT_STYLE
from browser_copilot.wizard.types import StepResult, WizardAction


class AuthenticationStep(WizardStep):
    """Handle authentication for providers that require it."""

    # Providers that need API keys
    API_KEY_PROVIDERS: dict[str, dict[str, str | None]] = {
        "openai": {
            "env_var": "OPENAI_API_KEY",
            "url": "https://platform.openai.com/api-keys",
            "prefix": "sk-",
        },
        "anthropic": {
            "env_var": "ANTHROPIC_API_KEY",
            "url": "https://console.anthropic.com/settings/keys",
            "prefix": "sk-ant-",
        },
        "google": {
            "env_var": "GOOGLE_API_KEY",
            "url": "https://makersuite.google.com/app/apikey",
            "prefix": "AI",
        },
        "azure": {
            "env_var": "AZURE_OPENAI_KEY",
            "url": "https://portal.azure.com/",
            "prefix": None,
        },
    }

    async def execute(self, state: WizardState) -> StepResult:
        """Execute authentication step."""
        if not state.provider:
            return StepResult(action=WizardAction.BACK, data={})

        # GitHub Copilot uses device flow
        if state.provider == "github_copilot":
            return await self._handle_github_copilot_auth(state)

        # Local models don't need authentication
        if state.provider == "local":
            return StepResult(action=WizardAction.CONTINUE, data={})

        # Check if provider needs API key
        if state.provider in self.API_KEY_PROVIDERS:
            return await self._handle_api_key_auth(state)

        # Unknown provider, skip authentication
        return StepResult(action=WizardAction.CONTINUE, data={})

    async def _handle_github_copilot_auth(self, state: WizardState) -> StepResult:
        """Handle GitHub Copilot device flow authentication."""
        print("\n🔐 GitHub Copilot Authentication\n")

        try:
            from modelforge.registry import ModelForgeRegistry

            # Check if already authenticated
            registry = ModelForgeRegistry()
            if registry.is_provider_configured("github_copilot"):
                # Check if we can use the existing auth
                try:
                    from modelforge import config as mf_config

                    current_config, _ = mf_config.get_config()
                    provider_data = current_config.get("providers", {}).get(
                        "github_copilot", {}
                    )
                    auth_data = provider_data.get("auth_data", {})

                    if auth_data.get("access_token"):
                        choices = [
                            "Use existing authentication",
                            "Re-authenticate (get new token)",
                            "Cancel",
                        ]

                        action = await questionary.select(
                            "Found existing GitHub Copilot authentication. What would you like to do?",
                            choices=choices,
                            default="Use existing authentication",
                            use_shortcuts=True,
                            use_arrow_keys=True,
                            style=BROWSER_PILOT_STYLE,
                        ).unsafe_ask_async()

                        if action == "Use existing authentication":
                            return StepResult(
                                action=WizardAction.CONTINUE,
                                data={"github_token": auth_data["access_token"]},
                            )
                        elif action == "Cancel":
                            return StepResult(action=WizardAction.BACK, data={})
                        # If "Re-authenticate", fall through to perform new authentication
                except Exception:
                    pass

            # Perform new authentication using ModelForge's device flow
            print("\nStarting GitHub Copilot device flow authentication...")
            print("This will provide you with a code to enter on GitHub.\n")

            # Use subprocess to run modelforge auth command
            import subprocess

            # Run the auth command with --force flag if re-authenticating
            # Note: ModelForge auth command will handle the device flow interactively
            auth_command = [
                "uv",
                "run",
                "modelforge",
                "auth",
                "login",
                "--provider",
                "github_copilot",
            ]

            # Add --force flag if we're re-authenticating (user chose to re-authenticate)
            if registry.is_provider_configured("github_copilot"):
                auth_command.append("--force")

            result = subprocess.run(
                auth_command,
                capture_output=False,  # Let it show output directly
                text=True,
            )

            if result.returncode == 0:
                # Authentication succeeded - token is saved in ModelForge config
                print("\n✅ Authentication successful!")
                return StepResult(
                    action=WizardAction.CONTINUE,
                    data={},  # Token is saved in ModelForge config
                )
            else:
                # Authentication failed
                print("\n❌ Authentication failed")
                return await self._handle_auth_failure("github_copilot")

        except Exception as e:
            # Fallback to manual instructions if something goes wrong
            print(f"⚠️  Could not start automatic authentication: {e}")
            print("\nYou can authenticate manually:")
            print("1. Run: uv run modelforge auth github_copilot")
            print("2. Follow the device flow instructions")
            print("3. Return here when complete\n")

            await questionary.press_any_key_to_continue(
                "Press any key to continue...", style=BROWSER_PILOT_STYLE
            ).unsafe_ask_async()

            return StepResult(action=WizardAction.CONTINUE, data={})

    async def _handle_api_key_auth(self, state: WizardState) -> StepResult:
        """Handle API key authentication."""
        if state.provider is None:
            return StepResult(action=WizardAction.BACK, data={})
        provider_info = self.API_KEY_PROVIDERS[state.provider]
        env_var = str(provider_info["env_var"])

        print(f"\n🔑 {state.provider.title()} API Key\n")

        # Check for existing API key
        existing_key = os.environ.get(env_var)
        if existing_key:
            use_existing = await questionary.confirm(
                f"Found {env_var} in environment. Use it?",
                default=True,
                style=BROWSER_PILOT_STYLE,
            ).unsafe_ask_async()

            if use_existing:
                return StepResult(
                    action=WizardAction.CONTINUE, data={"api_key": existing_key}
                )

        # Ask for API key
        print(f"Get your API key from: {str(provider_info['url'])}")
        print(f"Set as environment variable: export {env_var}='your-key'\n")

        api_key = await questionary.password(
            "Enter API key (or press Enter to set later):", style=BROWSER_PILOT_STYLE
        ).unsafe_ask_async()

        if api_key is None:
            return StepResult(action=WizardAction.BACK, data={})

        if not api_key:
            # User wants to set later
            skip_validation = await questionary.confirm(
                "Skip validation? You'll need to set the API key before using Browser Copilot.",
                default=False,
                style=BROWSER_PILOT_STYLE,
            ).unsafe_ask_async()

            if skip_validation:
                return StepResult(action=WizardAction.CONTINUE, data={})
            else:
                return StepResult(action=WizardAction.BACK, data={})

        # Basic validation
        prefix = provider_info["prefix"]
        if prefix and not api_key.startswith(str(prefix)):
            print(
                f"\n⚠️  Warning: API key doesn't start with expected prefix '{prefix}'"
            )
            proceed = await questionary.confirm(
                "Proceed anyway?", default=False, style=BROWSER_PILOT_STYLE
            ).unsafe_ask_async()

            if not proceed:
                return StepResult(action=WizardAction.RETRY, data={})

        return StepResult(action=WizardAction.CONTINUE, data={"api_key": api_key})

    async def _handle_auth_failure(self, provider: str) -> StepResult:
        """Handle authentication failure."""
        choices = [
            "Retry authentication",
            "Choose different provider",
            "Skip validation (not recommended)",
            "Exit wizard",
        ]

        action = await questionary.select(
            "What would you like to do?",
            choices=choices,
            use_shortcuts=True,
            use_arrow_keys=True,
            style=BROWSER_PILOT_STYLE,
        ).unsafe_ask_async()

        if action == "Retry authentication":
            return StepResult(action=WizardAction.RETRY, data={})
        elif action == "Choose different provider":
            return StepResult(action=WizardAction.BACK, data={})
        elif action == "Skip validation (not recommended)":
            return StepResult(action=WizardAction.CONTINUE, data={})
        else:
            return StepResult(action=WizardAction.CANCEL, data={})

    def can_skip(self, state: WizardState) -> bool:
        """Can skip if provider doesn't need authentication."""
        return state.provider not in ["github_copilot"] + list(
            self.API_KEY_PROVIDERS.keys()
        )
