# Context Management Flow Diagram

## Message History Growth Without Context Management

```
Step 1: [Human: Run test]
Step 2: [Human: Run test] → [AI: Navigating] → [Tool: Success]
Step 3: [Human: Run test] → [AI: Navigating] → [Tool: Success] → [AI: Taking snapshot] → [Tool: Page data]
Step 4: [Human: Run test] → [AI: Navigating] → [Tool: Success] → [AI: Taking snapshot] → [Tool: Page data] → [AI: Clicking button] → [Tool: Success]
...
Step N: [500+ messages accumulating, 30k+ tokens]
```

## With Context Management (Sliding Window)

```
Original: [Message 1] [Message 2] [Message 3] ... [Message 98] [Message 99] [Message 100]
                ↓
         Context Manager
                ↓
    ┌─────────────────────────┐
    │  1. Score Messages      │
    │  2. Preserve Critical   │
    │  3. Apply Window        │
    │  4. Maintain Pairs      │
    └─────────────────────────┘
                ↓
Trimmed: [Message 1] [Message 85] [Message 86] ... [Message 99] [Message 100]
         ↑                                                        ↑
    First Message                                          Recent Messages
    (Original Prompt)                                      (Current Context)
```

## Tool Call Pair Preservation

```
MUST PRESERVE TOGETHER:
┌─────────────────┐      ┌──────────────────┐
│   AIMessage     │ ───→ │   ToolMessage    │
│ tool_calls=[    │      │ tool_call_id=123 │
│   {id: "123"}   │      │ result="Success" │
│ ]               │      └──────────────────┘
└─────────────────┘

BREAKING PAIRS = API ERROR ❌
```

## Strategy Comparison

```
No-Op Strategy:
[■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■] 100% tokens

Sliding Window:
[■■■■■■■■■■■■■■■■■■■■■■□□□□□□□□□□□□□□□□□□] 55% tokens

LangChain Trim:
[■■■■■■■■■■■■■■■■□□□□□□□□□□□□□□□□□□□□□□□□] 40% tokens
```

## Configuration Impact

```
Small Window (5k tokens):          Large Window (50k tokens):
┌────────┐                        ┌────────────────────────┐
│ Recent │                        │                        │
│  Only  │                        │   Most History Kept    │
└────────┘                        └────────────────────────┘
 Aggressive                        Minimal Trimming
 Max Savings                       Better Context
 Risk: Lost Context                Higher Cost
```