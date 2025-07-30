# ReAct Agent Study Guide for Context Management

## Overview

This guide provides essential information about LangGraph's ReAct agents to help implement effective context management strategies.

## Understanding ReAct Agents

### What is ReAct?

ReAct (Reasoning and Acting) is an agent architecture that combines:
- **Reasoning**: The agent thinks about what to do next
- **Acting**: The agent takes actions using tools
- **Observation**: The agent observes results and adjusts

### LangGraph's Implementation

```python
from langgraph.prebuilt import create_react_agent

# Basic structure
agent = create_react_agent(llm, tools)
```

Key characteristics:
1. **Stateful**: Maintains conversation history
2. **Iterative**: Loops through think-act-observe cycles
3. **Tool-based**: Uses tools to interact with environment
4. **Message-driven**: Communicates via message passing

## Message Flow in ReAct

### 1. Message Types

```python
# User message (initial prompt)
{
    "role": "user",
    "content": "Execute test steps..."
}

# Agent reasoning message
{
    "role": "assistant",
    "content": "I need to navigate to the website first..."
}

# Tool call message
{
    "role": "assistant",
    "tool_calls": [{
        "id": "call_123",
        "name": "browser_navigate",
        "args": {"url": "https://example.com"}
    }]
}

# Tool response message
{
    "role": "tool",
    "tool_call_id": "call_123",
    "content": "Navigated to https://example.com"
}
```

### 2. Message Accumulation Pattern

```
Initial State:
- Messages: [user_prompt]

After Step 1:
- Messages: [user_prompt, agent_reasoning_1, tool_call_1, tool_response_1]

After Step 2:
- Messages: [user_prompt, agent_reasoning_1, tool_call_1, tool_response_1,
            agent_reasoning_2, tool_call_2, tool_response_2]

...continues growing...
```

### 3. Why Context Grows

1. **Decision Making**: Agent needs history to make informed decisions
2. **Error Recovery**: Past attempts help avoid repeating mistakes
3. **State Tracking**: Maintains understanding of current state
4. **Tool Coordination**: Knows which tools have been used

## Key Components to Understand

### 1. Agent Executor

```python
# Simplified view of agent execution
async def execute(messages):
    while not done:
        # 1. Send all messages to LLM
        response = await llm.invoke(messages)

        # 2. Parse response for tool calls
        if has_tool_calls(response):
            tool_results = await execute_tools(response.tool_calls)
            messages.extend([response, *tool_results])
        else:
            # Final response
            messages.append(response)
            done = True

    return messages
```

### 2. Streaming Interface

```python
# How Browser Copilot uses it
async for chunk in agent.astream({"messages": [initial_prompt]}):
    # Each chunk contains new messages
    if "agent" in chunk:
        # Agent reasoning/decisions
    if "tools" in chunk:
        # Tool execution results
```

### 3. State Management

LangGraph maintains state internally:
- Message history
- Current step in reasoning
- Tool execution status
- Recursion depth

## Context Management Opportunities

### 1. Message Interception Points

```python
# Before sending to LLM
messages = original_messages
compressed_messages = compress(messages)  # Our opportunity
response = await llm.invoke(compressed_messages)

# After receiving from LLM
# Must maintain full history for agent's internal state
```

### 2. Safe Compression Strategies

**Safe to Compress**:
- Tool response content (especially repetitive data)
- Intermediate reasoning steps
- Successful operation confirmations
- Redundant state information

**Must Preserve**:
- Initial instructions
- Error messages and recovery context
- Current state indicators
- Recent tool interactions (sliding window)

### 3. Message Identity Preservation

```python
# Important: Maintain message structure
compressed_message = {
    "role": original_message["role"],
    "content": compress_content(original_message["content"]),
    # Preserve tool_calls, tool_call_id, etc.
}
```

## Implementation Considerations

### 1. Streaming Complexity

```python
# Messages arrive in chunks during streaming
async for chunk in agent.astream(input):
    # Chunk structure:
    # {
    #   "agent": {"messages": [...]},
    #   "tools": {"messages": [...]}
    # }

    # Must accumulate messages correctly
    all_messages.extend(extract_messages(chunk))
```

### 2. Tool Call Preservation

```python
# Tool calls and responses are linked by ID
tool_call = {
    "id": "call_abc123",  # Must preserve
    "name": "browser_click",
    "args": {...}
}

tool_response = {
    "tool_call_id": "call_abc123",  # Must match
    "content": "Clicked successfully"
}
```

### 3. Agent Decision Context

The agent needs certain context to make decisions:
- What was the original goal?
- What has been tried?
- What was the last successful action?
- What errors occurred?

## Best Practices for Context Management

### 1. Gradual Degradation

```python
# Start with least aggressive compression
if context_size < 50% of limit:
    use_light_compression()
elif context_size < 75% of limit:
    use_medium_compression()
else:
    use_aggressive_compression()
```

### 2. Semantic Preservation

```python
# Instead of truncating, summarize
original = "Clicked button with id='submit-form', waited for response,
           page loaded successfully with confirmation message"
compressed = "Form submitted successfully"
```

### 3. Error Context Priority

```python
# Keep more context around errors
if "error" in message.content:
    keep_previous_n_messages(5)
    keep_next_n_messages(5)
```

## Testing Your Implementation

### 1. Verify Message Integrity

```python
# Ensure compressed messages still work
original_result = await agent.run(original_messages)
compressed_result = await agent.run(compressed_messages)
assert same_outcome(original_result, compressed_result)
```

### 2. Monitor Decision Quality

- Track if agent makes same decisions
- Check if error recovery still works
- Verify tool usage patterns remain consistent

### 3. Edge Cases to Test

- Very long test suites (100+ steps)
- Tests with many errors and retries
- Tests with complex state management
- Parallel tool executions

## Common Pitfalls

### 1. Over-Compression

```python
# Bad: Losing critical context
compressed = "Did some stuff"  # Too vague

# Good: Preserve key information
compressed = "Logged in as user123, added 2 items to cart"
```

### 2. Message Ordering

```python
# Must maintain chronological order
# Agent expects messages in sequence
```

### 3. Tool Response Corruption

```python
# Bad: Modifying tool response structure
# Good: Only compress content field
```

## Resources for Deep Dive

### 1. LangGraph Documentation
- Message formats
- Agent lifecycle
- Streaming behavior
- State management

### 2. Code to Study

```python
# Key files in langchain/langgraph:
- prebuilt/react.py  # ReAct implementation
- pregel/base.py     # Streaming logic
- channels/base.py   # Message passing
```

### 3. Experimentation Ideas

1. Log all messages to understand patterns
2. Measure token usage at each step
3. Identify redundancy patterns
4. Test compression strategies in isolation

## Implementation Checklist

- [ ] Understand message format completely
- [ ] Study streaming chunk structure
- [ ] Identify safe compression points
- [ ] Design message preservation rules
- [ ] Plan testing strategy
- [ ] Consider rollback mechanisms
- [ ] Document compression trade-offs

## Questions to Answer

Before implementing, ensure you understand:

1. How does the agent use historical messages for decisions?
2. What's the minimum context needed for each tool?
3. How do tool calls and responses relate?
4. What happens if message order is disrupted?
5. How does streaming affect message accumulation?

## Next Steps

1. **Experiment**: Create simple test to log all messages
2. **Analyze**: Identify patterns in message growth
3. **Prototype**: Try simple compression strategies
4. **Measure**: Quantify token savings vs. reliability
5. **Iterate**: Refine based on results
