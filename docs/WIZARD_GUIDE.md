# Browser Copilot Configuration Wizard Guide 🎯

The Browser Copilot Configuration Wizard provides an interactive, user-friendly way to set up Browser Copilot in less than 2 minutes. No prior knowledge of LLM providers or configuration files required!

## Table of Contents

1. [Quick Start](#quick-start)
2. [What the Wizard Does](#what-the-wizard-does)
3. [Running the Wizard](#running-the-wizard)
4. [Wizard Steps Explained](#wizard-steps-explained)
5. [Common Scenarios](#common-scenarios)
6. [Troubleshooting](#troubleshooting)
7. [Manual Configuration](#manual-configuration)

## Quick Start

### First-Time Setup

If you're running Browser Copilot for the first time without any configuration, you'll be prompted automatically:

```bash
browser-copilot examples/google-ai-search.md

# Output:
⚠️  No configuration found.

Would you like to run the setup wizard? It takes less than 2 minutes.
You can also run it anytime with: browser-copilot --setup-wizard

Run setup wizard now? [Y/n]: y
```

### Running the Wizard Manually

You can run the wizard anytime:

```bash
browser-copilot --setup-wizard
```

## What the Wizard Does

The wizard helps you:

1. **Select an LLM Provider** - GitHub Copilot is recommended (no API key needed!)
2. **Choose a Model** - Appropriate models for your selected provider
3. **Handle Authentication** - API keys or GitHub device flow
4. **Pick a Browser** - Chromium, Chrome, Firefox, etc.
5. **Configure Options** - Headless mode, token optimization, viewport size
6. **Validate Everything** - Tests your configuration before saving
7. **Save Configuration** - Stores settings for future use

## Running the Wizard

### Navigation

- **↑/↓ Arrow Keys**: Navigate between options
- **Enter**: Select the highlighted option
- **Tab**: Accept default and continue
- **Esc**: Go back or cancel
- **Ctrl+C**: Exit wizard (with confirmation)

### Example Walkthrough

```
╔═══════════════════════════════════════════╗
║      🎯 Browser Copilot Setup Wizard        ║
║   Simple • Reliable • Token Efficient     ║
╚═══════════════════════════════════════════╝

This wizard will help you set up Browser Copilot in less than 2 minutes.
You can press Enter to accept defaults or use arrow keys to change selections.

Ready to begin setup? (Y/n) ▏
```

## Wizard Steps Explained

### Step 1: Provider Selection

```
📋 Step 1: Select LLM Provider

Select your LLM provider:
❯ github_copilot     (Recommended - No API key needed!)
  openai            (Requires API key)
  anthropic         (Requires API key)
  google            (Requires API key)
  azure             (Requires credentials)
  local             (Requires local model)
```

**Tip**: GitHub Copilot is recommended because:
- No API key setup required
- Uses your existing GitHub account
- Great performance with GPT-4o
- Simple device flow authentication

### Step 2: Model Selection

Models are filtered based on your provider:

```
🤖 Step 2: Select Model for github_copilot

Select model for github_copilot:
❯ gpt-4o            (Recommended - Best performance, 128k context)
  gpt-4             (Previous generation, 8k context)
  gpt-3.5-turbo     (Faster, lower cost, 16k context)
  claude-3-sonnet   (Alternative model, 200k context)
```

### Step 3: Authentication

#### For GitHub Copilot:

```
🔐 GitHub Copilot requires authentication.

1. Go to: https://github.com/login/device
2. Enter code: ABCD-1234
3. Authorize the application

Waiting for authorization... ⣾
```

#### For API Key Providers:

```
🔑 Step 3: OpenAI API Key

Get your API key from: https://platform.openai.com/api-keys
Set as environment variable: export OPENAI_API_KEY='your-key'

Enter API key (or press Enter to set later): ▏
```

### Step 4: Browser Selection

```
🌐 Step 4: Select Browser

Select your preferred browser:
❯ chromium    (Recommended - Best compatibility, ✓ Installed)
  chrome      (Google Chrome, ✗ Not installed)
  firefox     (Mozilla Firefox, ✓ Installed)
  webkit      (Safari engine, ✓ Installed)
  edge        (Microsoft Edge, ✗ Not installed)
  → Install browsers...
```

### Step 5: Test Mode

```
🖥️  Step 5: Test Execution Mode

Default test execution mode:
❯ headless    (Faster, no browser window)
  headed      (See browser actions)
```

### Step 6: Token Optimization

```
💰 Step 6: Token Optimization

Reduce API costs by optimizing prompts:

Token optimization level:
❯ medium      (Balanced - 20% reduction)
  high        (Maximum savings - 30% reduction)
  low         (Conservative - 10% reduction)
  none        (No optimization)
```

### Step 7: Viewport Size

```
📐 Step 7: Browser Viewport Size

Default viewport size:
❯ Desktop HD (1920x1080)  (1920x1080)
  Desktop (1366x768)      (1366x768)
  Tablet (1024x768)       (1024x768)
  Mobile (375x812)        (375x812)
  Custom...
```

### Step 8: Validation

```
🔍 Step 8: Validating Configuration

• Checking provider configuration... ✓
• Testing model availability... ✓
• Sending test prompt... ✓
• Checking browser installation... ✓

✅ Configuration test passed!
```

### Step 9: Save Configuration

```
💾 Step 9: Save Configuration

Configuration Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Provider:        github_copilot
Model:           gpt-4o
Browser:         chromium
Mode:            headless
Optimization:    medium
Viewport:        1920x1080
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Save this configuration? [Y/n]: y

✅ Configuration saved to: /Users/you/.browser_copilot/settings/config.json
```

### Step 10: Next Steps

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

## Common Scenarios

### Scenario 1: New User with GitHub Account

1. Run `browser-copilot --setup-wizard`
2. Select `github_copilot` (already highlighted)
3. Select `gpt-4o` model
4. Complete GitHub device flow authentication
5. Keep defaults for everything else
6. Save and start testing!

**Time**: ~90 seconds

### Scenario 2: Existing OpenAI User

1. Set environment variable: `export OPENAI_API_KEY="sk-..."`
2. Run `browser-copilot --setup-wizard`
3. Select `openai`
4. Select `gpt-4` or `gpt-3.5-turbo`
5. Wizard detects API key automatically
6. Configure browser and options
7. Save and go!

**Time**: ~60 seconds

### Scenario 3: Reconfiguring Existing Setup

1. Run `browser-copilot --setup-wizard`
2. Navigate through steps (current values shown as defaults)
3. Change only what you need
4. Previous config is backed up automatically
5. Save new configuration

**Time**: ~45 seconds

## Troubleshooting

### "Questionary not installed"

```bash
pip install questionary
# or
uv pip install questionary
```

### "No providers found"

The wizard will fall back to a default list. You can:
1. Continue with manual provider selection
2. Fix ModelForge installation: `pip install model-forge-llm`

### "Authentication failed"

For GitHub Copilot:
- Ensure you completed the device flow
- Check you have an active GitHub Copilot subscription
- Try again (authentication can timeout)

For API keys:
- Verify the key is correct and active
- Check the key has the necessary permissions
- Ensure no extra spaces or quotes

### "Browser not installed"

Select "→ Install browsers..." option, or run:
```bash
npx playwright install chromium
```

### "Validation failed"

Common solutions:
1. Check internet connection
2. Verify API key/authentication
3. Try a different model
4. Skip validation (not recommended for first setup)

## Manual Configuration

If you prefer manual configuration or need to automate setup:

### Option 1: Environment Variables

```bash
export BROWSER_PILOT_PROVIDER=github_copilot
export BROWSER_PILOT_MODEL=gpt-4o
export BROWSER_PILOT_BROWSER=chromium
export BROWSER_PILOT_HEADLESS=true
export BROWSER_PILOT_COMPRESSION_LEVEL=medium
```

### Option 2: Configuration File

Create `~/.browser_copilot/settings/config.json`:

```json
{
  "provider": "github_copilot",
  "model": "gpt-4o",
  "browser": "chromium",
  "headless": true,
  "compression_level": "medium",
  "viewport": {
    "width": 1920,
    "height": 1080
  }
}
```

### Option 3: ModelForge CLI

```bash
modelforge config add --provider github_copilot --model gpt-4o
modelforge config set-default --provider github_copilot --model gpt-4o
```

## Advanced Features

### Multiple Configurations

Coming soon: Profile support for different projects or clients.

### Headless Server Setup

For CI/CD environments:

```bash
# Create config programmatically
cat > config.json << EOF
{
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "browser": "chromium",
  "headless": true,
  "api_key": "$OPENAI_API_KEY"
}
EOF

# Copy to Browser Copilot config location
mkdir -p ~/.browser_copilot/settings
cp config.json ~/.browser_copilot/settings/
```

## Getting Help

- **GitHub Issues**: Report bugs or request features
- **Documentation**: See other guides in the `docs/` directory
- **Quick Help**: Run `browser-copilot --help`

---

Remember: The wizard is designed to get you running quickly. You can always reconfigure later as your needs change!