# Context Management Strategy Requirements

## Overview

Browser Copilot uses LangGraph's ReAct agents for browser automation, which accumulate conversation history with each tool call. This leads to exponential token growth, especially for long test suites. We need a context management strategy to optimize token usage while maintaining agent effectiveness.

## Problem Statement

### Current Behavior
- ReAct agents send the entire conversation history with each LLM call
- Token usage grows from ~2,500 initial to ~33,000+ for complex tests
- Each tool call adds 300-1,000+ tokens to the context
- Long test suites can hit context limits or become expensive

### Impact
- Increased costs (2x or more tokens than necessary)
- Risk of hitting model context limits
- Slower response times due to larger prompts
- Reduced efficiency for long-running tests

## Goals

1. **Reduce token usage by 40-60%** without compromising test reliability
2. **Maintain agent's decision-making context** for accurate test execution
3. **Support long-running tests** without hitting context limits
4. **Preserve debugging information** for test reports
5. **Minimize implementation complexity** and maintain ReAct benefits

## Functional Requirements

### 1. Context Window Management

#### 1.1 Sliding Window
- Maintain a configurable window of recent tool calls (e.g., last 10-15)
- Preserve essential context outside the window
- Automatically prune older, less relevant interactions

#### 1.2 Context Preservation Rules
- **Always preserve**:
  - Initial test instructions and objectives
  - Current test phase/step being executed
  - Critical state information (login status, cart contents, etc.)
  - Error messages and recovery context

- **Selectively preserve**:
  - Screenshot paths and key observations
  - Form data that was entered
  - Verification results

- **Safe to prune**:
  - Successful navigation confirmations
  - Intermediate wait operations
  - Redundant page state updates
  - Verbose tool implementation details

### 2. Semantic Compression

#### 2.1 Tool Response Compression
- Truncate browser snapshots to essential elements
- Summarize console messages (group by type)
- Extract key information from page states
- Limit DOM tree depth in snapshots

#### 2.2 Phase Summarization
- After completing test phases, create concise summaries
- Replace detailed step history with phase outcomes
- Maintain enough context for subsequent phases

### 3. Checkpoint System

#### 3.1 Automatic Checkpoints
- Create checkpoints at natural boundaries:
  - After successful login
  - After adding items to cart
  - After form submissions
  - Before complex operations

#### 3.2 Checkpoint Contents
- Current URL and page state
- Authentication status
- Key page elements available
- Completed objectives
- Any persistent data (cart items, form values)

### 4. Intelligent Pruning

#### 4.1 Message Importance Scoring
- Assign importance scores to messages:
  - High: Errors, test objectives, state changes
  - Medium: Successful operations, verifications
  - Low: Wait operations, redundant confirmations

#### 4.2 Pruning Strategy
- Remove low-importance messages first
- Merge similar consecutive operations
- Keep error context longer than success context

## Non-Functional Requirements

### 1. Performance
- Context compression should add <100ms overhead
- Memory usage should remain bounded
- No impact on test execution reliability

### 2. Configurability
- Window size should be configurable
- Compression levels should be adjustable
- Users can disable context management if needed

### 3. Observability
- Log context management decisions in verbose mode
- Track token savings metrics
- Report compression effectiveness

### 4. Compatibility
- Must work with existing ReAct agent architecture
- Should not break existing test suites
- Graceful degradation if compression fails

## Technical Constraints

### 1. LangGraph Integration
- Must work within LangGraph's message format
- Cannot modify core ReAct agent behavior
- Must handle streaming responses correctly

### 2. Message Format Preservation
- Compressed messages must remain valid for the LLM
- Tool schemas must be preserved
- Agent decision context must be maintained

### 3. State Management
- Context compression must be stateless between runs
- No external dependencies for context storage
- Thread-safe for potential future parallelization

## Success Metrics

1. **Token Reduction**: 40-60% reduction in average token usage
2. **Test Reliability**: No decrease in test success rate
3. **Performance**: <5% increase in total execution time
4. **Context Limit**: Support tests 2-3x longer without hitting limits

## Configuration Options

```yaml
context_management:
  enabled: true
  strategy: "sliding_window"  # or "checkpoint", "hybrid"

  sliding_window:
    size: 15  # number of recent interactions to keep
    preserve_errors: true
    preserve_screenshots: true

  compression:
    level: "medium"  # none, low, medium, high
    truncate_snapshots: true
    max_snapshot_depth: 3
    summarize_console: true

  checkpoints:
    auto_checkpoint: true
    checkpoint_phases: ["login", "cart", "checkout"]
    max_checkpoint_size: 500  # tokens

  pruning:
    importance_threshold: "low"
    merge_similar: true
    keep_error_context: 5  # number of messages before/after errors
```

## Future Considerations

1. **Learning-based Optimization**: Analyze test patterns to predict important context
2. **Multi-agent Architecture**: Separate agents for different test phases
3. **External Context Store**: Offload context to vector database for retrieval
4. **Custom ReAct Implementation**: Build specialized agent for testing scenarios

## Dependencies

- Understanding of LangGraph's ReAct implementation
- Access to message flow between agent and LLM
- Ability to intercept and modify message streams
- Token counting capabilities for optimization metrics
