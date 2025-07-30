# Data Models Phase 2 - Tasks

**Last Updated**: July 30, 2025
**Overall Progress**: 5% Complete

## Overview

This document outlines the specific tasks for implementing Phase 2 of the data model refactoring.

**Current Status**: Phase 1 models are implemented but Phase 2 (component-specific models) has minimal progress. Only Reporter has been updated to support BrowserTestResult.

## Task Breakdown by Component

### 1. ConfigManager Refactoring

#### 1.1 Create Configuration Models (8 hours) ❌ NOT STARTED
- [ ] Create `browser_copilot/models/config.py`
- [ ] Implement ViewportConfig model with validation
- [ ] Implement BrowserConfig model with browser validation
- [ ] Implement ProviderConfig model with provider validation
- [ ] Implement OptimizationConfig model
- [ ] Implement ExecutionConfig model
- [ ] Implement StorageConfig model
- [ ] Implement AppConfig model with layer merging
- [ ] Add serialization methods to all config models

**Note**: ConfigManager still uses dictionaries exclusively

#### 1.2 Write Config Model Tests (6 hours)
- [ ] Test ViewportConfig validation (positive/negative dimensions)
- [ ] Test BrowserConfig validation (supported browsers)
- [ ] Test ProviderConfig validation (required fields)
- [ ] Test OptimizationConfig validation (compression levels)
- [ ] Test AppConfig layer merging (CLI > env > file > defaults)
- [ ] Test serialization/deserialization round trips
- [ ] Property-based tests with Hypothesis

#### 1.3 Update ConfigManager (4 hours)
- [ ] Add AppConfig as internal representation
- [ ] Implement model-based load() method
- [ ] Maintain backward-compatible get() method
- [ ] Update merge logic to work with models
- [ ] Add migration from dict to model format
- [ ] Add deprecation warnings for dict access

#### 1.4 Update ConfigManager Tests (2 hours)
- [ ] Update existing tests to verify compatibility
- [ ] Add tests for model-based interface
- [ ] Test migration scenarios
- [ ] Test deprecation warnings

### 2. VerboseLogger Refactoring

#### 2.1 Create Logging Models (6 hours) ❌ NOT STARTED
- [ ] Create `browser_copilot/models/logging.py`
- [ ] Implement LogLevel and StepType enums
- [ ] ~~Implement ExecutionStep model~~ Already exists in models/execution.py
- [ ] Implement ToolCall model with result truncation
- [ ] Implement TokenUsageLog model
- [ ] Implement ErrorLog model
- [ ] Implement LogSession model with aggregations
- [ ] Add JSON serialization for all models

**Note**: VerboseLogger uses dictionaries and string formatting

#### 2.2 Write Logging Model Tests (4 hours)
- [ ] Test ExecutionStep creation and validation
- [ ] Test ToolCall result truncation
- [ ] Test TokenUsageLog calculations
- [ ] Test LogSession aggregations
- [ ] Test serialization with various data types
- [ ] Test model relationships

#### 2.3 Update VerboseLogger (6 hours)
- [ ] Replace dict storage with model instances
- [ ] Update log_step() to create ExecutionStep
- [ ] Update log_tool_call() to create ToolCall
- [ ] Update log_token_usage() to create TokenUsageLog
- [ ] Update log_error() to create ErrorLog
- [ ] Update get_execution_summary() to use LogSession
- [ ] Maintain backward-compatible interfaces

#### 2.4 Update Logger Tests (2 hours)
- [ ] Update tests for model-based logging
- [ ] Verify log file format compatibility
- [ ] Test summary generation
- [ ] Test callback integration

### 3. TokenOptimizer Refactoring

#### 3.1 Create Optimization Models (3 hours) ⚠️ PARTIALLY EXISTS
- [ ] ~~Create `browser_copilot/models/optimization.py`~~
- [ ] Implement OptimizationStrategy enum
- [x] ~~Implement OptimizationMetrics model~~ Exists in components/models.py
- [ ] Implement CostAnalysis model
- [ ] Implement OptimizationResult model
- [ ] Add calculated properties

**Note**: OptimizationMetrics exists but in components/models.py, not in models/

#### 3.2 Write Optimization Model Tests (2 hours)
- [ ] Test metrics calculations
- [ ] Test cost analysis calculations
- [ ] Test edge cases (zero tokens, etc.)
- [ ] Test serialization

#### 3.3 Update TokenOptimizer (4 hours)
- [ ] Replace dict metrics with OptimizationMetrics
- [ ] Update optimize_prompt() to return OptimizationResult
- [ ] Update get_metrics() to return model
- [ ] Update estimate_cost_savings() to return CostAnalysis
- [ ] Maintain backward compatibility

#### 3.4 Update Optimizer Tests (2 hours)
- [ ] Update tests for model returns
- [ ] Test metric accuracy
- [ ] Test cost calculations
- [ ] Verify optimization strategies

### 4. Reporter Refactoring

#### 4.1 Update Reporter Implementation (3 hours) ✅ COMPLETED
- [x] Update print_results() to use BrowserTestResult model
- [x] Update save_results() to use model serialization
- [x] Update generate_summary() to use model properties
- [x] Update generate_markdown_report() to use model
- [x] Update create_html_report() to use model
- [x] ~~Remove all dict[str, Any] assumptions~~ Supports both for compatibility

**Note**: Reporter already supports both dict and BrowserTestResult

#### 4.2 Update Reporter Tests (2 hours) ❌ NOT VERIFIED
- [ ] Update test fixtures to use BrowserTestResult
- [ ] Verify output format compatibility
- [ ] Test with various result scenarios
- [ ] Test error handling

**Note**: Need to verify if reporter tests exist and use models

### 5. WizardState Enhancement

#### 5.1 Create Wizard Models (2 hours) ❌ NOT STARTED
- [ ] Create `browser_copilot/models/wizard.py`
- [ ] Implement WizardHistoryEntry model
- [ ] Implement WizardConfig model
- [ ] Add conversion methods

**Note**: WizardState is a dataclass but not a SerializableModel

#### 5.2 Update WizardState (2 hours)
- [ ] Replace dict history with WizardHistoryEntry list
- [ ] Update to_config() to return WizardConfig
- [ ] Update save_history() to create typed entries
- [ ] Maintain compatibility

#### 5.3 Update Wizard Tests (1 hour)
- [ ] Update tests for typed history
- [ ] Test config generation
- [ ] Test state restoration

### 6. Integration and Documentation

#### 6.1 Integration Testing (4 hours)
- [ ] End-to-end test with all new models
- [ ] Test component interactions
- [ ] Performance benchmarking
- [ ] Memory usage analysis
- [ ] Cross-platform testing

#### 6.2 Documentation Updates (3 hours)
- [ ] Update API documentation
- [ ] Create migration guide
- [ ] Update code examples
- [ ] Document new model structures
- [ ] Update type hints throughout

#### 6.3 Code Quality (2 hours)
- [ ] Run mypy in strict mode
- [ ] Run ruff for linting
- [ ] Ensure 100% test coverage
- [ ] Update CHANGELOG.md

## Task Dependencies

```mermaid
graph TD
    A[Config Models] --> B[Config Tests]
    B --> C[Update ConfigManager]
    C --> D[ConfigManager Tests]

    E[Logging Models] --> F[Logging Tests]
    F --> G[Update VerboseLogger]
    G --> H[Logger Tests]

    I[Optimization Models] --> J[Optimization Tests]
    J --> K[Update TokenOptimizer]
    K --> L[Optimizer Tests]

    M[Update Reporter] --> N[Reporter Tests]

    O[Wizard Models] --> P[Update WizardState]
    P --> Q[Wizard Tests]

    D --> R[Integration Testing]
    H --> R
    L --> R
    N --> R
    Q --> R
    R --> S[Documentation]
    S --> T[Code Quality]
```

## Time Estimates

| Component | Implementation | Testing | Total | Status |
|-----------|---------------|---------|-------|--------|
| ConfigManager | 12 hours | 8 hours | 20 hours | ❌ Not Started |
| VerboseLogger | 10 hours | 6 hours | 16 hours | ❌ Not Started |
| TokenOptimizer | 7 hours | 4 hours | 11 hours | ⚠️ 10% (OptimizationMetrics exists) |
| Reporter | 3 hours | 2 hours | 5 hours | ✅ 60% (implementation done) |
| WizardState | 2 hours | 1 hour | 3 hours | ❌ Not Started |
| Integration | 4 hours | 5 hours | 9 hours | ❌ Not Started |
| **Total** | **38 hours** | **26 hours** | **64 hours** | **~5% Complete** |

## Definition of Done

- [ ] All models implement SerializableModel base class
- [ ] All models have comprehensive validation
- [ ] All models have 100% test coverage
- [ ] All components maintain backward compatibility
- [ ] All deprecation warnings are in place
- [ ] Mypy passes in strict mode
- [ ] All tests pass on Windows, macOS, and Linux
- [ ] Documentation is complete and accurate
- [ ] Performance benchmarks show no regression
- [ ] Code review completed

## Risk Mitigation

1. **Backward Compatibility Break**
   - Mitigation: Extensive compatibility testing
   - Fallback: Feature flag to disable new models

2. **Performance Degradation**
   - Mitigation: Benchmark before/after
   - Fallback: Optimize hot paths

3. **Complex Migration**
   - Mitigation: Automated migration tools
   - Fallback: Support both formats temporarily

4. **Serialization Issues**
   - Mitigation: Round-trip testing
   - Fallback: Custom serializers

## Success Metrics

1. **Code Quality**
   - Zero mypy errors ❓ (not verified)
   - 100% test coverage ❌ (no model tests)
   - No ruff violations ❓ (not verified)

2. **Performance**
   - No increase in memory usage ❓ (not measured)
   - No increase in execution time ❓ (not measured)
   - Efficient serialization ✅ (models have efficient to_dict)

3. **Developer Experience**
   - IDE autocomplete works ✅ (dataclasses provide this)
   - Clear error messages ⚠️ (basic validation only)
   - Easy to understand models ✅ (clean structure)

4. **Compatibility**
   - All existing code works ✅ (Reporter supports both)
   - Smooth migration path ⚠️ (only Reporter migrated)
   - Clear deprecation timeline ❌ (no deprecation strategy)

## Current State Analysis

### What Exists from Phase 2
1. **Reporter Integration**: Already supports both dict and BrowserTestResult
2. **OptimizationMetrics**: Exists in components/models.py
3. **Base Infrastructure**: Phase 1 models ready for Phase 2 to build on

### What's Missing
1. **Config Models**: No typed configuration models
2. **Logging Models**: VerboseLogger still uses dicts
3. **Optimization Models**: TokenOptimizer uses dicts
4. **Wizard Models**: WizardState not using SerializableModel
5. **Tests**: No tests for any Phase 2 components

### Dependencies on Phase 1
- Phase 1 models exist but aren't integrated into core.py
- Should Phase 2 wait for Phase 1 integration?
- Or proceed with component models independently?

### Recommendation
Phase 2 appears **BLOCKED** by:
1. Phase 1 integration not complete
2. No clear migration strategy
3. Higher priority work on HIL and testing

Suggest completing Phase 1 integration before starting Phase 2.
