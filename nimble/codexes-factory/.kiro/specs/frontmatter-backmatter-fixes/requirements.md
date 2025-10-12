# Frontmatter and Backmatter Generation - Requirements Document

## Introduction

This specification addresses critical issues with frontmatter and backmatter generation, configuration hierarchy enforcement, and prevents regressions in the book production pipeline.

## Requirements

### Requirement 1: Configuration Hierarchy Enforcement

**User Story:** As a publisher, I want configuration values to follow a strict hierarchy, so that tranche settings always override other configurations.

#### Acceptance Criteria

1. WHEN configuration values conflict THEN hierarchy SHALL be: default < publisher < imprint < tranche (tranche wins)
2. WHEN schedule.json contains subtitle THEN it SHALL always trump machine-generated alternatives
3. WHEN tranche.json contains author and imprint THEN they SHALL always trump LLM generated values
4. WHEN ISBN is assigned THEN it SHALL appear on the copyright page
5. WHEN logo font is specified in imprint config THEN it SHALL be used (Zapfino for xynapse_traces)

### Requirement 2: Bibliography Formatting (DO NOT CHANGE)

**User Story:** As a publisher, I want bibliography formatting to remain stable, so that hanging indents work correctly.

#### Acceptance Criteria

1. WHEN bibliography is generated THEN it SHALL use memoir class `\begin{hangparas}{0.15in}{1}` format
2. WHEN bibliography formatting works correctly THEN it SHALL be marked as "do not change"
3. WHEN bibliography is compiled THEN first line SHALL be flush left, subsequent lines indented 0.15in

### Requirement 3: Publisher's Note Generation

**User Story:** As a publisher, I want publisher's note to be 100% LLM generated, so that no boilerplate text is attached.

#### Acceptance Criteria

1. WHEN publisher's note is generated THEN it SHALL be 100% LLM generated content
2. WHEN publisher's note is created THEN no boilerplate paragraphs SHALL be attached
3. WHEN publisher's note uses reprompting THEN it SHALL use `storefront_get_en_motivation` prompt

### Requirement 4: Foreword Generation

**User Story:** As a publisher, I want foreword generation to produce clean text, so that Korean characters and markdown are properly formatted.

#### Acceptance Criteria

1. WHEN foreword is generated THEN Korean characters SHALL be properly formatted (no visible markdown)
2. WHEN foreword contains Korean terms THEN they SHALL use proper LaTeX commands
3. WHEN foreword is generated THEN no visible markdown syntax SHALL appear (no `*pilsa*`)
4. WHEN foreword uses reprompting THEN it SHALL follow same sequence as main model calls

### Requirement 5: Glossary Formatting

**User Story:** As a publisher, I want glossary to display correctly, so that it has proper formatting and no numbering issues.

#### Acceptance Criteria

1. WHEN glossary is generated THEN it SHALL NOT have numeral "2" at the beginning
2. WHEN glossary text is displayed THEN it SHALL NOT be overprinted on itself
3. WHEN glossary is formatted THEN it SHALL have proper leading for typographic best practices
4. WHEN glossary uses chapter heading THEN it SHALL use `\chapter*{Glossary}` (unnumbered)

### Requirement 6: Mnemonics Generation

**User Story:** As a publisher, I want mnemonics section to appear in the final document, so that all backmatter is complete.

#### Acceptance Criteria

1. WHEN book is processed THEN mnemonics section SHALL appear in final document
2. WHEN mnemonics processing fails THEN fallback methods SHALL be used
3. WHEN mnemonics are generated THEN they SHALL use proper LLM configuration
4. WHEN mnemonics file is created THEN it SHALL be `mnemonics.tex` in build directory

### Requirement 7: Frontmatter vs Backmatter Classification

**User Story:** As a publisher, I want proper classification of document sections, so that frontmatter and backmatter are correctly organized.

#### Acceptance Criteria

1. WHEN sections are classified THEN foreword SHALL be frontmatter
2. WHEN sections are classified THEN publisher's note SHALL be frontmatter  
3. WHEN sections are classified THEN glossary SHALL be frontmatter
4. WHEN sections are classified THEN mnemonics SHALL be backmatter
5. WHEN sections are classified THEN bibliography SHALL be backmatter
6. WHEN frontmatter sections use reprompting THEN they SHALL follow reprompt sequence

## Technical Requirements

### TR1: Configuration Hierarchy Implementation
- Hierarchy: default < publisher < imprint < tranche
- Schedule.json subtitle: always wins
- Tranche author/imprint: always wins
- ISBN: must appear on copyright page
- Logo font: use imprint specification (Zapfino for xynapse_traces)

### TR2: Bibliography Stability (LOCKED)
- Format: `\begin{hangparas}{0.15in}{1}` ... `\end{hangparas}`
- Status: DO NOT CHANGE
- Indentation: 0.15in hanging indent

### TR3: Content Generation Requirements
- Publisher's note: 100% LLM, no boilerplate
- Foreword: clean Korean formatting, no visible markdown
- Glossary: `\chapter*{Glossary}`, proper leading, no overprinting
- Mnemonics: must appear, proper fallback handling

### TR4: Reprompting Integration
- Frontmatter sections: use reprompting system
- Sequence: same as main model calls
- Prompts: use existing prompt keys where available

### TR5: Regression Prevention
- Lock stable components (bibliography)
- Validate configuration hierarchy
- Test all sections appear in final document
- Prevent markdown/formatting leakage

## Anti-Regression Measures

### Configuration Validation
- Test hierarchy enforcement at each level
- Validate ISBN appears on copyright page
- Verify logo font matches imprint specification

### Content Validation  
- Check all sections appear in final document
- Validate formatting quality (no overprinting, proper leading)
- Ensure no boilerplate text in LLM-generated content

### Stability Locks
- Bibliography formatting: LOCKED (memoir class hangparas)
- Configuration hierarchy: ENFORCED
- Section classification: frontmatter vs backmatter

## Success Criteria

1. ✅ All sections appear in final document
2. ✅ Configuration hierarchy strictly enforced
3. ✅ No visible markdown or formatting errors
4. ✅ Bibliography hanging indents work correctly (LOCKED)
5. ✅ No regressions in working components
6. ✅ Clean, professional typographic output