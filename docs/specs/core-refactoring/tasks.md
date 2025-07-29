# Core.py Refactoring Implementation Tasks

## Overview

This document outlines the implementation tasks for refactoring `browser_copilot/core.py` into modular components. Tasks are organized in phases to ensure incremental progress and maintain stability.

## Phase 1: Foundation (Week 1)

### Task 1.1: Create Component Structure
**Priority**: High  
**Estimated Time**: 2 hours  
**Dependencies**: None

- [ ] Create `browser_copilot/components/` directory
- [ ] Create `__init__.py` files for module structure
- [ ] Set up base exception classes in `components/exceptions.py`
- [ ] Create data models in `components/models.py`

```bash
browser_copilot/
├── components/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── models.py
│   ├── llm_manager.py
│   ├── browser_config.py
│   ├── test_executor.py
│   ├── prompt_builder.py
│   ├── result_analyzer.py
│   └── token_metrics.py
```

### Task 1.2: Extract Data Models
**Priority**: High  
**Estimated Time**: 3 hours  
**Dependencies**: Task 1.1

- [ ] Define `ExecutionStep` dataclass
- [ ] Define `ExecutionResult` dataclass
- [ ] Define `ModelMetadata` dataclass
- [ ] Define `BrowserOptions` dataclass
- [ ] Define `TestResult` dataclass
- [ ] Define `TokenMetrics` dataclass
- [ ] Define `OptimizationMetrics` dataclass

### Task 1.3: Implement LLMManager
**Priority**: High  
**Estimated Time**: 4 hours  
**Dependencies**: Task 1.2

- [ ] Extract LLM initialization logic from `BrowserPilot.__init__`
- [ ] Implement `create_llm()` method
- [ ] Implement `get_model_metadata()` method
- [ ] Add error handling for provider issues
- [ ] Write unit tests for LLMManager

**Test Checklist**:
- [ ] Test successful LLM creation
- [ ] Test invalid provider handling
- [ ] Test callback integration
- [ ] Test metadata retrieval

## Phase 2: Core Components (Week 1-2)

### Task 2.1: Implement BrowserConfigBuilder
**Priority**: High  
**Estimated Time**: 4 hours  
**Dependencies**: Task 1.2

- [ ] Extract browser validation logic
- [ ] Extract MCP args building logic
- [ ] Implement `validate_browser()` method
- [ ] Implement `build_mcp_args()` method
- [ ] Implement `create_session_directory()` method
- [ ] Implement `get_server_params()` method
- [ ] Write comprehensive unit tests

**Test Checklist**:
- [ ] Test browser name validation
- [ ] Test browser alias mapping
- [ ] Test MCP args for all options
- [ ] Test session directory creation

### Task 2.2: Implement PromptBuilder
**Priority**: High  
**Estimated Time**: 3 hours  
**Dependencies**: Task 1.2

- [ ] Extract prompt building logic
- [ ] Extract test name extraction logic
- [ ] Implement `build()` method
- [ ] Implement `optimize()` method
- [ ] Implement `extract_test_name()` method
- [ ] Create prompt template constants
- [ ] Write unit tests

**Test Checklist**:
- [ ] Test basic prompt building
- [ ] Test with custom system prompt
- [ ] Test optimization integration
- [ ] Test name extraction edge cases

### Task 2.3: Implement TestExecutor
**Priority**: High  
**Estimated Time**: 5 hours  
**Dependencies**: Task 1.2

- [ ] Extract test execution logic
- [ ] Extract step processing logic
- [ ] Implement `execute()` method
- [ ] Implement `_process_chunk()` method
- [ ] Implement `_extract_steps()` method
- [ ] Add timeout handling
- [ ] Add verbose mode support
- [ ] Write unit tests with mocked agent

**Test Checklist**:
- [ ] Test successful execution
- [ ] Test timeout handling
- [ ] Test step extraction
- [ ] Test verbose output

## Phase 3: Analysis Components (Week 2)

### Task 3.1: Implement ResultAnalyzer
**Priority**: High  
**Estimated Time**: 3 hours  
**Dependencies**: Task 1.2

- [ ] Extract success checking logic
- [ ] Extract report parsing logic
- [ ] Implement `analyze()` method
- [ ] Implement `check_success()` method
- [ ] Implement `_has_valid_report()` method
- [ ] Define success/failure patterns
- [ ] Write unit tests

**Test Checklist**:
- [ ] Test various success patterns
- [ ] Test failure detection
- [ ] Test edge cases (empty report, malformed)
- [ ] Test result building

### Task 3.2: Implement TokenMetricsCollector
**Priority**: Medium  
**Estimated Time**: 4 hours  
**Dependencies**: Task 1.2, Task 1.3

- [ ] Extract token usage logic
- [ ] Extract cost calculation logic
- [ ] Implement `collect()` method
- [ ] Implement `_extract_from_telemetry()` method
- [ ] Implement `_calculate_context_usage()` method
- [ ] Implement `_calculate_optimization_savings()` method
- [ ] Write unit tests

**Test Checklist**:
- [ ] Test telemetry extraction
- [ ] Test cost calculations
- [ ] Test context usage percentages
- [ ] Test optimization metrics

## Phase 4: Integration (Week 2-3)

### Task 4.1: Refactor BrowserPilot - Part 1
**Priority**: Critical  
**Estimated Time**: 6 hours  
**Dependencies**: All Phase 1-3 tasks

- [ ] Update imports to use new components
- [ ] Replace initialization logic with component creation
- [ ] Update `__init__` to use LLMManager
- [ ] Add component initialization methods
- [ ] Ensure backward compatibility
- [ ] Run existing test suite

### Task 4.2: Refactor BrowserPilot - Part 2
**Priority**: Critical  
**Estimated Time**: 6 hours  
**Dependencies**: Task 4.1

- [ ] Replace `run_test_suite` implementation
- [ ] Use BrowserConfigBuilder for setup
- [ ] Use PromptBuilder for prompt creation
- [ ] Use TestExecutor for execution
- [ ] Use ResultAnalyzer for analysis
- [ ] Use TokenMetricsCollector for metrics
- [ ] Ensure all existing tests pass

### Task 4.3: Integration Testing
**Priority**: Critical  
**Estimated Time**: 4 hours  
**Dependencies**: Task 4.2

- [ ] Create integration test suite
- [ ] Test full execution flow
- [ ] Test error propagation
- [ ] Test component interactions
- [ ] Performance benchmarking
- [ ] Memory usage testing

## Phase 5: Cleanup and Documentation (Week 3)

### Task 5.1: Remove Old Code
**Priority**: Medium  
**Estimated Time**: 2 hours  
**Dependencies**: Task 4.3

- [ ] Remove extracted methods from core.py
- [ ] Clean up imports
- [ ] Remove temporary compatibility code
- [ ] Update type hints
- [ ] Run linters and fix issues

### Task 5.2: Update Documentation
**Priority**: High  
**Estimated Time**: 3 hours  
**Dependencies**: Task 5.1

- [ ] Update component docstrings
- [ ] Create architecture documentation
- [ ] Update README with new structure
- [ ] Add migration guide
- [ ] Document new testing approach

### Task 5.3: Performance Optimization
**Priority**: Medium  
**Estimated Time**: 4 hours  
**Dependencies**: Task 5.1

- [ ] Profile component performance
- [ ] Optimize hot paths
- [ ] Add caching where beneficial
- [ ] Reduce object creation overhead
- [ ] Validate performance metrics

## Phase 6: Advanced Features (Week 4)

### Task 6.1: Add Component Interfaces
**Priority**: Low  
**Estimated Time**: 3 hours  
**Dependencies**: Task 5.1

- [ ] Create Protocol definitions
- [ ] Add abstract base classes
- [ ] Update components to implement interfaces
- [ ] Add type checking for protocols
- [ ] Document interface contracts

### Task 6.2: Add Telemetry Enhancements
**Priority**: Low  
**Estimated Time**: 3 hours  
**Dependencies**: Task 5.1

- [ ] Add component-level metrics
- [ ] Track execution phases
- [ ] Add performance counters
- [ ] Create metrics dashboard
- [ ] Document telemetry features

### Task 6.3: Add Plugin Support
**Priority**: Low  
**Estimated Time**: 5 hours  
**Dependencies**: Task 6.1

- [ ] Design plugin architecture
- [ ] Add plugin loading mechanism
- [ ] Create example plugins
- [ ] Add plugin documentation
- [ ] Test plugin functionality

## Testing Strategy

### Unit Test Coverage Goals

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| LLMManager | 95% | High |
| BrowserConfigBuilder | 95% | High |
| PromptBuilder | 90% | High |
| TestExecutor | 90% | High |
| ResultAnalyzer | 95% | High |
| TokenMetricsCollector | 85% | Medium |
| BrowserPilot | 90% | Critical |

### Test Execution Plan

1. **Before Each PR**: Run unit tests for modified components
2. **After Each Phase**: Run full test suite
3. **Before Release**: Run performance benchmarks
4. **Weekly**: Run integration tests on all platforms

## Risk Mitigation

### High-Risk Tasks

1. **Task 4.1-4.2**: Refactoring BrowserPilot
   - Mitigation: Create comprehensive backup, work in feature branch
   - Rollback: Git revert if tests fail

2. **Task 2.3**: TestExecutor implementation  
   - Mitigation: Extensive mocking, edge case testing
   - Rollback: Keep old execution logic until stable

3. **Task 4.3**: Integration testing
   - Mitigation: Run on multiple platforms early
   - Rollback: Identify issues before merging

## Success Metrics

### Code Quality Metrics

- [ ] Cyclomatic complexity ≤ 10 per method
- [ ] Method length ≤ 50 lines
- [ ] Class length ≤ 300 lines
- [ ] Test coverage ≥ 90%
- [ ] Zero high-severity linting issues

### Performance Metrics

- [ ] Test execution time within 10% of baseline
- [ ] Memory usage within 5% of baseline
- [ ] No increase in token usage
- [ ] Startup time unchanged

### Deliverables Checklist

- [ ] All components implemented and tested
- [ ] Core.py reduced to <200 lines
- [ ] All existing tests passing
- [ ] Documentation updated
- [ ] Performance validated
- [ ] Code review completed
- [ ] Migration guide created

## Timeline Summary

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| 1 | Foundation & Core | LLMManager, BrowserConfigBuilder, Models |
| 2 | Components & Analysis | All components implemented |
| 3 | Integration & Cleanup | Refactored BrowserPilot, Documentation |
| 4 | Polish & Features | Optimizations, Interfaces, Plugins |

## Notes for Implementation

1. **Test-First Development**: Write tests before implementation
2. **Incremental Changes**: Small, reviewable PRs
3. **Backward Compatibility**: No breaking changes to public API
4. **Documentation**: Update as you go, not after
5. **Performance**: Measure before and after each phase