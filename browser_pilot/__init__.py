"""
Browser Pilot - AI-powered browser automation framework

A streamlined approach to browser test automation using natural language
test scenarios executed by AI agents.
"""

__version__ = "2.1.0"
__author__ = "Browser Pilot Team"

from .cli import main as cli_main
from .core import BrowserPilot

__all__ = ["BrowserPilot", "cli_main"]
