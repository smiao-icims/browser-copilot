# Data Model Refactoring Requirements

## 1. Overview

Currently, Browser Copilot uses dictionaries extensively for data models, particularly for test results and metadata. This refactoring aims to replace these untyped dictionaries with strongly-typed data classes while maintaining backward compatibility.

## 2. Problem Statement

### Current Issues

1. **Type Safety**: Dict[str, Any] provides no compile-time type checking
2. **Documentation**: Dictionary structure is not self-documenting
3. **Validation**: No automatic validation of required fields or value constraints
4. **Refactoring Risk**: Changing dictionary keys requires manual search and replace
5. **IDE Support**: Limited autocomplete and type hints for dictionary access
6. **Error Prone**: Typos in dictionary keys cause runtime errors

### Example Problem Areas

```python
# Current: No type safety
result = {
    "success": True,
    "test_name": "Login Test",
    "duration_seconds": 10.5,  # Could accidentally use "duration" elsewhere
    # Easy to forget fields or misspell keys
}

# Accessing:
duration = result["duration_seconds"]  # KeyError if typo
duration = result.get("duration_second")  # Silent None if typo
```

## 3. Goals

### 3.1 Primary Goals

1. **Type Safety**: Full static type checking for all data models
2. **Backward Compatibility**: Existing API consumers must continue working
3. **Developer Experience**: Better IDE support and documentation
4. **Validation**: Runtime validation of data constraints
5. **Maintainability**: Easier to refactor and extend

### 3.2 Success Criteria

- All public APIs maintain dictionary interfaces where currently exposed
- Zero breaking changes for existing users
- 100% type coverage for new data models
- Validation prevents invalid data states
- Performance impact < 5% for serialization/deserialization

## 4. Scope

### 4.1 In Scope

1. **Test Results**: The main result dictionary from `run_test_suite()`
2. **Token Metrics**: Token usage and cost information
3. **Execution Metadata**: Steps, timings, and execution details
4. **Test Metadata**: Internal metadata passed between components
5. **Configuration Data**: Model configurations and options

### 4.2 Out of Scope

1. **External APIs**: MCP protocol messages (remain as-is)
2. **LangChain Objects**: External library objects
3. **Storage Formats**: JSON/YAML file formats (backward compatible via serialization)
4. **CLI Arguments**: Command-line interfaces remain unchanged

## 5. Requirements

### 5.1 Functional Requirements

#### FR-1: Data Model Definition
- Each dictionary-based data structure must have a corresponding data class
- Data classes must use Python 3.10+ type annotations
- Optional fields must be clearly marked with appropriate defaults

#### FR-2: Backward Compatibility
- All existing public methods returning dicts must continue to do so
- New data classes must provide `to_dict()` methods
- Dictionary interfaces must maintain exact same keys and structure

#### FR-3: Validation
- Required fields must be validated at construction time
- Numeric fields must support min/max constraints
- String fields must support length and pattern constraints
- Invalid data must raise clear, actionable exceptions

#### FR-4: Serialization
- Data models must be JSON serializable
- Support for custom serialization of complex types (datetime, Path)
- Round-trip serialization must preserve all data

#### FR-5: Factory Methods
- Provide convenient factory methods for common construction patterns
- Support building from existing dictionaries
- Support partial construction with defaults

### 5.2 Non-Functional Requirements

#### NFR-1: Performance
- Model instantiation overhead < 1ms for typical data
- Serialization performance within 10% of dict operations
- No significant memory overhead vs dictionaries

#### NFR-2: Developer Experience
- All fields must have descriptive docstrings
- IDE autocomplete must work for all model fields
- Type checkers (mypy, pyright) must fully understand types

#### NFR-3: Testing
- 100% test coverage for data models
- Property-based testing for validation rules
- Serialization round-trip tests

#### NFR-4: Documentation
- Auto-generated API documentation from type hints
- Migration guide for internal developers
- Examples of common usage patterns

## 6. Technical Constraints

### 6.1 Technology Choices

- **Primary**: Python dataclasses (stdlib, zero dependencies)
- **Validation**: Pydantic for models requiring complex validation
- **Serialization**: Built-in dataclasses.asdict() with custom encoder
- **Type Checking**: Compatible with mypy strict mode

### 6.2 Compatibility Requirements

- Python 3.10+ (for modern type hints)
- Must work with existing ModelForge integration
- Must serialize to formats compatible with storage layer
- Must work with pytest fixtures and mocks

## 7. Migration Strategy

### 7.1 Phased Approach

1. **Phase 1**: Create new data models alongside existing code
2. **Phase 2**: Update internal code to use data models
3. **Phase 3**: Add deprecation notices to dict-based internals
4. **Phase 4**: Remove deprecated code (major version bump)

### 7.2 Compatibility Layer

```python
class BrowserTestResult:
    # ... dataclass fields ...

    def to_dict(self) -> dict[str, Any]:
        """Convert to legacy dictionary format"""
        return {
            "success": self.success,
            "duration_seconds": self.duration,  # Map to old key
            # ... other mappings ...
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BrowserTestResult":
        """Construct from legacy dictionary"""
        return cls(
            success=data["success"],
            duration=data.get("duration_seconds", data.get("duration", 0)),
            # ... handle variations ...
        )
```

## 8. Risks and Mitigations

### 8.1 Breaking Changes

**Risk**: Accidentally breaking existing integrations
**Mitigation**:
- Comprehensive test suite before refactoring
- Canary testing with real usage patterns
- Feature flag for gradual rollout

### 8.2 Performance Regression

**Risk**: Data classes slower than dictionaries
**Mitigation**:
- Benchmark critical paths before/after
- Use `__slots__` for frequently created objects
- Profile and optimize hot paths

### 8.3 Complexity Increase

**Risk**: Over-engineering simple data structures
**Mitigation**:
- Start with dataclasses, only add Pydantic where needed
- Keep models focused and single-purpose
- Regular code review for complexity

## 9. Acceptance Criteria

### 9.1 Technical Criteria

- [ ] All identified dictionaries replaced with data models
- [ ] 100% backward compatibility (all tests pass)
- [ ] Type coverage > 95% for affected modules
- [ ] Performance benchmarks within acceptable range
- [ ] Documentation complete and reviewed

### 9.2 Quality Criteria

- [ ] No new mypy errors in strict mode
- [ ] All public APIs documented with types
- [ ] Migration guide approved by team
- [ ] Code review passed by senior developers

## 10. Future Considerations

### 10.1 API Evolution

- Consider GraphQL/REST API generation from models
- Explore automatic OpenAPI schema generation
- Plan for versioned data models

### 10.2 Advanced Features

- Immutable data models for thread safety
- Computed properties with caching
- Change tracking for audit logs
- Automatic schema migration support
