# Code Cleanup Requirements

**Date**: July 30, 2025
**Version**: 1.0
**Priority**: High
**Estimated Effort**: 2 weeks

## Executive Summary

Browser Copilot has accumulated significant technical debt through incomplete refactoring efforts. This specification outlines a systematic approach to identify and remove unused code, consolidate duplicated functionality, and establish a cleaner codebase.

## Current Problems

### 1. Unused Components (Critical)
- **8 fully implemented component files** in `browser_copilot/components/` that are never imported or used by the application
- These represent ~40 hours of development work with zero delivered value
- Components have comprehensive test suites (95 tests) but provide no functionality

### 2. Duplicate Data Models (High)
- **Two parallel model systems**:
  - `browser_copilot/models/` - New strongly-typed models (7 files)
  - `browser_copilot/components/models.py` - Component-specific models
- Neither is fully integrated with core.py
- Creates confusion about which models to use

### 3. Incomplete Refactoring (High)
- Core.py still contains all original monolithic code
- New components exist alongside old code without replacement
- No clear migration path from old to new architecture

### 4. Dead Code Accumulation (Medium)
- Experimental HIL pattern detection code (replaced by tool-based approach)
- Old configuration management code (replaced by CLI args)
- Legacy error handling patterns

## Goals

1. **Remove all unused code** that provides no current value
2. **Consolidate duplicate implementations** into single, well-tested modules
3. **Complete or abandon** partial refactoring efforts
4. **Establish clear architecture** with no ambiguity about active code
5. **Reduce codebase size** by at least 30%

## Success Criteria

- [ ] All unused components removed or integrated
- [ ] Single source of truth for each functionality
- [ ] Core.py reduced to <500 lines (currently ~1000+)
- [ ] No duplicate model definitions
- [ ] Clear documentation of active vs deprecated code
- [ ] All tests passing with simplified structure
- [ ] Performance metrics unchanged or improved

## Constraints

1. **No breaking changes** to public API
2. **Maintain all current functionality**
3. **Preserve test coverage** for active code
4. **Keep git history** for code archaeology
5. **Enable rollback** if issues discovered

## Risks

1. **Removing code that appears unused but has hidden dependencies**
   - Mitigation: Comprehensive testing before removal

2. **Breaking functionality during consolidation**
   - Mitigation: Feature flags and gradual rollout

3. **Team attachment to unused code**
   - Mitigation: Archive in separate branch before deletion

## Non-Goals

- Complete rewrite of core functionality
- Adding new features during cleanup
- Changing external interfaces
- Modifying test frameworks

## Proposed Approach

### Phase 1: Analysis and Documentation
1. Create comprehensive inventory of unused code
2. Map dependencies between components
3. Document decision for each piece of code (keep/remove/refactor)

### Phase 2: Archive and Remove
1. Create archive branch with all unused code
2. Remove unused components directory
3. Remove duplicate model definitions
4. Clean up dead experimental code

### Phase 3: Consolidation
1. Merge duplicate implementations
2. Simplify import structures
3. Update all references to use consolidated code

### Phase 4: Validation
1. Run comprehensive test suite
2. Performance benchmarking
3. Manual testing of critical paths
4. Update documentation

## Timeline

- Week 1: Analysis and planning
- Week 2: Execution and validation

## Dependencies

- No external dependencies
- Requires team alignment on cleanup decisions
- CI/CD pipeline for validation
