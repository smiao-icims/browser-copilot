"""Browser selection step for the configuration wizard."""

import subprocess
from typing import List, Dict, Any
import questionary
from questionary import Choice

from browser_pilot.wizard.base import WizardStep
from browser_pilot.wizard.state import WizardState
from browser_pilot.wizard.styles import BROWSER_PILOT_STYLE
from browser_pilot.wizard.types import StepResult, WizardAction


class BrowserSelectionStep(WizardStep):
    """Handle browser selection with availability detection."""
    
    BROWSERS = [
        {
            "name": "chromium",
            "display": "Chromium",
            "description": "Recommended - Best compatibility",
            "priority": 1,
        },
        {
            "name": "chrome",
            "display": "Google Chrome",
            "description": "Popular browser",
            "priority": 2,
        },
        {
            "name": "firefox",
            "display": "Mozilla Firefox",
            "description": "Privacy-focused",
            "priority": 3,
        },
        {
            "name": "webkit",
            "display": "WebKit",
            "description": "Safari engine",
            "priority": 4,
        },
        {
            "name": "edge",
            "display": "Microsoft Edge",
            "description": "Windows default",
            "priority": 5,
        },
    ]
    
    async def execute(self, state: WizardState) -> StepResult:
        """Execute browser selection."""
        print("\n🌐 Select Browser\n")
        
        # Check which browsers are installed
        installed_browsers = await self._check_installed_browsers()
        
        # Create choices
        choices = []
        for browser in self.BROWSERS:
            is_installed = browser["name"] in installed_browsers
            label = f"{browser['display']:<20}"
            
            if browser["name"] == "chromium":
                label += " (Recommended"
            else:
                label += " ("
                
            if browser.get("description"):
                label += f" - {browser['description']}"
                
            if is_installed:
                label += ", ✓ Installed)"
            else:
                label += ", ✗ Not installed)"
                
            choices.append(Choice(
                title=label,
                value=browser["name"],
                disabled=not is_installed
            ))
        
        # Add option to install browsers
        choices.append(Choice(
            title="→ Install browsers...",
            value="__install__"
        ))
        
        # Show selection prompt
        selected = await questionary.select(
            "Select your preferred browser:",
            choices=choices,
            use_shortcuts=True,
            use_arrow_keys=True,
            style=BROWSER_PILOT_STYLE
        ).unsafe_ask_async()
        
        if selected is None:
            return StepResult(action=WizardAction.BACK, data={})
        
        if selected == "__install__":
            await self._show_install_instructions()
            return StepResult(action=WizardAction.RETRY, data={})
        
        return StepResult(
            action=WizardAction.CONTINUE,
            data={"browser": selected}
        )
    
    async def _check_installed_browsers(self) -> List[str]:
        """Check which browsers are installed via Playwright."""
        installed = []
        
        try:
            # Check using playwright
            result = subprocess.run(
                ["npx", "playwright", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                for browser in self.BROWSERS:
                    if browser["name"] in output:
                        installed.append(browser["name"])
            
            # If no browsers found, check if playwright is installed
            if not installed:
                # Try to check if any browser executables exist
                for browser in self.BROWSERS:
                    try:
                        check_result = subprocess.run(
                            ["npx", "playwright", "show-trace", "--help"],
                            capture_output=True,
                            timeout=2
                        )
                        if check_result.returncode == 0:
                            # Playwright is installed, just no browsers
                            break
                    except:
                        pass
                        
        except subprocess.TimeoutExpired:
            print("⚠️  Timeout checking installed browsers")
        except FileNotFoundError:
            print("⚠️  Playwright not found. Install with: npm install -g playwright")
        except Exception as e:
            print(f"⚠️  Error checking browsers: {e}")
        
        # Default to chromium if we can't detect
        if not installed:
            installed = ["chromium"]
            
        return installed
    
    async def _show_install_instructions(self):
        """Show instructions for installing browsers."""
        print("\n📦 Installing Browsers\n")
        print("To install browsers, run one of these commands:\n")
        print("Install all browsers:")
        print("  npx playwright install")
        print()
        print("Install specific browser:")
        print("  npx playwright install chromium")
        print("  npx playwright install firefox")
        print("  npx playwright install webkit")
        print()
        print("On Linux, you may need system dependencies:")
        print("  npx playwright install-deps chromium")
        print()
        
        await questionary.press_any_key_to_continue(
            "\nPress any key to continue...",
            style=BROWSER_PILOT_STYLE
        ).unsafe_ask_async()
    
    def can_skip(self, state: WizardState) -> bool:
        """Browser selection cannot be skipped."""
        return False