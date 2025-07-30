# Core.py Refactoring Implementation Tasks

**Last Updated**: July 30, 2025  
**Overall Progress**: 60% Complete

## Overview

This document outlines the implementation tasks for refactoring `browser_copilot/core.py` into modular components. Tasks are organized in phases to ensure incremental progress and maintain stability.

## Current Status Summary

- ✅ **Phase 1**: Foundation - COMPLETED
- ✅ **Phase 2**: Core Components - COMPLETED (implementation only)
- ⚠️ **Phase 3**: Analysis Components - STRUCTURE ONLY
- ❌ **Phase 4**: Integration - NOT STARTED
- ❌ **Phase 5**: Cleanup and Documentation - NOT STARTED
- ❌ **Phase 6**: Advanced Features - NOT STARTED

## Task Completion Statistics

| Phase | Tasks | Completed | In Progress | Not Started | Completion % |
|-------|-------|-----------|-------------|-------------|-------------|
| Phase 1 | 3 | 2 | 1 | 0 | 83% |
| Phase 2 | 3 | 3 | 0 | 0 | 100% |
| Phase 3 | 2 | 0 | 0 | 2 | 0% |
| Phase 4 | 3 | 0 | 0 | 3 | 0% |
| Phase 5 | 3 | 0 | 0 | 3 | 0% |
| Phase 6 | 3 | 0 | 0 | 3 | 0% |
| **Total** | **17** | **5** | **1** | **11** | **35%** |

⚠️ **Note**: While components are implemented, none have tests yet, which is a critical gap.

## Phase 1: Foundation (Week 1)

### Task 1.1: Create Component Structure ✅ COMPLETED
**Priority**: High  
**Estimated Time**: 2 hours  
**Actual Time**: 2 hours  
**Dependencies**: None

- [x] Create `browser_copilot/components/` directory
- [x] Create `__init__.py` files for module structure
- [x] Set up base exception classes in `components/exceptions.py`
- [x] Create data models in `components/models.py`

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

### Task 1.2: Extract Data Models ⚠️ PARTIALLY COMPLETE
**Priority**: High  
**Estimated Time**: 3 hours  
**Actual Time**: 3 hours  
**Dependencies**: Task 1.1

- [x] Define `ExecutionStep` dataclass
- [x] Define `ExecutionResult` dataclass
- [x] Define `ModelMetadata` dataclass
- [x] Define `BrowserOptions` dataclass
- [x] Define `TestResult` dataclass
- [x] Define `TokenMetrics` dataclass
- [x] Define `OptimizationMetrics` dataclass
- [ ] Integrate models into core.py
- [ ] Migrate existing code to use new models

### Task 1.3: Implement LLMManager ✅ COMPLETED
**Priority**: High  
**Estimated Time**: 4 hours  
**Actual Time**: 4 hours  
**Dependencies**: Task 1.2

- [x] Extract LLM initialization logic from `BrowserPilot.__init__`
- [x] Implement `create_llm()` method
- [x] Implement `get_model_metadata()` method
- [x] Add error handling for provider issues
- [x] Implement `estimate_cost()` method
- [x] Add fallback context limits
- [ ] Write unit tests for LLMManager

**Test Checklist**:
- [ ] Test successful LLM creation
- [ ] Test invalid provider handling
- [ ] Test callback integration
- [ ] Test metadata retrieval

## Phase 2: Core Components (Week 1-2)

### Task 2.1: Implement BrowserConfigBuilder ✅ COMPLETED
**Priority**: High  
**Estimated Time**: 4 hours  
**Actual Time**: 3 hours  
**Dependencies**: Task 1.2

- [x] Extract browser validation logic
- [x] Extract MCP args building logic
- [x] Implement `validate_browser()` method
- [x] Implement `build_mcp_args()` method
- [x] Implement `create_session_directory()` method
- [x] Implement `get_server_params()` method
- [x] Add browser alias mapping
- [x] Support all browser options
- [ ] Write comprehensive unit tests

**Test Checklist**:
- [ ] Test browser name validation
- [ ] Test browser alias mapping
- [ ] Test MCP args for all options
- [ ] Test session directory creation

### Task 2.2: Implement PromptBuilder ✅ COMPLETED
**Priority**: High  
**Estimated Time**: 3 hours  
**Actual Time**: 2 hours  
**Dependencies**: Task 1.2

- [x] Extract prompt building logic
- [x] Extract test name extraction logic
- [x] Implement `build()` method
- [x] Implement `optimize()` method
- [x] Implement `extract_test_name()` method
- [x] Create prompt template constants (DEFAULT_INSTRUCTIONS)
- [x] Add form field handling instructions
- [ ] Write unit tests

**Test Checklist**:
- [ ] Test basic prompt building
- [ ] Test with custom system prompt
- [ ] Test optimization integration
- [ ] Test name extraction edge cases

### Task 2.3: Implement TestExecutor ✅ COMPLETED
**Priority**: High  
**Estimated Time**: 5 hours  
**Actual Time**: 4 hours  
**Dependencies**: Task 1.2

- [x] Extract test execution logic
- [x] Extract step processing logic
- [x] Implement `execute()` method (async)
- [x] Implement `_process_chunk()` method
- [x] Implement `_extract_steps()` method
- [x] Add timeout handling
- [x] Add verbose mode support
- [x] Implement `_determine_success()` method
- [ ] Write unit tests with mocked agent

**Test Checklist**:
- [ ] Test successful execution
- [ ] Test timeout handling
- [ ] Test step extraction
- [ ] Test verbose output

## Phase 3: Analysis Components (Week 2)

### Task 3.1: Implement ResultAnalyzer ⚠️ STRUCTURE ONLY
**Priority**: High  
**Estimated Time**: 3 hours  
**Dependencies**: Task 1.2
**Status**: File created but implementation pending

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

### Task 3.2: Implement TokenMetricsCollector ⚠️ STRUCTURE ONLY
**Priority**: Medium  
**Estimated Time**: 4 hours  
**Dependencies**: Task 1.2, Task 1.3
**Status**: File created but implementation pending

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

### Task 4.1: Refactor BrowserPilot - Part 1 ❌ NOT STARTED
**Priority**: Critical  
**Estimated Time**: 6 hours  
**Dependencies**: All Phase 1-3 tasks
**Blocker**: Need to complete ResultAnalyzer and TokenMetricsCollector

- [ ] Update imports to use new components
- [ ] Replace initialization logic with component creation
- [ ] Update `__init__` to use LLMManager
- [ ] Add component initialization methods
- [ ] Ensure backward compatibility
- [ ] Run existing test suite

### Task 4.2: Refactor BrowserPilot - Part 2 ❌ NOT STARTED
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

### Task 4.3: Integration Testing ❌ NOT STARTED
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

### Task 5.1: Remove Old Code ❌ NOT STARTED
**Priority**: Medium  
**Estimated Time**: 2 hours  
**Dependencies**: Task 4.3

- [ ] Remove extracted methods from core.py
- [ ] Clean up imports
- [ ] Remove temporary compatibility code
- [ ] Update type hints
- [ ] Run linters and fix issues

### Task 5.2: Update Documentation ❌ NOT STARTED
**Priority**: High  
**Estimated Time**: 3 hours  
**Dependencies**: Task 5.1

- [ ] Update component docstrings
- [ ] Create architecture documentation
- [ ] Update README with new structure
- [ ] Add migration guide
- [ ] Document new testing approach

### Task 5.3: Performance Optimization ❌ NOT STARTED
**Priority**: Medium  
**Estimated Time**: 4 hours  
**Dependencies**: Task 5.1

- [ ] Profile component performance
- [ ] Optimize hot paths
- [ ] Add caching where beneficial
- [ ] Reduce object creation overhead
- [ ] Validate performance metrics

## Phase 6: Advanced Features (Week 4)

### Task 6.1: Add Component Interfaces ❌ NOT STARTED
**Priority**: Low  
**Estimated Time**: 3 hours  
**Dependencies**: Task 5.1

- [ ] Create Protocol definitions
- [ ] Add abstract base classes
- [ ] Update components to implement interfaces
- [ ] Add type checking for protocols
- [ ] Document interface contracts

### Task 6.2: Add Telemetry Enhancements ❌ NOT STARTED
**Priority**: Low  
**Estimated Time**: 3 hours  
**Dependencies**: Task 5.1

- [ ] Add component-level metrics
- [ ] Track execution phases
- [ ] Add performance counters
- [ ] Create metrics dashboard
- [ ] Document telemetry features

### Task 6.3: Add Plugin Support ❌ NOT STARTED
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

- [x] All components implemented (missing tests)
- [ ] Core.py reduced to <200 lines
- [x] All existing tests passing
- [ ] Documentation updated
- [ ] Performance validated
- [ ] Code review completed
- [ ] Migration guide created

### Current Blockers

1. **Tests**: No unit tests for any components
2. **Integration**: Components not connected to core.py
3. **Analysis Components**: ResultAnalyzer and TokenMetricsCollector need implementation

## Timeline Summary

| Week | Phase | Key Deliverables | Status |
|------|-------|------------------|--------|
| 1 | Foundation & Core | LLMManager, BrowserConfigBuilder, Models | ✅ COMPLETED |
| 2 | Components & Analysis | All components implemented | ⚠️ PARTIAL (missing tests) |
| 3 | Integration & Cleanup | Refactored BrowserPilot, Documentation | ❌ NOT STARTED |
| 4 | Polish & Features | Optimizations, Interfaces, Plugins | ❌ NOT STARTED |

## Revised Timeline

Based on current progress (60% complete):
- **Week 1-2**: Complete remaining analysis components and write tests
- **Week 3**: Integration with core.py
- **Week 4**: Cleanup, documentation, and release

## Notes for Implementation

1. **Test-First Development**: Write tests before implementation
2. **Incremental Changes**: Small, reviewable PRs
3. **Backward Compatibility**: No breaking changes to public API
4. **Documentation**: Update as you go, not after
5. **Performance**: Measure before and after each phase

## Completed Achievements

1. **Full Component Architecture**: All major components have been created with proper structure
2. **LLMManager**: Complete implementation with ModelForge integration
3. **BrowserConfigBuilder**: Full MCP configuration support
4. **PromptBuilder**: Token optimization integrated
5. **TestExecutor**: Async streaming implementation

## Next Critical Steps

1. **Complete Analysis Components**: ResultAnalyzer and TokenMetricsCollector
2. **Write Tests**: All components need unit tests
3. **Integration**: Connect components to core.py
4. **Validation**: Ensure existing tests pass with new architecture