# Context Management Strategy Design

## Architecture Overview

The context management system will be implemented as a middleware layer between the ReAct agent and the LLM, intercepting and optimizing message flows while preserving agent behavior.

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Test Suite    │────▶│  Browser Pilot   │────▶│   ReAct Agent   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                          │
                                ▼                          ▼
                        ┌──────────────────┐      ┌─────────────────┐
                        │ Context Manager  │◀─────│  Message Stream │
                        └──────────────────┘      └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │ Optimized Stream │
                        └──────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │      LLM         │
                        └──────────────────┘
```

## Component Design

### 1. Context Manager

```python
class ContextManager:
    """Manages conversation context for ReAct agents"""

    def __init__(self, config: ContextConfig):
        self.config = config
        self.window = SlidingWindow(config.window_size)
        self.compressor = MessageCompressor(config.compression_level)
        self.checkpoints = CheckpointManager()
        self.pruner = IntelligentPruner(config.pruning_rules)
        self.metrics = ContextMetrics()

    async def process_messages(
        self,
        messages: List[Message],
        current_phase: Optional[str] = None
    ) -> List[Message]:
        """Process and optimize message history"""
        # 1. Update metrics
        self.metrics.record_input_size(messages)

        # 2. Apply context management strategy
        if self.config.strategy == "sliding_window":
            messages = await self._apply_sliding_window(messages)
        elif self.config.strategy == "checkpoint":
            messages = await self._apply_checkpoint_strategy(messages, current_phase)
        elif self.config.strategy == "hybrid":
            messages = await self._apply_hybrid_strategy(messages, current_phase)

        # 3. Apply compression
        messages = await self.compressor.compress(messages)

        # 4. Record metrics
        self.metrics.record_output_size(messages)

        return messages
```

### 2. Sliding Window Implementation

```python
class SlidingWindow:
    """Maintains a sliding window of recent messages"""

    def __init__(self, window_size: int = 15):
        self.window_size = window_size
        self.preserved_messages = []  # Important messages outside window

    def apply(self, messages: List[Message]) -> List[Message]:
        """Apply sliding window to message history"""
        # 1. Identify messages to preserve
        preserved = self._extract_preserved_messages(messages)

        # 2. Get recent messages within window
        recent = messages[-self.window_size:]

        # 3. Merge preserved and recent, avoiding duplicates
        return self._merge_messages(preserved, recent)

    def _extract_preserved_messages(self, messages: List[Message]) -> List[Message]:
        """Extract messages that must be preserved"""
        preserved = []

        for msg in messages:
            if self._should_preserve(msg):
                preserved.append(msg)

        return preserved

    def _should_preserve(self, msg: Message) -> bool:
        """Determine if a message should be preserved"""
        # Preserve initial instructions
        if msg.role == "user" and msg.index == 0:
            return True

        # Preserve error messages
        if "error" in msg.content.lower():
            return True

        # Preserve state changes
        if any(keyword in msg.content.lower()
               for keyword in ["logged in", "cart updated", "order completed"]):
            return True

        return False
```

### 3. Message Compression

```python
class MessageCompressor:
    """Compresses message content while preserving meaning"""

    def __init__(self, level: CompressionLevel):
        self.level = level
        self.snapshot_compressor = SnapshotCompressor()
        self.console_compressor = ConsoleMessageCompressor()

    async def compress(self, messages: List[Message]) -> List[Message]:
        """Compress messages based on compression level"""
        if self.level == CompressionLevel.NONE:
            return messages

        compressed = []
        for msg in messages:
            compressed_msg = await self._compress_message(msg)
            compressed.append(compressed_msg)

        return compressed

    async def _compress_message(self, msg: Message) -> Message:
        """Compress individual message"""
        if msg.type == "tool_response":
            return await self._compress_tool_response(msg)
        elif msg.type == "agent":
            return await self._compress_agent_message(msg)
        else:
            return msg  # Don't compress user messages

    async def _compress_tool_response(self, msg: Message) -> Message:
        """Compress tool response messages"""
        compressed_content = msg.content

        # Compress browser snapshots
        if "snapshot" in msg.tool_name:
            compressed_content = self.snapshot_compressor.compress(
                msg.content,
                max_depth=3,
                preserve_interactive=True
            )

        # Compress console messages
        elif "console" in msg.content:
            compressed_content = self.console_compressor.compress(msg.content)

        # Truncate long responses
        elif len(msg.content) > 1000:
            compressed_content = self._truncate_with_summary(msg.content)

        return Message(
            role=msg.role,
            content=compressed_content,
            tool_name=msg.tool_name,
            metadata={**msg.metadata, "compressed": True}
        )
```

### 4. Checkpoint Manager

```python
class CheckpointManager:
    """Manages checkpoints for context reset"""

    def __init__(self):
        self.checkpoints = {}
        self.current_phase = None

    def create_checkpoint(
        self,
        phase: str,
        state: BrowserState,
        completed_objectives: List[str]
    ) -> Checkpoint:
        """Create a checkpoint for the current phase"""
        checkpoint = Checkpoint(
            phase=phase,
            timestamp=datetime.now(UTC),
            state=state,
            completed_objectives=completed_objectives,
            summary=self._generate_summary(state, completed_objectives)
        )

        self.checkpoints[phase] = checkpoint
        return checkpoint

    def get_context_from_checkpoint(
        self,
        checkpoint: Checkpoint,
        original_instructions: str
    ) -> List[Message]:
        """Generate minimal context from checkpoint"""
        return [
            Message(
                role="user",
                content=original_instructions
            ),
            Message(
                role="assistant",
                content=f"""Previous phases completed. Current state:

Phase: {checkpoint.phase}
URL: {checkpoint.state.url}
Page: {checkpoint.state.page_title}
Completed: {', '.join(checkpoint.completed_objectives)}

{checkpoint.summary}

Continuing with the next phase..."""
            )
        ]

    def _generate_summary(
        self,
        state: BrowserState,
        objectives: List[str]
    ) -> str:
        """Generate concise summary of completed work"""
        return f"Successfully completed {len(objectives)} objectives. " \
               f"Currently on {state.page_title} page."
```

### 5. Intelligent Pruner

```python
class IntelligentPruner:
    """Intelligently prunes messages based on importance"""

    def __init__(self, rules: PruningRules):
        self.rules = rules
        self.importance_scorer = ImportanceScorer()

    def prune(
        self,
        messages: List[Message],
        target_size: Optional[int] = None
    ) -> List[Message]:
        """Prune messages based on importance scores"""
        # 1. Score all messages
        scored_messages = [
            (msg, self.importance_scorer.score(msg, messages))
            for msg in messages
        ]

        # 2. Sort by importance (descending)
        scored_messages.sort(key=lambda x: x[1], reverse=True)

        # 3. Keep messages above threshold or until target size
        kept_messages = []
        current_size = 0

        for msg, score in scored_messages:
            if score >= self.rules.importance_threshold:
                kept_messages.append(msg)
                current_size += self._estimate_tokens(msg)

                if target_size and current_size >= target_size:
                    break
            elif self._must_keep(msg):
                kept_messages.append(msg)

        # 4. Restore chronological order
        kept_messages.sort(key=lambda m: m.timestamp)

        # 5. Merge similar consecutive messages
        if self.rules.merge_similar:
            kept_messages = self._merge_similar_messages(kept_messages)

        return kept_messages
```

### 6. Context Metrics

```python
class ContextMetrics:
    """Tracks context management effectiveness"""

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.compression_events = []
        self.checkpoint_events = []

    def record_compression(
        self,
        input_size: int,
        output_size: int,
        strategy: str
    ):
        """Record compression event"""
        event = CompressionEvent(
            timestamp=datetime.now(UTC),
            input_tokens=input_size,
            output_tokens=output_size,
            reduction_percent=(1 - output_size/input_size) * 100,
            strategy=strategy
        )
        self.compression_events.append(event)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        if not self.compression_events:
            return {"status": "no compression events"}

        total_input = sum(e.input_tokens for e in self.compression_events)
        total_output = sum(e.output_tokens for e in self.compression_events)

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_reduction": (1 - total_output/total_input) * 100,
            "compression_count": len(self.compression_events),
            "average_reduction": sum(e.reduction_percent for e in self.compression_events) / len(self.compression_events),
            "checkpoint_count": len(self.checkpoint_events)
        }
```

## Integration with ReAct Agent

### 1. Message Interception

```python
class ContextManagedAgent:
    """Wrapper around ReAct agent with context management"""

    def __init__(
        self,
        agent: Any,
        context_manager: ContextManager
    ):
        self.agent = agent
        self.context_manager = context_manager
        self.original_messages = []

    async def astream(self, messages: Dict[str, Any]):
        """Stream with context management"""
        # Store original messages for reference
        self.original_messages = messages.get("messages", [])

        # Apply context management
        optimized_messages = await self.context_manager.process_messages(
            self.original_messages
        )

        # Stream with optimized messages
        async for chunk in self.agent.astream({"messages": optimized_messages}):
            # Intercept and process chunks
            yield await self._process_chunk(chunk)

    async def _process_chunk(self, chunk: Dict[str, Any]):
        """Process streaming chunks"""
        # Update original messages with new interactions
        if "agent" in chunk:
            for msg in chunk["agent"].get("messages", []):
                self.original_messages.append(msg)

        if "tools" in chunk:
            for msg in chunk["tools"].get("messages", []):
                self.original_messages.append(msg)

        return chunk
```

### 2. Configuration

```python
@dataclass
class ContextConfig:
    """Configuration for context management"""
    enabled: bool = True
    strategy: str = "sliding_window"  # sliding_window, checkpoint, hybrid

    # Sliding window config
    window_size: int = 15
    preserve_errors: bool = True
    preserve_screenshots: bool = True

    # Compression config
    compression_level: str = "medium"  # none, low, medium, high
    truncate_snapshots: bool = True
    max_snapshot_depth: int = 3
    summarize_console: bool = True

    # Checkpoint config
    auto_checkpoint: bool = True
    checkpoint_phases: List[str] = field(default_factory=lambda: ["login", "cart", "checkout"])
    max_checkpoint_size: int = 500  # tokens

    # Pruning config
    importance_threshold: float = 0.3  # 0-1 score
    merge_similar: bool = True
    keep_error_context: int = 5  # messages before/after errors
```

## Implementation Strategy

### Phase 1: Basic Sliding Window
1. Implement SlidingWindow class
2. Add message preservation logic
3. Integrate with agent streaming
4. Test with simple scenarios

### Phase 2: Message Compression
1. Implement compression strategies
2. Add snapshot truncation
3. Console message summarization
4. Test compression effectiveness

### Phase 3: Checkpoint System
1. Implement checkpoint creation
2. Add phase detection
3. Context reconstruction from checkpoints
4. Test with multi-phase scenarios

### Phase 4: Intelligent Pruning
1. Implement importance scoring
2. Add pruning algorithms
3. Message merging logic
4. Fine-tune scoring weights

### Phase 5: Metrics and Optimization
1. Add comprehensive metrics
2. Implement adaptive strategies
3. Performance optimization
4. Configuration tuning

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock message streams
- Verify compression algorithms
- Test edge cases

### Integration Tests
- Test with real ReAct agents
- Verify message integrity
- Test streaming behavior
- Measure token reduction

### Performance Tests
- Benchmark compression overhead
- Memory usage profiling
- Token reduction measurements
- End-to-end timing

### Reliability Tests
- Test with various test suites
- Verify no functionality loss
- Error handling scenarios
- Context limit testing
