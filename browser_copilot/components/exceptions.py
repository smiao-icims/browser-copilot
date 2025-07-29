"""
Exception hierarchy for Browser Copilot components
"""


class BrowserPilotError(Exception):
    """Base exception for Browser Pilot"""

    pass


class ConfigurationError(BrowserPilotError):
    """Configuration-related errors"""

    pass


class BrowserSetupError(BrowserPilotError):
    """Browser setup failures"""

    pass


class ExecutionError(BrowserPilotError):
    """Test execution failures"""

    pass


class AnalysisError(BrowserPilotError):
    """Result analysis failures"""

    pass
