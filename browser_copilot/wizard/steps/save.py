"""Save configuration step for the wizard."""

import json
import os
import shutil
from pathlib import Path

import questionary

from browser_copilot.storage_manager import StorageManager
from browser_copilot.wizard.base import WizardStep
from browser_copilot.wizard.state import WizardState
from browser_copilot.wizard.styles import BROWSER_PILOT_STYLE
from browser_copilot.wizard.types import StepResult, WizardAction


class SaveConfigurationStep(WizardStep):
    """Save the configuration to disk."""

    async def execute(self, state: WizardState) -> StepResult:
        """Execute configuration save."""
        print("\n💾 Save Configuration\n")

        # Show configuration summary
        print("Configuration Summary:")
        print("━" * 50)
        print(f"Provider:        {state.provider}")
        print(f"Model:           {state.model}")
        print(f"Browser:         {state.browser}")
        print(f"Mode:            {'headless' if state.headless else 'headed'}")
        print(f"Optimization:    {state.compression_level}")
        print(f"Viewport:        {state.viewport_width}x{state.viewport_height}")
        print("━" * 50)
        print()

        # Ask for confirmation
        save_config = await questionary.confirm(
            "Save this configuration?", default=True, style=BROWSER_PILOT_STYLE
        ).unsafe_ask_async()

        if not save_config:
            choices = [
                "Go back and modify",
                "Exit without saving",
            ]

            action = await questionary.select(
                "What would you like to do?",
                choices=choices,
                use_shortcuts=True,
                use_arrow_keys=True,
                style=BROWSER_PILOT_STYLE,
            ).unsafe_ask_async()

            if action == "Go back and modify":
                return StepResult(action=WizardAction.BACK, data={})
            else:
                return StepResult(action=WizardAction.CANCEL, data={})

        # Save configuration
        try:
            config_path = self._save_configuration(state)
            print(f"\n✅ Configuration saved to: {config_path}")

            # Also save to ModelForge if applicable
            if state.provider and state.model:
                self._save_to_modelforge(state)

            return StepResult(action=WizardAction.CONTINUE, data={})

        except Exception as e:
            print(f"\n❌ Failed to save configuration: {e}")

            retry = await questionary.confirm(
                "Try again?", default=True, style=BROWSER_PILOT_STYLE
            ).unsafe_ask_async()

            if retry:
                return StepResult(action=WizardAction.RETRY, data={})
            else:
                return StepResult(action=WizardAction.CANCEL, data={})

    def _save_configuration(self, state: WizardState) -> Path:
        """Save configuration to disk."""
        # Get storage manager
        storage = StorageManager()
        config_dir = storage.get_settings_dir()
        config_path = config_dir / "config.json"

        # Backup existing config if it exists
        if config_path.exists():
            backup_path = config_path.with_suffix(".backup")
            shutil.copy(config_path, backup_path)
            print(f"📋 Backed up existing config to: {backup_path}")

        # Convert state to config format
        config = state.to_config()

        # Write configuration
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        # Set appropriate permissions (read/write for owner only)
        os.chmod(config_path, 0o600)

        return config_path

    def _save_to_modelforge(self, state: WizardState) -> None:
        """Save provider configuration to ModelForge."""
        try:
            import subprocess

            # Check if provider needs configuration
            from modelforge.registry import ModelForgeRegistry

            registry = ModelForgeRegistry()

            # Skip if already configured
            if registry.is_model_configured(state.provider, state.model):
                print("✅ ModelForge already has this provider/model configured")
                return

            # Build modelforge command
            if not state.provider or not state.model:
                return

            cmd: list[str] = [
                "uv",
                "run",
                "modelforge",
                "config",
                "add",
                "--provider",
                state.provider,
                "--model",
                state.model,
            ]

            if state.api_key:
                cmd.extend(["--api-key", state.api_key])

            # Run command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                print("✅ Also saved to ModelForge configuration")

                # Set as default
                # We know provider and model are not None from the check above
                assert state.provider is not None
                assert state.model is not None
                subprocess.run(
                    [
                        "uv",
                        "run",
                        "modelforge",
                        "config",
                        "set-default",
                        "--provider",
                        state.provider,
                        "--model",
                        state.model,
                    ],
                    capture_output=True,
                    timeout=5,
                )
            else:
                print(f"⚠️  Could not save to ModelForge: {result.stderr}")

        except Exception as e:
            print(f"⚠️  ModelForge save optional - skipped: {e}")

    def can_skip(self, state: WizardState) -> bool:
        """Save step cannot be skipped."""
        return False
