# Browser Copilot Configuration Wizard Requirements

**Date**: January 28, 2025
**Version**: 1.0
**Status**: Draft

## Executive Summary

This document outlines the requirements for an interactive CLI configuration wizard that simplifies Browser Copilot setup for QA engineers. The wizard will guide users through all configuration steps with smart defaults and validation, eliminating the need for manual configuration file editing or command memorization.

## Goals

1. **Zero-to-Testing in < 2 minutes** - From fresh install to running first test
2. **No Prior Knowledge Required** - Works for users who don't know about ModelForge or LLM providers
3. **Smart Defaults** - One-key setup with sensible defaults
4. **Validation at Each Step** - Ensure configuration works before saving
5. **Seamless Integration** - Works with existing configuration system

## User Stories

### US-001: First-Time User Setup
**As a** QA engineer new to Browser Copilot
**I want** a guided setup process
**So that** I can start testing without reading documentation

**Acceptance Criteria:**
- Wizard launches automatically on first run if no config exists
- Can also be triggered with `browser-copilot --setup-wizard`
- Guides through provider selection, model choice, and browser config
- Tests configuration before saving
- Shows clear success message with next steps

### US-002: Reconfiguration
**As an** existing Browser Copilot user
**I want** to easily change my configuration
**So that** I can switch providers or update settings

**Acceptance Criteria:**
- Wizard shows current values as defaults
- Can navigate with arrow keys to change selections
- Only modified values are updated
- Backup of previous config is created

### US-003: GitHub Copilot Priority
**As a** user without API keys
**I want** GitHub Copilot suggested first
**So that** I can use Browser Copilot without additional setup

**Acceptance Criteria:**
- GitHub Copilot always appears first in provider list
- Other providers sorted alphabetically after
- Clear indication that GitHub Copilot requires no API key

## Functional Requirements

### FR-001: Interactive Navigation
- **Arrow Keys**: Up/Down to navigate choices
- **Enter**: Select current choice
- **Tab**: Accept default and move to next field
- **Esc**: Cancel wizard (with confirmation)
- **Ctrl+C**: Exit wizard (with confirmation)

### FR-002: Configuration Steps

#### Step 1: Welcome Screen
```
🎯 Browser Copilot Configuration Wizard

This wizard will help you set up Browser Copilot in less than 2 minutes.
You can press Enter to accept defaults or use arrow keys to change selections.

Press Enter to continue or Esc to cancel...
```

#### Step 2: Provider Selection
```
Select your LLM provider:

❯ github_copilot     (Recommended - No API key needed!)
  openai            (Requires API key)
  anthropic         (Requires API key)
  google            (Requires API key)
  azure             (Requires credentials)
  local             (Requires local model)

[Use arrows to move, Enter to select]
```

#### Step 3: Model Selection
```
Select model for github_copilot:

❯ gpt-4o            (Recommended - Best performance)
  gpt-4             (Previous generation)
  gpt-3.5-turbo     (Faster, lower cost)
  claude-3-sonnet   (Alternative model)

[Use arrows to move, Enter to select]
```

#### Step 4: Authentication (if needed)
```
GitHub Copilot requires authentication.

1. Go to: https://github.com/login/device
2. Enter code: XXXX-XXXX
3. Authorize the application

Waiting for authorization... ⣾

✅ Authentication successful!
```

#### Step 5: Browser Selection
```
Select your preferred browser:

❯ chromium    (Recommended - Best compatibility)
  chrome      (Google Chrome)
  firefox     (Mozilla Firefox)
  safari      (macOS only)
  edge        (Microsoft Edge)

[Use arrows to move, Enter to select]
```

#### Step 6: Test Mode
```
Default test execution mode:

❯ headless    (Faster, no browser window)
  headed      (See browser actions)

[Use arrows to move, Enter to select]
```

#### Step 7: Token Optimization
```
Token optimization level:

❯ medium      (Balanced - 20% reduction)
  high        (Maximum savings - 30% reduction)
  low         (Conservative - 10% reduction)
  none        (No optimization)

[Use arrows to move, Enter to select]
```

#### Step 8: Configuration Test
```
🔍 Testing your configuration...

✓ Connecting to github_copilot...
✓ Model gpt-4o is available
✓ Sending test prompt...
✓ Response received successfully
✓ Browser chromium is installed

✅ Configuration test passed!
```

#### Step 9: Save Configuration
```
Configuration Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Provider:        github_copilot
Model:           gpt-4o
Browser:         chromium
Mode:            headless
Optimization:    medium
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Save this configuration? [Y/n]: 
```

#### Step 10: Next Steps
```
🎉 Setup Complete!

You're ready to start testing. Try:

1. Quick test:
   browser-copilot --quick-test

2. Run an example:
   browser-copilot examples/google-ai-search.md

3. Create your own test:
   echo "Navigate to example.com and verify the title" | browser-copilot -

Need help? Run: browser-copilot --help
```

### FR-003: Dynamic Model Filtering
- Models list updates based on selected provider
- Only compatible models shown for each provider
- Model descriptions include context window size

### FR-004: Validation
- Test each configuration before proceeding
- Show clear error messages with solutions
- Allow retry on failure
- Skip to next step if validation passes

### FR-005: Error Handling
```
❌ Configuration test failed

Error: Unable to connect to openai
Reason: Invalid API key

Solutions:
1. Check your API key at https://platform.openai.com/api-keys
2. Set environment variable: export OPENAI_API_KEY="sk-..."
3. Try a different provider (GitHub Copilot requires no API key)

Would you like to:
❯ Enter API key now
  Choose different provider
  Skip validation (not recommended)
  Exit wizard
```

### FR-006: Configuration Storage
- Save to standard Browser Copilot config location
- Create backup of existing config
- Use same format as manual configuration
- Set appropriate file permissions

## Non-Functional Requirements

### NFR-001: Performance
- Wizard completes in < 2 minutes for typical setup
- Response to key presses < 100ms
- Provider/model list loads < 500ms

### NFR-002: Usability
- Works in all standard terminals
- Clear visual feedback for selections
- Consistent keyboard shortcuts
- Help text available at each step

### NFR-003: Compatibility
- Python 3.11+ (same as Browser Copilot)
- Works on Windows, macOS, Linux
- Terminal width >= 80 characters
- Supports both TTY and non-TTY environments

### NFR-004: Integration
- Uses ModelForge for provider/model discovery
- Respects existing environment variables
- Compatible with current config system
- Can be run multiple times safely

## Technical Requirements

### TR-001: Library Choice
- **Questionary** for interactive prompts
  - Provides arrow key navigation
  - Built-in validation
  - Custom styling support
  - Cross-platform compatibility

### TR-002: ModelForge Integration
- Query available providers dynamically
- Get model lists from ModelForge
- Use ModelForge authentication flows
- Validate using ModelForge test methods

### TR-003: State Management
- Track wizard progress
- Allow back navigation
- Save partial progress
- Resume interrupted setup

## Future Enhancements

1. **Import existing config** from other tools
2. **Profile support** for multiple configurations
3. **Team setup** with shared configurations
4. **Proxy configuration** wizard
5. **Advanced options** mode for power users

## Success Metrics

1. **Setup Time**: 80% of users complete setup in < 2 minutes
2. **Success Rate**: 95% of wizard runs result in working configuration
3. **User Satisfaction**: 90% prefer wizard over manual setup
4. **Error Recovery**: 100% of errors have actionable solutions
5. **Adoption**: 70% of new users use wizard for initial setup