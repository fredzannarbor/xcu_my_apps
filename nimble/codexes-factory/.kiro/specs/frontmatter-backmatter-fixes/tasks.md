# Implementation Plan

## Phase 1: Lock Stable Components and Prevent Regressions

- [ ] 1. Mark bibliography formatting as LOCKED (DO NOT CHANGE)
  - Add clear documentation that bibliography uses memoir class hangparas
  - Add validation to ensure format is not changed
  - Create regression test for bibliography hanging indents
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 2. Implement configuration hierarchy enforcement
  - Create ConfigurationHierarchyEnforcer class
  - Implement strict hierarchy: default < publisher < imprint < tranche
  - Ensure schedule.json subtitle always trumps machine-generated alternatives
  - Ensure tranche author and imprint always trump LLM generated values
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 3. Fix ISBN display on copyright page
  - Ensure assigned ISBN appears on copyright page
  - Validate ISBN is pulled from correct configuration level
  - Test ISBN display in compiled PDF
  - _Requirements: 1.4_

- [ ] 4. Fix logo font configuration
  - Ensure Zapfino font is used for xynapse_traces (not Berkshire)
  - Implement proper font hierarchy from imprint config
  - Validate logo font in compiled PDF
  - _Requirements: 1.5_

## Phase 2: Fix Content Generation Issues

- [ ] 5. Fix glossary formatting issues
  - Remove numeral "2" from glossary by using `\chapter*{Glossary}`
  - Fix text overprinting by restoring proper leading
  - Implement proper typographic spacing
  - Test glossary display in compiled PDF
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 6. Clean up publisher's note generation
  - Remove boilerplate paragraph attachment
  - Ensure 100% LLM generated content
  - Use only `storefront_get_en_motivation` prompt output
  - Test publisher's note in compiled PDF
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 7. Fix foreword generation Korean formatting
  - Update foreword prompt to eliminate visible markdown
  - Fix Korean character presentation using proper LaTeX commands
  - Remove `*pilsa*` markdown syntax from output
  - Use `\textit{pilsa}` and `\korean{필사}` properly
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 8. Ensure mnemonics section appears
  - Debug why mnemonics section is not being created
  - Implement proper fallback mechanisms
  - Ensure mnemonics.tex file is generated
  - Validate mnemonics appear in final document
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

## Phase 3: Implement Reprompting System for Frontmatter

- [ ] 9. Classify sections as frontmatter vs backmatter
  - Mark foreword, publisher's note, glossary as frontmatter
  - Mark mnemonics, bibliography as backmatter
  - Document section classification clearly
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 10. Implement foreword reprompting
  - Add foreword to reprompt_keys in prompts.json
  - Create foreword prompt with proper Korean formatting
  - Integrate foreword generation with reprompting system
  - Follow same sequence as main model calls
  - _Requirements: 4.4, 7.6_

- [ ] 11. Integrate publisher's note with reprompting
  - Ensure publisher's note uses existing `storefront_get_en_motivation`
  - Remove any direct LLM calls in prepress for publisher's note
  - Use reprompting system consistently
  - _Requirements: 3.3, 7.6_

## Phase 4: Comprehensive Validation and Testing

- [ ] 12. Create regression prevention system
  - Implement validation for all fixed components
  - Add automated tests for configuration hierarchy
  - Create content presence validation
  - Add formatting quality checks
  - _Requirements: All requirements validation_

- [ ] 13. Add comprehensive logging and monitoring
  - Log configuration hierarchy application
  - Log all section generation success/failure
  - Monitor for formatting regressions
  - Add clear error messages for debugging
  - _Requirements: TR5_

- [ ] 14. Create integration tests
  - Test complete pipeline with configuration hash 4889ffa3373907e7
  - Validate all sections appear in final document
  - Test configuration hierarchy enforcement
  - Verify no regressions in working components
  - _Requirements: All requirements validation_

- [ ] 15. Document locked components and anti-regression measures
  - Create clear documentation of DO NOT CHANGE components
  - Document configuration hierarchy requirements
  - Create troubleshooting guide for common issues
  - Document best practices for preventing regressions
  - _Requirements: TR5_

## Critical Success Criteria

Each task must ensure:
1. ✅ No regressions in working components (especially bibliography)
2. ✅ Configuration hierarchy strictly enforced
3. ✅ All sections appear in final document
4. ✅ Clean, professional formatting output
5. ✅ Proper Korean character handling
6. ✅ No visible markdown or formatting errors

## Anti-Regression Checklist

Before marking any task complete:
- [ ] Bibliography hanging indents still work correctly
- [ ] Configuration hierarchy is enforced
- [ ] All required sections appear in final document
- [ ] No new formatting errors introduced
- [ ] Korean characters display properly
- [ ] No visible markdown syntax in output