# Pipeline Configuration Fixes - Requirements Document

## Introduction

This specification addresses critical configuration issues discovered during the production of the GLOBAL RENEWABLES book. The fixes ensure proper default values, LLM configuration respect, font configuration consistency, and proper generation of all backmatter components including foreword, publisher's note, and glossary.

## Requirements

### Requirement 1: Required Field Defaults

**User Story:** As a publisher, I want required fields to have sensible defaults, so that I don't have to manually enter common values every time.

#### Acceptance Criteria

1. WHEN using simple or advanced display modes THEN lightning_source_account SHALL default to "6024045"
2. WHEN configuring language settings THEN language_code SHALL default to "eng"
3. WHEN setting up field reports THEN field_reports SHALL default to "HTML"
4. WHEN these defaults are set THEN they SHALL be visible in the UI and used in processing

### Requirement 2: LLM Configuration Consistency

**User Story:** As a publisher, I want all LLM calls to respect the pipeline configuration, so that I have consistent model usage and cost control.

#### Acceptance Criteria

1. WHEN I configure LLM settings in the pipeline THEN all stage 3 processing SHALL use those settings
2. WHEN BackmatterProcessor is instantiated THEN it SHALL receive the pipeline LLM configuration
3. WHEN foreword generation occurs THEN it SHALL use the pipeline LLM configuration (not hardcoded gemini-2.5-pro)
4. WHEN publisher's note generation occurs THEN it SHALL use the pipeline LLM configuration
5. WHEN no LLM configuration is provided THEN it SHALL use sensible defaults (not hardcoded gemini models)
6. WHEN LLM calls are made THEN they SHALL log the model being used for transparency

### Requirement 3: Font Configuration Consistency

**User Story:** As a publisher, I want font configurations to be consistently applied, so that the compiled PDF matches my configuration settings.

#### Acceptance Criteria

1. WHEN Korean font is configured in tranche settings THEN the LaTeX template SHALL use that font
2. WHEN template processing occurs THEN font variables SHALL be substituted from configuration
3. WHEN fonts are not specified THEN sensible defaults SHALL be used
4. WHEN font substitution fails THEN clear error messages SHALL be provided

### Requirement 4: Backmatter Generation Completeness

**User Story:** As a publisher, I want all backmatter components to be generated properly, so that the final interior contains complete foreword, publisher's note, and glossary sections.

#### Acceptance Criteria

1. WHEN book processing occurs THEN a foreword SHALL be generated using LLM about pilsa tradition
2. WHEN book processing occurs THEN a publisher's note SHALL be generated with 3 structured paragraphs
3. WHEN book processing occurs THEN a glossary SHALL be generated in 2-column format
4. WHEN glossary is generated THEN Korean terms SHALL appear at top of left-hand cells with English equivalents below
5. WHEN glossary is generated THEN it SHALL fit within page margins using proper column layout
6. WHEN any backmatter generation fails THEN clear error messages SHALL be provided

### Requirement 5: LaTeX Formatting and Escaping

**User Story:** As a publisher, I want clean LaTeX output without broken commands, so that the compiled PDF displays properly formatted text.

#### Acceptance Criteria

1. WHEN LaTeX content is generated THEN broken LaTeX commands like "extit{" SHALL be properly escaped or removed
2. WHEN foreword is generated THEN it SHALL contain no stray LaTeX commands in the final output
3. WHEN any text processing occurs THEN LaTeX special characters SHALL be properly escaped
4. WHEN LaTeX compilation occurs THEN no LaTeX syntax errors SHALL be present

### Requirement 6: Bibliography Formatting

**User Story:** As a publisher, I want properly formatted bibliography citations, so that the compiled PDF displays professional hanging indents.

#### Acceptance Criteria

1. WHEN bibliography is generated THEN citations SHALL have first line flush left
2. WHEN bibliography is generated THEN second and following lines SHALL be indented 0.15 inches
3. WHEN bibliography appears in compiled PDF THEN hanging indent formatting SHALL be visible
4. WHEN bibliography formatting fails THEN clear error messages SHALL be provided

### Requirement 7: Configuration Validation

**User Story:** As a publisher, I want configuration validation, so that I can catch issues before processing begins.

#### Acceptance Criteria

1. WHEN required fields are missing THEN validation SHALL fail with clear messages
2. WHEN LLM configuration is invalid THEN validation SHALL provide helpful guidance
3. WHEN font configuration is invalid THEN validation SHALL suggest alternatives
4. WHEN validation passes THEN processing SHALL proceed with confidence

## Technical Requirements

### TR1: Default Value Management
- Lightning Source Account: "6024045"
- Language Code: "eng"
- Field Reports: "HTML"
- LLM Model: "gpt-4o-mini" (not gemini models)

### TR2: Configuration Propagation
- Pipeline configuration must flow to all processing modules
- LLM configuration must be passed to BackmatterProcessor
- LLM configuration must be passed to foreword generation
- LLM configuration must be passed to publisher's note generation
- Font configuration must be available to template processing

### TR3: Template Variable System
- Font variables must be injected into LaTeX templates
- Configuration values must override hardcoded values
- Template processing must be robust and provide clear errors

### TR4: Backmatter Generation Requirements
- Foreword: 300-400 words about pilsa tradition and practice
- Publisher's Note: 3 paragraphs with pilsa book explanation
- Glossary: 2-column layout with Korean/English term stacking
- All components must use pipeline LLM configuration

### TR5: LaTeX Processing and Formatting
- LaTeX escaping must be robust and prevent broken commands
- Bibliography must use hanging indent with 0.15in indentation
- All LaTeX special characters must be properly escaped
- LaTeX compilation must be error-free

### TR6: Logging and Transparency
- LLM model usage must be logged for all backmatter generation
- Configuration values must be logged at startup
- Template substitution must be logged for debugging
- Backmatter generation success/failure must be logged
- LaTeX processing errors must be logged with context