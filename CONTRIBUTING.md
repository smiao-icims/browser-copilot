# Contributing to Browser Copilot

Thank you for your interest in contributing to Browser Copilot! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing viewpoints and experiences

## How to Contribute

### Reporting Issues

1. **Check existing issues** first to avoid duplicates
2. **Use issue templates** when available
3. **Provide details**:
   - Browser Copilot version
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages/logs

### Suggesting Features

1. **Open a discussion** first for major features
2. **Explain the use case** and benefits
3. **Consider implementation** complexity
4. **Be open to feedback** and alternatives

### Contributing Code

#### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/smiao-icims/browser-copilot.git
cd browser-copilot

# Install uv (if not already installed)
# On macOS and Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or with pip:
pip install uv

# Create virtual environment and install dependencies
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install
```

#### Development Workflow

1. **Fork the repository** on GitHub
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**:
   - Write clean, documented code
   - Follow existing patterns
   - Add tests for new functionality
4. **Run tests**:
   ```bash
   uv run pytest tests/
   uv run pytest --cov=browser_copilot tests/  # With coverage
   ```
5. **Format and lint**:
   ```bash
   uv run black browser_copilot/
   uv run isort browser_copilot/
   uv run ruff check browser_copilot/
   uv run mypy browser_copilot/
   ```
6. **Commit changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```
7. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Messages

Follow conventional commits format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `style:` Code style changes
- `chore:` Build/tooling changes

Examples:
```
feat: add support for webkit browser
fix: handle timeout in page navigation
docs: update test writing guide
test: add login flow test cases
```

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **Line length**: 88 characters (Black default)
- **Imports**: Use isort for organization
- **Type hints**: Required for all public functions
- **Docstrings**: Google style for all public APIs

Example:
```python
from typing import Dict, Any, Optional

def process_results(
    data: Dict[str, Any], 
    timeout: Optional[float] = None
) -> Dict[str, Any]:
    """
    Process test execution results.
    
    Args:
        data: Raw test result data
        timeout: Optional timeout in seconds
        
    Returns:
        Processed results dictionary
        
    Raises:
        ValueError: If data is invalid
    """
    # Implementation
    pass
```

### Testing Guidelines

1. **Write tests first** (TDD approach)
2. **Test categories**:
   - Unit tests: `tests/unit/`
   - Integration tests: `tests/integration/`
   - E2E tests: `tests/e2e/`
3. **Test naming**: `test_<function>_<scenario>`
4. **Use fixtures** for common setup
5. **Mock external dependencies**

Example test:
```python
import pytest
from browser_copilot.core import BrowserPilot

@pytest.fixture
def pilot():
    """Create a test pilot instance."""
    return BrowserPilot("mock_provider", "mock_model")

def test_pilot_initialization(pilot):
    """Test pilot initializes with correct attributes."""
    assert pilot.provider == "mock_provider"
    assert pilot.model == "mock_model"
    assert pilot.telemetry is not None
```

### Documentation

1. **Update relevant docs** with code changes
2. **Add docstrings** to new functions/classes
3. **Include examples** in documentation
4. **Update README** if needed
5. **Add to changelog** for notable changes

### Pull Request Process

1. **Fill out PR template** completely
2. **Link related issues** using keywords
3. **Ensure CI passes** all checks
4. **Request review** from maintainers
5. **Address feedback** promptly
6. **Keep PR focused** on one feature/fix

#### PR Checklist

- [ ] Tests pass locally
- [ ] Code is formatted and linted
- [ ] Documentation is updated
- [ ] Changelog entry added (if applicable)
- [ ] PR description is clear
- [ ] Related issues are linked

### Release Process

Maintainers handle releases:

1. Update version in `__init__.py` and `pyproject.toml`
2. Update CHANGELOG.md
3. Create release PR
4. Tag release after merge
5. GitHub Actions publishes to PyPI

## Development Tips

### Running Specific Tests

```bash
# Run single test file
uv run pytest tests/unit/test_core.py

# Run single test
uv run pytest tests/unit/test_core.py::test_pilot_initialization

# Run with verbose output
uv run pytest -v tests/

# Run with print statements
uv run pytest -s tests/
```

### Debugging

1. Use `--verbose` flag when running browser-copilot
2. Enable Python logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```
3. Use debugger:
   ```python
   import pdb; pdb.set_trace()
   ```

### Performance Considerations

- Minimize token usage in prompts
- Cache MCP tool connections
- Use efficient selectors in tests
- Profile code for bottlenecks

### Windows Compatibility

Since development is primarily done on macOS/Linux, pay special attention to Windows compatibility:

#### Common Windows Issues and Solutions

1. **File Lock Errors**: Windows doesn't allow deleting files that are open
   - Always close file handlers, especially in tests
   - Use try/finally blocks to ensure cleanup
   - Add `.close()` methods to classes that open files
   - Example: VerboseLogger needs explicit close() to release log files

2. **Unicode Encoding**: Windows defaults to cp1252, not UTF-8
   - Always specify `encoding="utf-8"` for file operations
   - Use `Path.write_text(data, encoding="utf-8")`
   - Use `open(file, "w", encoding="utf-8")`
   - For JSON: `json.dump(..., ensure_ascii=False)`

3. **Path Separators**: Windows uses backslashes
   - Always use `pathlib.Path` instead of string concatenation
   - Use forward slashes in Path() constructors - they work on all platforms

#### Testing on macOS/Linux for Windows Compatibility

While you can't fully simulate Windows, you can:

1. **Use CI/CD**: Push changes and monitor Windows CI builds on GitHub Actions
2. **Write defensive code**: 
   - Always specify encoding explicitly
   - Always close resources properly
   - Use pathlib for all path operations
3. **Common patterns to avoid**:
   - Don't assume UTF-8 is default
   - Don't leave files open
   - Don't use os.path.join() - use pathlib
   - Don't hardcode path separators

#### Windows Compatibility Checklist

Before committing, check:
- [ ] All file operations specify `encoding="utf-8"`
- [ ] All file handles are properly closed (especially in tests)
- [ ] All paths use pathlib.Path
- [ ] No hardcoded forward/backward slashes in paths
- [ ] Tests use try/finally or context managers for cleanup

## Getting Help

- **Discord**: Join our community server
- **GitHub Discussions**: Ask questions
- **Issues**: Report bugs
- **Email**: maintainers@example.com

## Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- Project website

Thank you for contributing to Browser Copilot! 🚀