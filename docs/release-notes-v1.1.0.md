# Browser Copilot v1.1.0 Release Notes

Release Date: July 30, 2025

## 🎉 Overview

Browser Copilot v1.1.0 introduces Human-in-the-Loop (HIL) capabilities, making browser automation more intelligent and interactive. The AI can now ask for clarification when needed and provide smart responses based on context.

## ✨ Major Features

### 🤝 Human-in-the-Loop (HIL)

Browser Copilot now includes intelligent HIL capabilities:

- **Smart by Default**: HIL is enabled by default, providing intelligent responses when the AI needs clarification
- **Interactive Mode**: Use `--hil-interactive` for real human input during test development
- **Flexible Control**: Use `--no-hil` for fully autonomous execution
- **Safety Features**: Built-in exit commands and 50-interaction limit
- **Context-Aware**: Uses the same LLM as your main agent for consistency

### 🪟 Windows Compatibility

Full cross-platform support with comprehensive Windows fixes:

- All file operations now use UTF-8 encoding
- Proper resource cleanup and file handle management
- Compatible with Windows default encoding (cp1252)

### 🏗️ Architecture Improvements

- **Component Architecture**: Modular design with dedicated components
  - LLMManager for LLM lifecycle management
  - BrowserConfigBuilder for browser configuration
  - PromptBuilder with token optimization
  - TestExecutor for async test execution
- **Better Resource Management**: VerboseLogger now properly closes file handles
- **Enhanced Error Handling**: More informative error messages

## 📝 Usage Examples

### Basic HIL Usage (Default)
```bash
# HIL is enabled by default
browser-copilot test.md
```

### Interactive Mode
```bash
# Get prompted for real input when needed
browser-copilot test.md --hil-interactive
```

### Autonomous Mode
```bash
# Disable HIL for fully autonomous execution
browser-copilot test.md --no-hil
```

## 🐛 Bug Fixes

- Fixed Windows file encoding issues (cp1252 vs UTF-8)
- Fixed resource cleanup on test completion
- Fixed VerboseLogger file handle management
- Fixed test file encoding in all test suites

## 📚 Documentation Updates

- Added comprehensive HIL documentation
- Updated all specifications to reflect current implementation
- Added Browser Copilot Studio vision document
- Enhanced README with HIL features and examples

## 🔄 Migration Guide

### From v1.0.x to v1.1.0

1. **HIL is now enabled by default**
   - If you prefer the old behavior, use `--no-hil`
   - No other changes required for existing tests

2. **Windows Users**
   - File encoding issues have been resolved
   - No manual intervention needed

## 🙏 Acknowledgments

Thanks to all contributors who helped make this release possible, especially those who tested the HIL features and reported Windows compatibility issues.

## 📦 Installation

```bash
# Upgrade from PyPI
pip install --upgrade browser-copilot

# Or with uv
uv pip install --upgrade browser-copilot
```

## 🔗 Links

- [GitHub Repository](https://github.com/smiao-icims/browser-copilot)
- [PyPI Package](https://pypi.org/project/browser-copilot/)
- [Documentation](https://github.com/smiao-icims/browser-copilot#readme)
- [Issue Tracker](https://github.com/smiao-icims/browser-copilot/issues)