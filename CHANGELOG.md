# Changelog

All notable changes to Browser Copilot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-01-26

### Added

#### Core Features
- **Enhanced Verbose Mode** - Step-by-step debugging with dual console/file output to `~/.browser_copilot/logs/`
- **Token Optimization Module** - Reduces token usage by 20-30% with configurable compression levels
- **Flexible Input/Output** - Support for stdin input and multiple output formats (JSON, YAML, XML, JUnit, HTML, Markdown)
- **System Prompt Customization** - Use custom prompts to control agent behavior
- **Smart Configuration** - Layered config system with CLI > ENV > file > defaults priority
- **Local Storage Management** - Cross-platform storage in appropriate OS directories
- **Test Suite Enhancement** - AI-powered test improvement suggestions
- **Browser Validation** - Support for Chrome, Safari, Edge with proper validation

#### New CLI Arguments
- Positional `test_scenario` - Can be file path or `-` for stdin
- `--output-format` - Choose output format
- `--output-file` - Save to file instead of console
- `--system-prompt` - Custom system prompt file
- `--verbose/-v` - Enhanced verbose mode
- `--quiet/-q` - Suppress non-error output
- `--no-screenshots` - Disable screenshot capture
- `--no-token-optimization` - Disable optimization
- `--config` - Use custom config file
- `--save-config` - Save settings as defaults
- `--viewport-width/height` - Separate viewport controls

#### Technical Improvements
- **ConfigManager** - Centralized configuration with validation
- **StorageManager** - Platform-aware local storage handling
- **VerboseLogger** - Structured logging with LangChain callbacks
- **TokenOptimizer** - Multi-level prompt optimization
- **Enhanced Reports** - Added timing metrics, token optimization stats, and cost analysis
- **Browser Aliases** - Map chrome->chromium, edge->chromium, safari->webkit

### Changed
- Minimum Python version is now 3.11+ (required by ModelForge)
- Default package manager is now `uv` instead of pip
- Provider and model are now optional (uses ModelForge defaults)
- Reports now include comprehensive metrics and optimization data
- Viewport size split into separate width/height arguments

### Fixed
- Proper browser validation before test execution
- Token usage tracking with error handling
- Cross-platform path handling in storage manager
- Import compatibility issues with standalone modules

## [2.0.0] - 2025-01-20

### Added
- Single agent architecture for improved efficiency
- ModelForge integration for LLM provider management  
- Markdown-based test format
- Basic token usage tracking
- Multi-browser support (Chromium, Firefox, WebKit)

### Changed
- Complete rewrite from multi-agent to single-agent design
- Simplified test format using numbered steps
- Streamlined CLI interface

### Removed
- Complex multi-agent orchestration
- YAML-based test definitions
- Legacy provider integrations

## [1.0.0] - 2024-12-15

### Added
- Initial release with multi-agent architecture
- Basic browser automation capabilities
- Support for OpenAI and Anthropic models
- Screenshot capture functionality