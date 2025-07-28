"""
Pytest configuration and fixtures for Browser Copilot tests
"""

import os
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_storage_dir(temp_dir: Path) -> Path:
    """Create a mock storage directory structure"""
    storage_dir = temp_dir / "browser_copilot"
    for subdir in ["logs", "settings", "reports", "screenshots", "cache", "memory"]:
        (storage_dir / subdir).mkdir(parents=True, exist_ok=True)
    return storage_dir


@pytest.fixture
def sample_test_suite() -> str:
    """Sample test suite content"""
    return """# Login Test

1. Navigate to https://example.com/login
2. Click on the email input field
3. Type "user@example.com"
4. Click on the password field
5. Type "password123"
6. Click the "Login" button
7. Verify that the page contains "Dashboard"
8. Take a screenshot
"""


@pytest.fixture
def sample_config() -> dict:
    """Sample configuration dictionary"""
    return {
        "provider": "openai",
        "model": "gpt-4",
        "browser": "chromium",
        "headless": False,
        "verbose": True,
        "output_format": "json",
        "token_optimization": True,
        "compression_level": "medium",
    }


@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content="Mocked LLM response")
    mock.ainvoke.return_value = MagicMock(content="Mocked async LLM response")
    return mock


@pytest.fixture
def mock_telemetry():
    """Mock telemetry callback"""
    mock = Mock()
    mock.metrics = Mock()
    mock.metrics.token_usage = Mock(
        total_tokens=1000, prompt_tokens=800, completion_tokens=200
    )
    mock.metrics.estimated_cost = 0.02
    return mock


@pytest.fixture
def sample_test_result() -> dict:
    """Sample test execution result"""
    return {
        "success": True,
        "provider": "openai",
        "model": "gpt-4",
        "browser": "chromium",
        "headless": False,
        "duration_seconds": 15.5,
        "steps_executed": 8,
        "report": "# Test Execution Report\n\n## Summary\n- Overall Status: PASSED",
        "token_usage": {
            "total_tokens": 1000,
            "prompt_tokens": 800,
            "completion_tokens": 200,
            "estimated_cost": 0.02,
        },
        "timestamp": "2025-01-26T12:00:00",
        "error": None,
    }


@pytest.fixture(autouse=True)
def cleanup_env():
    """Clean up environment variables after each test"""
    # Store original env vars
    original_env = dict(os.environ)

    yield

    # Restore original env vars
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_langchain_imports(monkeypatch):
    """Mock langchain imports for tests that don't need real LangChain"""
    # Create mock modules
    mock_langchain = MagicMock()
    mock_langchain.schema = MagicMock()
    mock_langchain.schema.BaseMessage = Mock
    mock_langchain.schema.HumanMessage = Mock
    mock_langchain.schema.SystemMessage = Mock

    # Patch the imports
    monkeypatch.setitem(sys.modules, "langchain", mock_langchain)
    monkeypatch.setitem(sys.modules, "langchain.schema", mock_langchain.schema)

    return mock_langchain


# Test markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line(
        "markers", "requires_llm: mark test as requiring an LLM provider"
    )
    config.addinivalue_line(
        "markers", "requires_browser: mark test as requiring browser automation"
    )
