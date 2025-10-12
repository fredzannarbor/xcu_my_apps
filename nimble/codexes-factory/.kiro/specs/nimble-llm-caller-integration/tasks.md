# Nimble LLM Caller Integration Tasks

## Phase 1: Environment Setup and Package Installation

### Task 1.1: Install nimble-llm-caller Package
- [ ] Add nimble-llm-caller to requirements.txt
- [ ] Install package in development environment
- [ ] Verify installation with test imports
- [ ] Update any virtual environment configurations
- [ ] Test basic functionality with CLI tool

**Acceptance Criteria:**
- Package installs without conflicts
- All imports work correctly
- CLI test passes
- No dependency conflicts with existing packages

### Task 1.2: Create Integration Configuration
- [ ] Create `src/codexes/config/llm_config.json` configuration file
- [ ] Set up environment variables for API keys
- [ ] Create configuration validation utilities
- [ ] Test configuration loading and validation
- [ ] Document configuration options

**Acceptance Criteria:**
- Configuration file loads correctly
- API keys are properly secured
- Configuration validation works
- Clear error messages for configuration issues

## Phase 2: Integration Layer Development

### Task 2.1: Create LLM Integration Wrapper
- [ ] Create `src/codexes/core/llm_integration.py`
- [ ] Implement backward compatibility wrapper for `call_model_with_prompt`
- [ ] Implement backward compatibility wrapper for `get_responses_from_multiple_models`
- [ ] Add proper error handling and logging
- [ ] Create unit tests for integration layer

**Acceptance Criteria:**
- Existing API interfaces maintained
- All function signatures preserved
- Error handling improved
- Comprehensive logging added
- Unit tests pass

### Task 2.2: Update Core Module Imports
- [ ] Update imports in modules that use LLM functionality
- [ ] Replace direct calls to old functions with integration wrapper
- [ ] Test each module individually
- [ ] Verify no functionality regression
- [ ] Update any module-specific configurations

**Acceptance Criteria:**
- All modules import from integration layer
- No direct imports of old LLM caller
- All existing functionality works
- No performance regression
- Tests pass for all updated modules

## Phase 3: Prompt Migration

### Task 3.1: Analyze and Catalog Existing Prompts
- [ ] Scan codebase for all LLM prompts
- [ ] Document current prompt formats and usage
- [ ] Identify prompt parameters and substitutions
- [ ] Create migration mapping document
- [ ] Plan prompt organization structure

**Acceptance Criteria:**
- Complete inventory of all prompts
- Documentation of current usage patterns
- Clear migration plan for each prompt
- Organized structure for new prompt file

### Task 3.2: Create Centralized Prompt File
- [ ] Create `src/codexes/prompts/codexes_prompts.json`
- [ ] Convert all existing prompts to JSON format
- [ ] Add proper metadata and parameters
- [ ] Organize prompts by functional area
- [ ] Validate prompt structure and syntax

**Acceptance Criteria:**
- All prompts converted to JSON format
- Proper message structure and parameters
- Organized by logical groupings
- Validation passes for all prompts
- Documentation updated

### Task 3.3: Update Prompt References
- [ ] Replace hardcoded prompts with prompt key references
- [ ] Update prompt substitution calls
- [ ] Test prompt loading and formatting
- [ ] Verify all substitutions work correctly
- [ ] Update any prompt-specific error handling

**Acceptance Criteria:**
- All prompts loaded from centralized file
- Prompt substitutions work correctly
- No hardcoded prompts remain
- Error handling for missing prompts
- All tests pass

## Phase 4: Core Function Migration

### Task 4.1: Replace LLM Calling Implementation
- [ ] Update `call_model_with_prompt` implementation
- [ ] Update `get_responses_from_multiple_models` implementation
- [ ] Implement improved retry logic
- [ ] Add comprehensive error handling
- [ ] Maintain backward compatibility

**Acceptance Criteria:**
- New implementation uses nimble-llm-caller
- Improved retry logic and error handling
- Backward compatibility maintained
- Performance matches or exceeds original
- All existing tests pass

### Task 4.2: Enhance Error Handling and Logging
- [ ] Implement structured error handling
- [ ] Add comprehensive logging throughout
- [ ] Create error recovery mechanisms
- [ ] Add monitoring and metrics collection
- [ ] Update error messages and documentation

**Acceptance Criteria:**
- Structured error handling patterns
- Comprehensive logging for debugging
- Improved error recovery
- Monitoring capabilities added
- Clear error messages and documentation

## Phase 5: Module-by-Module Migration

### Task 5.1: Update High-Priority Modules
- [ ] Identify critical modules using LLM functionality
- [ ] Update `src/codexes/modules/builders/` modules
- [ ] Update `src/codexes/modules/distribution/` modules
- [ ] Test each module thoroughly
- [ ] Update module-specific tests

**Acceptance Criteria:**
- All high-priority modules updated
- No functionality regression
- Improved error handling
- All tests pass
- Performance validated

### Task 5.2: Update Remaining Modules
- [ ] Update all remaining modules using LLM functionality
- [ ] Ensure consistent patterns across codebase
- [ ] Update imports and function calls
- [ ] Test functionality thoroughly
- [ ] Update documentation

**Acceptance Criteria:**
- All modules use new integration layer
- Consistent patterns throughout codebase
- No old LLM calling code remains
- All functionality works correctly
- Documentation updated

## Phase 6: Testing and Validation

### Task 6.1: Comprehensive Testing
- [ ] Run full test suite with new implementation
- [ ] Perform integration tests with real API calls
- [ ] Conduct performance benchmarking
- [ ] Test error scenarios and recovery
- [ ] Validate all existing functionality

**Acceptance Criteria:**
- All tests pass with new implementation
- Performance meets or exceeds benchmarks
- Error handling works correctly
- No functionality regression
- Integration tests successful

### Task 6.2: User Acceptance Testing
- [ ] Test with real book pipeline workflows
- [ ] Validate LSI CSV generation functionality
- [ ] Test metadata extraction and processing
- [ ] Verify document generation works
- [ ] Test error recovery scenarios

**Acceptance Criteria:**
- All real-world workflows function correctly
- No user-facing functionality changes
- Error handling improves user experience
- Performance is acceptable
- Documentation is accurate

## Phase 7: Cleanup and Optimization

### Task 7.1: Remove Deprecated Code
- [ ] Remove old `src/codexes/core/llm_caller.py` file
- [ ] Clean up unused imports throughout codebase
- [ ] Remove duplicate functionality
- [ ] Update any remaining references
- [ ] Clean up configuration files

**Acceptance Criteria:**
- No deprecated code remains
- All imports cleaned up
- No duplicate functionality
- Configuration consolidated
- Codebase is clean and maintainable

### Task 7.2: Documentation and Training
- [ ] Update API documentation
- [ ] Create migration guide for developers
- [ ] Update examples and tutorials
- [ ] Create troubleshooting guide
- [ ] Update README and setup instructions

**Acceptance Criteria:**
- Complete API documentation
- Clear migration guide
- Updated examples and tutorials
- Comprehensive troubleshooting guide
- Easy setup for new developers

## Phase 8: Deployment and Monitoring

### Task 8.1: Production Deployment
- [ ] Deploy to staging environment
- [ ] Test in staging with real data
- [ ] Monitor performance and errors
- [ ] Deploy to production environment
- [ ] Monitor production deployment

**Acceptance Criteria:**
- Successful staging deployment
- All functionality works in staging
- Production deployment successful
- No critical errors in production
- Performance monitoring active

### Task 8.2: Post-Deployment Validation
- [ ] Monitor system performance
- [ ] Collect user feedback
- [ ] Address any issues discovered
- [ ] Optimize based on real usage
- [ ] Document lessons learned

**Acceptance Criteria:**
- System performs well in production
- User feedback is positive
- Issues addressed promptly
- Performance optimized
- Documentation complete

## Success Metrics

### Technical Metrics
- All existing functionality works through nimble-llm-caller
- Performance matches or exceeds previous implementation
- Error handling and recovery improved
- Code duplication reduced by >50%
- Test coverage maintained or improved

### User Experience Metrics
- No regression in user-facing functionality
- Improved error messages and handling
- Better logging for debugging
- Easier development and testing
- Faster development of new features

### Maintenance Metrics
- Reduced maintenance overhead
- Easier to add new LLM providers
- Better separation of concerns
- Improved code organization
- Enhanced monitoring capabilities

## Risk Mitigation

### Technical Risks
- **API Compatibility**: Maintain backward compatibility during transition
- **Performance Regression**: Comprehensive benchmarking and optimization
- **Integration Issues**: Thorough testing at each phase
- **Configuration Complexity**: Clear documentation and validation

### Operational Risks
- **Deployment Issues**: Staged deployment with rollback plan
- **User Impact**: Maintain existing functionality and interfaces
- **Training Needs**: Comprehensive documentation and examples
- **Support Issues**: Enhanced error handling and troubleshooting guides