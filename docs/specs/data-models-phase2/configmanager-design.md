# ConfigManager Data Model Design

## Current State Analysis

### Problems with Current Implementation

1. **No Type Safety**: Configuration is stored as `dict[str, Any]`
2. **Scattered Validation**: Validation logic spread across multiple methods
3. **Complex Merging**: Layer merging without structure guarantees
4. **Poor IDE Support**: No autocomplete for configuration keys
5. **Error-Prone Access**: String-based key access with typos

### Current Usage Patterns

```python
# Current dict-based usage
config = config_manager.load()
model = config.get("model", "gpt-4")
headless = config.get("headless", True)
viewport = config.get("viewport", {"width": 1920, "height": 1080})
```

## Proposed Model Design

### Model Hierarchy

```python
AppConfig
├── ProviderConfig
│   ├── provider: str
│   ├── model: str
│   └── api_key: Optional[str]
├── BrowserConfig
│   ├── browser: str
│   ├── headless: bool
│   └── viewport: ViewportConfig
├── OptimizationConfig
│   ├── enabled: bool
│   ├── compression_level: str
│   └── skip_screenshots: bool
├── ExecutionConfig
│   ├── retry_count: int
│   └── continue_on_error: bool
└── StorageConfig
    ├── output_dir: str
    └── keep_artifacts: bool
```

### Configuration Layers

1. **CLI Arguments** (highest priority)
2. **Environment Variables**
3. **Configuration File**
4. **Defaults** (lowest priority)

### Layer Merging Strategy

```python
@classmethod
def from_layers(cls,
               cli_args: Dict[str, Any],
               env_vars: Dict[str, Any],
               config_file: Dict[str, Any],
               defaults: Dict[str, Any]) -> 'AppConfig':
    """
    Merge configuration layers with proper precedence.

    Priority: CLI > Environment > File > Defaults
    """
    # Deep merge implementation
    merged = deep_merge(defaults, config_file, env_vars, cli_args)

    # Convert to nested models
    return cls(
        provider=ProviderConfig.from_dict(merged['provider']),
        browser=BrowserConfig.from_dict(merged.get('browser', {})),
        optimization=OptimizationConfig.from_dict(merged.get('optimization', {})),
        execution=ExecutionConfig.from_dict(merged.get('execution', {})),
        storage=StorageConfig.from_dict(merged.get('storage', {}))
    )
```

## Validation Strategy

### Field-Level Validation

```python
@dataclass
class BrowserConfig(SerializableModel):
    browser: str = "chromium"

    def __post_init__(self):
        if self.browser not in SUPPORTED_BROWSERS:
            raise ValueError(
                f"Unsupported browser: {self.browser}. "
                f"Supported: {', '.join(SUPPORTED_BROWSERS)}"
            )
```

### Cross-Field Validation

```python
@dataclass
class ProviderConfig(SerializableModel):
    provider: str
    model: str
    api_key: Optional[str] = None

    def validate(self):
        if self.provider != "github_copilot" and not self.api_key:
            raise ValueError(f"API key required for provider: {self.provider}")
```

## Backward Compatibility

### Dict-Like Interface

```python
class ConfigManager:
    def get(self, key: str, default: Any = None) -> Any:
        """Legacy dict-like access with deprecation warning."""
        warnings.warn(
            f"Dict-style config access is deprecated. Use config.{key} instead.",
            DeprecationWarning,
            stacklevel=2
        )

        # Map string keys to model attributes
        if '.' in key:
            # Handle nested access like "browser.headless"
            parts = key.split('.')
            value = self._config
            for part in parts:
                value = getattr(value, part, None)
                if value is None:
                    return default
            return value

        return getattr(self._config, key, default)
```

### Migration Helper

```python
class ConfigMigrator:
    """Helps migrate from dict to model-based config."""

    @staticmethod
    def migrate_dict_config(old_config: Dict[str, Any]) -> AppConfig:
        """Convert old dict config to new model format."""
        # Handle old key names
        if 'llm_provider' in old_config:
            old_config['provider'] = old_config.pop('llm_provider')

        # Handle flat to nested conversion
        provider_config = {
            'provider': old_config.pop('provider', None),
            'model': old_config.pop('model', None),
            'api_key': old_config.pop('api_key', None)
        }

        return AppConfig.from_dict({
            'provider': provider_config,
            **old_config
        })
```

## Usage Examples

### New Model-Based Usage

```python
# Type-safe access
config = config_manager.load()
print(config.provider.model)  # IDE autocomplete works!
print(config.browser.viewport.width)

# Validation at construction
try:
    config.browser.browser = "safari"  # Raises ValueError
except ValueError as e:
    print(f"Invalid browser: {e}")
```

### During Migration

```python
# Old code continues to work
model = config_manager.get("model")  # Shows deprecation warning

# New code gets benefits
config = config_manager.get_config()  # Returns AppConfig
model = config.provider.model  # Type-safe
```

## Environment Variable Mapping

```python
ENV_MAPPING = {
    'BROWSER_COPILOT_PROVIDER': 'provider.provider',
    'BROWSER_COPILOT_MODEL': 'provider.model',
    'BROWSER_COPILOT_API_KEY': 'provider.api_key',
    'BROWSER_COPILOT_BROWSER': 'browser.browser',
    'BROWSER_COPILOT_HEADLESS': 'browser.headless',
    'BROWSER_COPILOT_VIEWPORT_WIDTH': 'browser.viewport.width',
    'BROWSER_COPILOT_VIEWPORT_HEIGHT': 'browser.viewport.height',
}
```

## Benefits

1. **Type Safety**: Catch configuration errors at development time
2. **IDE Support**: Full autocomplete and refactoring support
3. **Validation**: Centralized validation with clear error messages
4. **Documentation**: Models serve as configuration documentation
5. **Maintainability**: Easy to add new configuration options
6. **Testing**: Can use property-based testing for validation

## Migration Plan

### Phase 1: Add Models (No Breaking Changes)
1. Implement all configuration models
2. Update ConfigManager to use models internally
3. Maintain full backward compatibility

### Phase 2: Deprecation (Next Minor Release)
1. Add deprecation warnings to dict access
2. Update documentation with migration guide
3. Provide migration tooling

### Phase 3: Removal (Next Major Release)
1. Remove dict-based interface
2. Clean up compatibility code
3. Simplify implementation
