# CLI Refactoring - Tasks

**Last Updated**: July 30, 2025
**Overall Progress**: 40% Complete

## 1. Overview

This document breaks down the CLI refactoring into specific tasks with clear deliverables, dependencies, and acceptance criteria.

**Current Status**: Partial refactoring has been completed with a basic cli package structure, but not the full modular architecture originally planned.

## 2. Task Breakdown

### Phase 1: Setup and Structure (Sprint 1)

#### Task 1.1: Create CLI Package Structure ⚠️ PARTIALLY COMPLETE
**Priority**: P0
**Estimate**: 2 hours
**Actual**: 1 hour
**Assignee**: TBD

- [x] Create `browser_copilot/cli/` directory
- [ ] Create subdirectories: `handlers/`, `validators/`, `loaders/`, `executors/`, `reporters/`, `formatters/`, `models/`, `utils/`
- [x] Add `__init__.py` files to all directories
- [x] Update imports in main `cli.py`

**Note**: Basic cli package created but not the full subdirectory structure

**Acceptance Criteria**:
- Package structure created
- All imports working
- No circular dependencies

#### Task 1.2: Define Data Models ❌ NOT STARTED
**Priority**: P0
**Estimate**: 3 hours
**Dependencies**: Task 1.1

- [ ] Create `cli/models/cli_models.py`
- [ ] Define `ExecutionContext` dataclass
- [ ] Define `TestResults` dataclass
- [ ] Define `ValidationResult` dataclass
- [ ] Add type hints and documentation

**Note**: Models exist in browser_copilot/models/ but not CLI-specific models

**Acceptance Criteria**:
- All models properly typed
- Serialization methods implemented
- 100% test coverage

#### Task 1.3: Create Base Test Suite
**Priority**: P0
**Estimate**: 4 hours
**Dependencies**: Task 1.1

- [ ] Create test structure mirroring CLI package
- [ ] Set up test fixtures
- [ ] Create test data files
- [ ] Implement test utilities

**Acceptance Criteria**:
- Test structure matches code structure
- Fixtures cover common scenarios
- Tests run successfully

### Phase 2: Core Components (Sprint 1-2)

#### Task 2.1: Implement Input Validator ⚠️ LOGIC EXISTS
**Priority**: P0
**Estimate**: 6 hours
**Dependencies**: Task 1.2

- [ ] Create `InputValidator` class
- [ ] Implement `validate_all()` method
- [x] Add individual validation methods (exist in parser.py):
  - [x] `_validate_path()` (in parser)
  - [x] `_validate_output_format()` (in parser)
  - [x] `_validate_browser()` (in utils)
  - [x] `_validate_viewport()` (in parser)
  - [x] `_validate_timeout()` (in parser)
- [ ] Write comprehensive tests

**Note**: Validation logic exists but scattered in parser.py and utils.py

**Acceptance Criteria**:
- All inputs validated
- Clear error messages
- Helpful suggestions
- 100% test coverage

#### Task 2.2: Implement Test Loader ✅ COMPLETED (Different Structure)
**Priority**: P0
**Estimate**: 5 hours
**Actual**: 3 hours
**Dependencies**: Task 1.2

- [x] ~~Create `TestLoader` class~~ Implemented in io/input_handler.py
- [x] Implement loading methods:
  - [x] `_load_from_file()` (read_test_file)
  - [x] `_load_from_stdin()` (read_from_stdin)
  - [ ] `_load_from_url()` (stub for future)
- [x] Add encoding support (UTF-8)
- [x] Handle large files efficiently
- [ ] Write tests for all scenarios

**Note**: Implemented as InputHandler in io package

**Acceptance Criteria**:
- All input sources working
- Encoding issues handled
- Large files supported
- Error handling comprehensive

#### Task 2.3: Extract Output Formatters ✅ COMPLETED (Different Structure)
**Priority**: P1
**Estimate**: 8 hours
**Actual**: 6 hours
**Dependencies**: Task 1.2

- [x] ~~Create base `OutputFormatter` class~~ Implemented in io/output_handler.py
- [x] Implement formatters (in OutputHandler):
  - [x] `JsonFormatter` (format_json)
  - [x] `YamlFormatter` (format_yaml)
  - [x] `MarkdownFormatter` (reporter.py)
  - [x] `HtmlFormatter` (reporter.py)
  - [x] `XmlFormatter` (format_xml)
  - [x] `JunitFormatter` (format_junit)
- [x] ~~Create `FormatterFactory`~~ Using format method dispatch
- [ ] Write tests for each formatter

**Note**: Implemented in io/output_handler.py and reporter.py

**Acceptance Criteria**:
- All formats preserved
- Output identical to current
- Easy to add new formats
- Memory efficient

### Phase 3: Execution Components (Sprint 2)

#### Task 3.1: Implement Test Executor ✅ COMPLETED
**Priority**: P0
**Estimate**: 8 hours
**Actual**: 6 hours
**Dependencies**: Task 2.1, 2.2

- [x] Create `TestExecutor` class (cli/executor.py)
- [x] Implement execution flow:
  - [x] `_create_pilot()` (in execute_test)
  - [x] `_execute_once()` (run_test_suite)
  - [x] `_handle_retry()` (retry logic)
- [x] Add timeout handling
- [x] Implement token tracking
- [ ] Write comprehensive tests

**Acceptance Criteria**:
- Clean execution flow
- Proper retry logic
- Resource cleanup guaranteed
- Token tracking accurate

#### Task 3.2: Implement Report Handler
**Priority**: P1
**Estimate**: 6 hours
**Dependencies**: Task 2.3

- [ ] Create `ReportHandler` class
- [ ] Implement report generation
- [ ] Add file writing logic
- [ ] Handle stdout output
- [ ] Save artifacts (screenshots, logs)
- [ ] Write tests

**Acceptance Criteria**:
- Reports generated correctly
- File output working
- Artifacts saved properly
- Memory efficient

#### Task 3.3: Create Test Handler
**Priority**: P0
**Estimate**: 6 hours
**Dependencies**: Tasks 2.1, 2.2, 3.1, 3.2

- [ ] Create `TestHandler` class
- [ ] Implement orchestration logic
- [ ] Add error handling
- [ ] Implement factory method
- [ ] Write integration tests

**Acceptance Criteria**:
- Clean orchestration
- All components integrated
- Error handling comprehensive
- Exit codes correct

### Phase 4: Integration (Sprint 2-3)

#### Task 4.1: Refactor run_test_async ✅ COMPLETED
**Priority**: P0
**Estimate**: 4 hours
**Actual**: 3 hours
**Dependencies**: Phase 3 complete

- [x] Create minimal `run_test_async` (cli/commands.py)
- [x] Delegate to executor module
- [x] Preserve backward compatibility
- [x] ~~Add feature flag if needed~~ Not needed

**Acceptance Criteria**:
- Function < 50 lines
- All tests still pass
- No behavior changes
- Performance maintained

#### Task 4.2: Update Error Handling
**Priority**: P1
**Estimate**: 4 hours
**Dependencies**: Task 4.1

- [ ] Integrate with custom exceptions
- [ ] Update error messages
- [ ] Add context to errors
- [ ] Test error paths

**Acceptance Criteria**:
- Better error messages
- Context included
- Suggestions provided
- All paths tested

#### Task 4.3: Integration Testing
**Priority**: P0
**Estimate**: 6 hours
**Dependencies**: Task 4.1, 4.2

- [ ] Create end-to-end tests
- [ ] Test all CLI options
- [ ] Verify output formats
- [ ] Performance benchmarks
- [ ] Memory profiling

**Acceptance Criteria**:
- All workflows tested
- No regressions
- Performance acceptable
- Memory usage stable

### Phase 5: Cleanup and Documentation (Sprint 3)

#### Task 5.1: Remove Old Code
**Priority**: P1
**Estimate**: 3 hours
**Dependencies**: Phase 4 complete

- [ ] Remove old implementation
- [ ] Clean up imports
- [ ] Remove dead code
- [ ] Update references

**Acceptance Criteria**:
- Old code removed
- All imports updated
- No dead code
- Tests still pass

#### Task 5.2: Update Documentation
**Priority**: P2
**Estimate**: 4 hours
**Dependencies**: Task 5.1

- [ ] Update architecture docs
- [ ] Document new structure
- [ ] Add developer guide
- [ ] Update API documentation

**Acceptance Criteria**:
- Docs reflect new structure
- Examples updated
- Developer guide complete
- API docs accurate

#### Task 5.3: Performance Optimization
**Priority**: P2
**Estimate**: 4 hours
**Dependencies**: Phase 4 complete

- [ ] Profile hot paths
- [ ] Optimize slow operations
- [ ] Add caching where beneficial
- [ ] Verify improvements

**Acceptance Criteria**:
- No performance regression
- Startup time < 500ms
- Memory usage stable
- Benchmarks documented

## 3. Task Dependencies

```mermaid
graph TD
    A[1.1 Package Structure] --> B[1.2 Data Models]
    A --> C[1.3 Test Suite]
    B --> D[2.1 Input Validator]
    B --> E[2.2 Test Loader]
    B --> F[2.3 Output Formatters]
    D & E --> G[3.1 Test Executor]
    F --> H[3.2 Report Handler]
    G & H --> I[3.3 Test Handler]
    I --> J[4.1 Refactor Function]
    J --> K[4.2 Error Handling]
    J --> L[4.3 Integration Tests]
    L --> M[5.1 Cleanup]
    M --> N[5.2 Documentation]
    L --> O[5.3 Performance]
```

## 4. Definition of Done

A task is complete when:
- [ ] Code implemented and working
- [ ] Unit tests written and passing
- [ ] Test coverage > 95%
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] No performance regression
- [ ] Integration tests pass

## 5. Risk Mitigation

### Risk: Breaking backward compatibility
**Mitigation**:
- Extensive integration tests
- Feature flags for rollback
- Gradual rollout

### Risk: Performance degradation
**Mitigation**:
- Benchmark before/after
- Profile critical paths
- Optimize as needed

### Risk: Complex migration
**Mitigation**:
- Small incremental changes
- Keep old code temporarily
- Thorough testing

## 6. Estimated Timeline

- **Sprint 1** (Week 1-2): Phase 1 & 2 ⚠️ PARTIALLY COMPLETE
- **Sprint 2** (Week 3-4): Phase 3 & 4 ⚠️ PARTIALLY COMPLETE
- **Sprint 3** (Week 5-6): Phase 5 & stabilization ❌ NOT STARTED

Total estimated effort: ~100 hours
Actual progress: ~40 hours (40%)

## Current Implementation Summary

### What Was Completed
1. **Basic CLI Package**: Created cli/ with parser, executor, commands, utils
2. **IO Package**: Created io/ with input_handler, output_handler, stream_handler
3. **Test Execution**: Refactored into executor.py
4. **Input/Output Handling**: Separated into dedicated handlers
5. **Command Structure**: Main entry point simplified

### What Was NOT Completed
1. **Full Modular Structure**: No subdirectories for handlers/validators/formatters
2. **CLI-Specific Models**: Still using general models
3. **Comprehensive Tests**: Limited test coverage
4. **Full Separation**: Some logic still mixed (validation in parser)
5. **Documentation**: Architecture not fully documented

### Different Approach Taken
- Instead of many subdirectories, used a flatter structure
- Created io package for input/output handling
- Kept validation logic in parser rather than separate validator
- Used existing reporter.py rather than creating new formatters
