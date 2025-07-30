# Code Cleanup Design

**Date**: July 30, 2025
**Version**: 1.0

## Overview

This document provides the detailed design for cleaning up the Browser Copilot codebase, focusing on removing unused code and consolidating duplicate implementations.

## Inventory of Unused Code

### 1. Unused Components (`browser_copilot/components/`)

| Component | Status | Tests | Decision | Rationale |
|-----------|--------|-------|----------|-----------|
| `llm_manager.py` | Implemented, not used | 15 tests | **REMOVE** | ModelForge handles LLM management |
| `browser_config.py` | Implemented, not used | 21 tests | **REMOVE** | Logic exists in core.py |
| `prompt_builder.py` | Implemented, not used | 14 tests | **REMOVE** | Prompt building in core.py |
| `test_executor.py` | Implemented, not used | 14 tests | **REMOVE** | Execution logic in core.py |
| `result_analyzer.py` | Implemented, not used | 18 tests | **REMOVE** | Analysis in core.py |
| `token_metrics.py` | Implemented, not used | 13 tests | **REMOVE** | Telemetry handles metrics |
| `models.py` | Duplicate of `/models` | N/A | **REMOVE** | Use `/models` directory |
| `exceptions.py` | Basic hierarchy only | N/A | **KEEP** | May be useful for future |

**Total to remove**: 7 files, 95 tests

### 2. Duplicate Models

| Location | Purpose | Decision |
|----------|---------|----------|
| `/browser_copilot/models/` | New model system | **KEEP** - Well structured |
| `/browser_copilot/components/models.py` | Component models | **REMOVE** - Duplicate |

### 3. Dead Experimental Code

| Code | Location | Decision |
|------|----------|----------|
| HIL pattern detection | Various comments/drafts | **REMOVE** - Replaced by tools |
| Old config management | Legacy in core.py | **REMOVE** - Using CLI args |
| Unused imports | Throughout codebase | **REMOVE** - Clean up |

## Consolidation Strategy

### Models Consolidation

```python
# Current duplicate structure:
browser_copilot/
├── models/           # KEEP THIS
│   ├── base.py
│   ├── execution.py
│   ├── metrics.py
│   └── results.py
└── components/
    └── models.py     # REMOVE THIS
```

### Core.py Simplification

Instead of integrating unused components, we'll:
1. Keep current working implementation
2. Extract only proven patterns from components
3. Reduce file size through better organization

## Migration Plan

### Phase 1: Create Archive (Day 1)
```bash
# Create archive branch
git checkout -b archive/unused-components-2025-07-30
git add .
git commit -m "Archive: Snapshot before code cleanup"
git push origin archive/unused-components-2025-07-30
```

### Phase 2: Remove Unused Code (Day 2-3)

1. **Remove components directory**
   ```bash
   rm -rf browser_copilot/components/
   rm -rf tests/components/
   ```

2. **Clean up imports**
   - Remove any references to components
   - Update type hints
   - Fix any broken imports

3. **Remove experimental code**
   - Search for TODO/FIXME related to old approaches
   - Remove commented-out code blocks
   - Clean up unused constants

### Phase 3: Consolidate Models (Day 4-5)

1. **Ensure `/models` is complete**
   - Verify all needed types exist
   - Add any missing models from components
   - Update docstrings

2. **Update all imports**
   ```python
   # Change from:
   from browser_copilot.components.models import TestResult
   # To:
   from browser_copilot.models.results import BrowserTestResult
   ```

### Phase 4: Optimize Core.py (Day 6-7)

1. **Extract constants**
   ```python
   # Create browser_copilot/constants.py
   DEFAULT_TIMEOUT = 30000
   DEFAULT_INSTRUCTIONS = "..."
   ```

2. **Extract utilities**
   ```python
   # Create browser_copilot/utils/validation.py
   def validate_browser_name(name: str) -> str:
       ...
   ```

3. **Improve organization**
   - Group related methods
   - Extract helper functions
   - Reduce method complexity

## Validation Strategy

### Automated Testing
1. Run full test suite after each phase
2. Ensure 100% of existing tests pass
3. Check test coverage doesn't decrease

### Manual Testing
1. Test each example scenario
2. Verify CLI commands work
3. Check all output formats

### Performance Testing
```bash
# Before cleanup
python benchmark.py --baseline

# After cleanup
python benchmark.py --compare baseline
```

## Rollback Plan

If issues discovered post-cleanup:

1. **Immediate rollback**
   ```bash
   git revert <cleanup-commit>
   ```

2. **Restore from archive**
   ```bash
   git checkout archive/unused-components-2025-07-30 -- browser_copilot/components/
   ```

3. **Selective restoration**
   - Cherry-pick specific components if needed
   - Re-integrate with careful testing

## Code Cleanup Patterns

### Pattern 1: Remove Entire Unused Module
```python
# Before: Unused component with tests
browser_copilot/components/feature.py
tests/components/test_feature.py

# After: Completely removed
# (archived in branch)
```

### Pattern 2: Consolidate Duplicate Code
```python
# Before: Two implementations
browser_copilot/components/validator.py
browser_copilot/utils/validation.py

# After: Single implementation
browser_copilot/utils/validation.py  # Merged best of both
```

### Pattern 3: Extract from Monolith
```python
# Before: 1000+ line core.py
class BrowserPilot:
    def __init__(self):
        # 200 lines of init

    def run_test_suite(self):
        # 300 lines of logic

# After: Organized modules
browser_copilot/core.py          # <500 lines
browser_copilot/constants.py     # Extracted constants
browser_copilot/utils/parse.py   # Extracted utilities
```

## Expected Outcomes

### Metrics
- **Lines of Code**: -40% (remove ~3000 lines)
- **Number of Files**: -30% (remove ~15 files)
- **Test Files**: -20% (remove unused component tests)
- **Import Complexity**: -50% (simpler structure)

### Benefits
1. **Clarity**: No confusion about which code is active
2. **Maintainability**: Less code to maintain
3. **Performance**: Faster imports, less memory
4. **Onboarding**: Easier for new developers

## Documentation Updates

1. Update architecture diagrams
2. Remove references to components
3. Update development guide
4. Create "What's Changed" guide

## Communication Plan

1. **Team Notification**: Before starting cleanup
2. **Daily Updates**: Progress on each phase
3. **Completion Report**: Summary of changes
4. **Retrospective**: Lessons learned

## Success Validation

- [ ] All unused components removed
- [ ] No duplicate model definitions
- [ ] Core.py under 500 lines
- [ ] All tests passing
- [ ] Performance unchanged or improved
- [ ] Documentation updated
- [ ] Archive branch created
- [ ] Team informed of changes
