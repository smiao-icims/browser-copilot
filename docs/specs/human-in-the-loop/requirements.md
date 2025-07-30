# Human-in-the-Loop Response Handling Requirements

## Overview

Browser Copilot is designed for autonomous browser automation without human intervention. However, LLMs sometimes generate responses asking for human input, breaking the automation flow. This specification defines how to detect and handle such situations.

## Problem Statement

### Current Issue
- LLM generates questions like "Would you like to explore these results further?"
- Agent waits for human response that never comes
- Test execution stalls or fails
- Particularly problematic when context is trimmed (losing test instructions)

### Root Causes
1. **Context Loss**: Test instructions trimmed from conversation history
2. **LLM Behavior**: Models trained to be interactive/helpful
3. **Ambiguous Instructions**: Test steps not explicit about continuation
4. **Error Recovery**: LLM unsure how to proceed after errors

## Functional Requirements

### Detection (HIL-001)
**Priority**: High

The system MUST detect when LLM is requesting human input:

1. **Pattern Detection**
   - Questions ending with "?"
   - Phrases like "Would you like", "Should I", "Do you want"
   - Waiting for confirmation: "Please confirm", "Is this correct"
   - Menu-style options: "You can: 1) ... 2) ..."

2. **Context Analysis**
   - Check if response lacks concrete browser actions
   - Detect when no tool calls are made
   - Identify conversational patterns vs. action patterns

### Prevention (HIL-002)
**Priority**: High

The system MUST prevent human-in-the-loop responses:

1. **Context Preservation**
   - Always preserve initial test instructions
   - Maintain test completion criteria in context
   - Keep error recovery instructions visible

2. **Prompt Engineering**
   - Explicit "no human interaction" instructions
   - "Continue until all steps complete" directives
   - "On error, report and continue" guidance

3. **System Prompts**
   - Add to system prompt: "You are an autonomous agent. Never ask for human input."
   - Include: "If uncertain, make reasonable assumptions and continue."
   - Specify: "Complete all test steps without waiting for confirmation."

### Recovery (HIL-003)
**Priority**: Medium

When human-in-the-loop is detected:

1. **Automatic Continuation**
   - Generate implied "yes, continue" response
   - Re-prompt with stronger autonomous instructions
   - Inject test context reminder

2. **Fallback Actions**
   - If no clear next step, check test success criteria
   - If criteria met, generate test report
   - If not met, attempt next numbered step

3. **Error Reporting**
   - Log human-in-the-loop detection
   - Include in test report as warning
   - Track frequency for model tuning

## Technical Requirements

### Implementation Approach

1. **Response Analyzer**
   ```python
   class ResponseAnalyzer:
       def is_human_in_loop(self, response: str) -> bool:
           """Detect if response is asking for human input."""

       def extract_implied_action(self, response: str) -> Optional[str]:
           """Extract what the LLM would likely do if human said 'yes'."""
   ```

2. **Context Injector**
   ```python
   class ContextInjector:
       def inject_autonomy_reminder(self, messages: List[Message]) -> List[Message]:
           """Add reminders about autonomous operation."""

       def ensure_test_context(self, messages: List[Message]) -> List[Message]:
           """Ensure test instructions remain in context."""
   ```

3. **Auto-Responder**
   ```python
   class AutoResponder:
       def generate_continuation(self, context: Dict) -> str:
           """Generate appropriate continuation response."""

       def create_affirmative_response(self) -> Message:
           """Create 'yes, continue' style response."""
   ```

### Integration Points

1. **Pre-Model Hook**
   - Ensure test instructions are preserved
   - Add autonomy reminders if needed

2. **Post-Model Hook**
   - Analyze response for HIL patterns
   - Trigger recovery if detected

3. **Agent Wrapper**
   - Intercept HIL responses
   - Inject continuation logic
   - Maintain conversation flow

## Configuration

### Settings
```yaml
human_in_loop:
  detection:
    enabled: true
    patterns:
      - "would you like"
      - "should i"
      - "do you want"
      - "please confirm"
    confidence_threshold: 0.8

  prevention:
    preserve_test_context: true
    inject_autonomy_reminders: true
    reminder_frequency: 5  # every N messages

  recovery:
    auto_continue: true
    max_recovery_attempts: 3
    fallback_to_report: true
```

### CLI Arguments
```bash
--no-human-in-loop          # Disable HIL handling
--hil-strict               # Fail immediately on HIL detection
--hil-verbose              # Log all HIL analysis
```

## Success Metrics

1. **Zero HIL Occurrences**: Target 0% human-in-loop responses
2. **Recovery Success**: 100% successful recovery when HIL detected
3. **No False Positives**: Legitimate questions in test output not flagged
4. **Performance Impact**: <10ms per response analysis

## Testing Strategy

### Test Scenarios
1. Context with/without test instructions
2. Various question patterns
3. Error recovery situations
4. Long conversations with context trimming
5. Different LLM providers/models

### Test Cases
- Simulate context loss scenarios
- Test pattern detection accuracy
- Verify recovery mechanisms
- Ensure no interference with normal operation
- Validate with real browser automation tasks

## Implementation Priority

### Phase 1: Detection & Logging
- Implement ResponseAnalyzer
- Add logging without intervention
- Gather data on HIL frequency

### Phase 2: Prevention
- Enhanced prompts
- Context preservation rules
- Test with context management strategies

### Phase 3: Recovery
- Auto-continuation logic
- Integration with agent flow
- Comprehensive testing

## Notes

1. This is critical for production reliability
2. Should work with all context management strategies
3. Consider model-specific tuning (GPT-4 vs Claude vs others)
4. May need adjustment as models evolve
5. Should be transparent in test reports
