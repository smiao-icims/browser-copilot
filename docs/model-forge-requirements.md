# Model-Forge Enhancement Requirements from Browser Copilot

## Overview
Browser Copilot needs enhanced model metadata and configuration capabilities from model-forge to provide better insights and control for QA engineers using LLM-powered test automation.

## Core Requirements

### 1. Model Metadata Exposure
Expose model capabilities and limits that are already fetched from models.dev:

#### Required Properties on LLM Object
```python
class LLM:
    # Existing properties...
    
    # New metadata properties
    @property
    def context_length(self) -> int:
        """Maximum context window in tokens"""
        pass
    
    @property
    def max_output_tokens(self) -> int:
        """Maximum output tokens the model can generate"""
        pass
    
    @property
    def supports_function_calling(self) -> bool:
        """Whether the model supports function/tool calling"""
        pass
    
    @property
    def supports_vision(self) -> bool:
        """Whether the model supports image inputs"""
        pass
    
    @property
    def model_info(self) -> dict:
        """Full model metadata from models.dev including:
        - context_length
        - max_output_tokens
        - capabilities (reasoning, multimodal, etc.)
        - pricing info
        - knowledge cutoff date
        """
        pass
```

### 2. Model Configuration Parameters
Allow setting and retrieving model parameters consistently across providers:

```python
# Setting parameters
llm = registry.get_llm("provider", "model")
llm.temperature = 0.7
llm.top_p = 0.9
llm.top_k = 40
llm.max_tokens = 2000  # Already supported by some

# Getting current values
current_temp = llm.temperature  # Should return actual value, not None
```

### 3. Provider-Agnostic Parameter Validation
```python
# Validate parameters based on model capabilities
llm.validate_parameters({
    "temperature": 0.7,
    "max_tokens": 150000  # Should raise if exceeds model limit
})
```

### 4. Cost Estimation Enhancement
```python
# Expose pricing information for better cost tracking
@property
def pricing_info(self) -> dict:
    """Returns pricing per 1M tokens:
    {
        "input_per_1m": 10.0,
        "output_per_1m": 30.0,
        "currency": "USD"
    }
    """
    pass

# Calculate estimated cost for a request
def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
    """Calculate estimated cost for given token counts"""
    pass
```

## Use Cases in Browser Copilot

### 1. Context Length Awareness
```python
# Browser Copilot can warn users about context limits
llm = registry.get_llm("github_copilot", "gpt-4o")
context_limit = llm.context_length  # 128000
if prompt_tokens > context_limit * 0.8:
    warn("Approaching context limit, consider splitting test")
```

### 2. Dynamic Model Selection
```python
# Choose model based on requirements
models = registry.list_models_with_capabilities(
    min_context_length=100000,
    supports_function_calling=True,
    max_input_cost_per_1m=15.0
)
```

### 3. Parameter Optimization
```python
# Adjust parameters based on test type
if test_type == "exploratory":
    llm.temperature = 0.7  # More creative
else:
    llm.temperature = 0.1  # More deterministic
```

## Implementation Priority

1. **High Priority** (Needed immediately):
   - `context_length` property
   - `max_output_tokens` property
   - Basic parameter support (temperature, top_p, top_k)

2. **Medium Priority** (Nice to have):
   - Full `model_info` dict with all metadata
   - Capability flags (vision, function calling)
   - Parameter validation

3. **Low Priority** (Future enhancement):
   - Cost estimation methods
   - Dynamic model discovery/filtering

## Technical Notes

- The ModelsDevClient already fetches this data from models.dev
- Need to pass this metadata through to the LLM objects
- Should cache model metadata to avoid repeated API calls
- Parameters should be provider-agnostic (model-forge handles mapping)

## Backwards Compatibility

- All new properties should be optional/have defaults
- Existing code should continue to work without changes
- Use `@property` decorators for clean API

## Example Implementation Path

1. Store model metadata in ModelForgeRegistry when creating LLMs
2. Pass metadata to LLM objects during initialization
3. Expose via properties and methods
4. Add parameter setters that work across all providers

This enhancement will make Browser Copilot more intelligent about model selection, cost management, and test optimization.