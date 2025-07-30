# Browser Copilot Studio - Design Document

## Overview

Browser Copilot Studio is an interactive CLI environment for test automation, providing a REPL-like experience for QA engineers to design, execute, and debug tests through natural language conversations.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Interface                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Studio    │  │   Command    │  │    Session    │  │
│  │   Shell     │  │   Parser     │  │   Manager     │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    Core Engine                           │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │    Test     │  │   Browser    │  │      AI       │  │
│  │  Designer   │  │  Controller  │  │   Assistant   │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    Storage Layer                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │    Test     │  │   Session    │  │   History     │  │
│  │  Repository │  │    Store     │  │   Tracker     │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Studio Shell

```python
class StudioShell:
    """Interactive shell for Browser Copilot Studio"""

    def __init__(self, config: StudioConfig):
        self.config = config
        self.session_manager = SessionManager()
        self.command_parser = CommandParser()
        self.prompt = StudioPrompt()

    async def run(self):
        """Main REPL loop"""
        while True:
            command = await self.prompt.get_input()
            result = await self.execute_command(command)
            self.display_result(result)
```

### 2. Command System

```python
@dataclass
class Command:
    """Base command structure"""
    name: str
    args: List[str]
    options: Dict[str, Any]

class CommandRegistry:
    """Registry of available commands"""
    commands = {
        'new': NewTestCommand,
        'run': RunTestCommand,
        'debug': DebugCommand,
        'step': StepCommand,
        'edit': EditTestCommand,
        'list': ListTestsCommand,
        'help': HelpCommand,
    }
```

### 3. Test Designer

```python
class TestDesigner:
    """Conversational test design engine"""

    async def design_test(self, intent: str) -> TestSuite:
        """Design test through conversation"""
        conversation = []
        test_steps = []

        while not self.is_complete(test_steps):
            response = await self.ai_assistant.get_next_question(
                intent, conversation, test_steps
            )
            user_input = await self.get_user_response(response)
            conversation.append((response, user_input))

            if action := self.extract_action(user_input):
                test_steps.append(action)
                await self.preview_action(action)
```

### 4. Browser Controller

```python
class BrowserController:
    """Manages persistent browser session"""

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def ensure_browser(self):
        """Ensure browser is running"""
        if not self.browser:
            self.browser = await self.launch_browser()
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
```

### 5. Session Manager

```python
class SessionManager:
    """Manages studio sessions"""

    def __init__(self):
        self.current_session = None
        self.session_history = []
        self.checkpoints = []

    async def save_checkpoint(self, name: str):
        """Save current state as checkpoint"""
        checkpoint = {
            'name': name,
            'timestamp': datetime.now(),
            'test_state': self.current_test.serialize(),
            'browser_state': await self.browser.get_state(),
            'conversation': self.conversation_history
        }
        self.checkpoints.append(checkpoint)
```

## Data Models

### Test Definition

```python
@dataclass
class TestStep:
    """Single test step"""
    id: str
    action: str
    target: Optional[str]
    value: Optional[str]
    assertion: Optional[str]
    screenshot: Optional[bool]

@dataclass
class TestSuite:
    """Complete test suite"""
    id: str
    name: str
    description: str
    steps: List[TestStep]
    metadata: TestMetadata
    created_at: datetime
    updated_at: datetime
```

### Session State

```python
@dataclass
class StudioSession:
    """Studio session state"""
    id: str
    start_time: datetime
    browser_state: BrowserState
    current_test: Optional[TestSuite]
    conversation_history: List[ConversationTurn]
    checkpoints: List[Checkpoint]
```

## User Interface Design

### Command Line Interface

```
┌─ Browser Copilot Studio ─────────────────────────────────┐
│ Session: test-login-flow-2024-07-30                      │
│ Browser: ● Connected (chromium)                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ studio> new test "user login flow"                      │
│                                                          │
│ 🤖 I'll help you create a login test. Let's start by   │
│    navigating to your application.                      │
│                                                          │
│    What's the URL of your login page?                   │
│                                                          │
│ > https://app.example.com/login                          │
│                                                          │
│ [Browser navigates to login page]                       │
│ 📸 Screenshot saved: step-1-navigate.png                │
│                                                          │
│ 🤖 I can see the login form with:                      │
│    - Email/username field                               │
│    - Password field                                     │
│    - "Remember me" checkbox                             │
│    - "Sign In" button                                   │
│                                                          │
│    What credentials should I use for testing?           │
│                                                          │
│ studio>                                                  │
└──────────────────────────────────────────────────────────┘
```

### Status Bar

```
[Session: active] [Test: login-flow (5 steps)] [Browser: connected] [Mode: design]
```

## Integration Points

### 1. LLM Integration

```python
class AIAssistant:
    """AI assistant for test design"""

    def __init__(self, llm_provider: str, model: str):
        self.llm = ModelForgeRegistry().get_llm(provider, model)
        self.prompt_manager = PromptManager()

    async def suggest_next_step(self, context: TestContext) -> str:
        """Suggest next test step based on context"""
        prompt = self.prompt_manager.build_suggestion_prompt(context)
        return await self.llm.ainvoke(prompt)
```

### 2. Browser Integration

- Persistent Playwright browser instance
- Real-time page state synchronization
- Visual feedback for actions
- Screenshot capture at each step

### 3. Storage Integration

- Tests saved as enhanced Markdown
- Git-friendly format
- Metadata in YAML frontmatter
- Binary assets (screenshots) in session directory

## Error Handling

### Graceful Degradation

```python
class StudioErrorHandler:
    """Handle errors gracefully in studio"""

    async def handle_browser_error(self, error: Exception):
        """Handle browser disconnection"""
        if isinstance(error, BrowserDisconnectedError):
            await self.prompt_reconnect()
        else:
            await self.show_error_with_recovery(error)
```

## Performance Considerations

### 1. Browser Lifecycle
- Keep browser warm between commands
- Lazy loading of browser instance
- Automatic cleanup on exit

### 2. Memory Management
- Limit conversation history size
- Periodic checkpoint cleanup
- Efficient test storage format

### 3. Response Time
- Streaming LLM responses
- Parallel browser operations
- Cached element selectors

## Security Considerations

### 1. Credential Handling
- Never store passwords in test files
- Support environment variables
- Mask sensitive data in UI

### 2. Browser Isolation
- Separate context per session
- Clear cookies/storage between tests
- Sandbox mode by default

## Future Extensibility

### Plugin System

```python
class StudioPlugin(ABC):
    """Base class for studio plugins"""

    @abstractmethod
    async def on_command(self, command: Command) -> Optional[Any]:
        """Handle custom commands"""
        pass

    @abstractmethod
    async def on_test_step(self, step: TestStep) -> None:
        """React to test steps"""
        pass
```

### Extension Points
- Custom commands
- Test step processors
- Export formats
- Browser providers
- AI providers
