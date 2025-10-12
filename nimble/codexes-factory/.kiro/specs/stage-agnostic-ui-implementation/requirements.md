# Stage-Agnostic UI Implementation Requirements

## Introduction

This document outlines the requirements for implementing truly stage/length-agnostic user interfaces for the Advanced Ideation System. The current implementation has hardcoded forms for specific content types, but the system should support CodexObject-agnostic interfaces where any type of creative content (idea, logline, synopsis, outline, draft, manuscript) can be submitted to any workflow (reader panels, tournaments, generation, transformation, etc.).

The goal is to create flexible, universal forms and interfaces that adapt to the CodexObject type and development stage while maintaining usability and providing appropriate guidance for each content type.

## Requirements

### Requirement 1: Universal CodexObject Input Interface

**User Story:** As a content creator, I want to upload or input any type of creative content (idea, synopsis, draft, manuscript, etc.) through a single, intelligent interface that adapts to my content type so that I don't need to navigate different forms for different content stages.

#### Acceptance Criteria

1. WHEN a user accesses the content input interface THEN the system SHALL provide a single, universal form entry point that accepts any text content including one or more documents of any size.
2. WHEN a user uploads or enters content THEN the system SHALL automatically detect the content type (idea, logline, synopsis, outline, draft, manuscript) and development stage
3. WHEN content type is detected THEN the system SHALL if necessary dynamically adjust the form fields to show relevant metadata options for that content type
4. WHEN the content type cannot be determined THEN the system SHALL allow manual selection from all available CodexObjectType options
5. WHEN content is submitted THEN the system SHALL create a properly classified CodexObject regardless of the original content type
6. WHEN the form adapts to content type THEN the system SHALL maintain all previously entered data and not reset the form

### Requirement 2: Stage-Agnostic Workflow Submission

**User Story:** As a creative professional, I want to submit any CodexObject to any available workflow (tournaments, reader panels, series generation, element extraction) so that I can use the same content across multiple evaluation and development processes.

#### Acceptance Criteria

1. WHEN a user selects CodexObjects for processing THEN the system SHALL display all available workflows regardless of the object's current type or stage
2. WHEN a user submits CodexObjects to a tournament THEN the system SHALL accept objects of any type (ideas, synopses, drafts, manuscripts) in the same tournament
3. WHEN a user submits CodexObjects to a reader panel THEN the system SHALL evaluate any content type using appropriate evaluation criteria for that type
4. WHEN a user requests content transformation THEN the system SHALL allow transformation from any source type to any target type with appropriate prompting
5. WHEN workflows process mixed content types THEN the system SHALL handle comparison and evaluation appropriately (e.g., comparing an idea against a synopsis)
6. WHEN workflow results are displayed THEN the system SHALL clearly indicate the original content type and any transformations applied

### Requirement 3: Dynamic Form Field Adaptation

**User Story:** As a user working with different content types, I want the interface to show me relevant fields and options based on my content type while hiding irrelevant options so that I can focus on the metadata that matters for my specific content.

#### Acceptance Criteria

1. WHEN content is classified as an "idea" THEN the system SHALL emphasize fields like premise, genre, target audience, and basic themes
2. WHEN content is classified as a "synopsis" THEN the system SHALL show fields for plot structure, character development, and detailed genre classification
3. WHEN content is classified as an "outline" THEN the system SHALL provide fields for chapter structure, pacing, and detailed character arcs
4. WHEN content is classified as a "draft" or "manuscript" THEN the system SHALL show fields for word count, completion status, and revision notes
5. WHEN content type is "unknown" THEN the system SHALL show all available fields with clear explanations
6. WHEN users manually change content type THEN the system SHALL immediately adapt the form fields without losing existing data
7. WHEN the system looks for a list of content types THEN the system SHALL provide a list of all available content types with clear explanations. The system administrator SHALL be able to add content types, e.g. "scene".

### Requirement 4: Universal Content Transformation Interface

**User Story:** As a content developer, I want to transform any CodexObject into any other type (e.g., idea to synopsis, synopsis to outline, draft to treatment) through a single interface that guides me through the transformation process.

#### Acceptance Criteria

1. WHEN a user selects content for transformation THEN the system SHALL display all possible target types regardless of the source type
2. WHEN a transformation is requested THEN the system SHALL show a preview of what fields will be generated or modified in the target type
3. WHEN transformation parameters are configured THEN the system SHALL allow customization of the transformation approach (expand, condense, restructure, etc.)
4. WHEN transformation is executed THEN the system SHALL create a new CodexObject of the target type while preserving the relationship to the source
5. WHEN transformation is complete THEN the system SHALL display both the original and transformed content with clear differentiation
6. WHEN multiple transformations are chained THEN the system SHALL maintain the full transformation history and lineage
7. WHEN the system looks for a list of transformation types THEN the system SHALL provide a list of all available transformation types with clear explanations. The system administrator SHALL be able to add transformation types, e.g. "expand to outline".
8. WHEN the system looks for a list of transformation approaches THEN the system SHALL provide a list of all available transformation approaches with clear explanations. The first two approaches are "planning" top-down and "gardening" (bottom up).
9. WHEN the system looks for a list of transformation parameters THEN the system SHALL provide a list of all available transformation parameters with clear explanations. The first two parameters are "expand" and "condense".
10. WHEN the system looks for a list of transformation destinations THEN the system SHALL provide a list of all available transformation destinations (CodexTypes) with clear explanations. Initial CodexTypes = Idea, BookIdea, IdeaWithFields, Synopsis, Treatment, Outline, Draft, Manuscript. CodexMetaTypes include Series, SeriesOrdered, and SeriesUnordered.

### Requirement 5: Flexible Content Selection and Filtering

**User Story:** As a user managing multiple CodexObjects of different types, I want to select and filter content for workflows based on flexible criteria so that I can work with mixed content types or focus on specific types as needed.

#### Acceptance Criteria

1. WHEN a user accesses content selection interfaces THEN the system SHALL provide filtering options by content type, development stage, genre, creation date, and custom tags
2. WHEN multiple content types are selected THEN the system SHALL clearly display the type and stage of each selected item
3. WHEN content is selected for batch operations THEN the system SHALL allow mixed-type selections and show appropriate warnings or guidance
4. WHEN filtering is applied THEN the system SHALL maintain filter state across different workflow interfaces
5. WHEN content lists are displayed THEN the system SHALL show key metadata (type, stage, word count, creation date) in a scannable format
6. WHEN users search for content THEN the system SHALL search across all content types and provide type-aware search suggestions

### Requirement 6: Adaptive Workflow Configuration

**User Story:** As a workflow manager, I want to configure tournaments, reader panels, and other processes to handle mixed content types appropriately so that I can run meaningful evaluations across different development stages.

#### Acceptance Criteria

1. WHEN configuring a tournament with mixed content types THEN the system SHALL provide evaluation criteria that work across all included types
2. WHEN setting up reader panels THEN the system SHALL allow configuration of evaluation approaches for different content types (e.g., different questions for ideas vs. manuscripts)
3. WHEN configuring batch processing THEN the system SHALL allow type-specific processing rules while maintaining unified workflow management
4. WHEN workflows include mixed types THEN the system SHALL provide clear documentation of how different types will be handled
5. WHEN workflow results are generated THEN the system SHALL provide type-aware analysis and comparison metrics
6. WHEN workflows are saved as templates THEN the system SHALL preserve type-handling configurations for reuse

### Requirement 7: Intelligent Content Type Detection and Classification

**User Story:** As a user uploading various types of creative content, I want the system to automatically and accurately detect what type of content I'm providing so that I don't need to manually classify every piece of content.

#### Acceptance Criteria

1. WHEN content is pasted or uploaded THEN the system SHALL analyze length, structure, and content patterns to determine the most likely content type
2. WHEN content type detection is uncertain THEN the system SHALL show confidence scores and allow manual override
3. WHEN content has mixed characteristics THEN the system SHALL suggest the most appropriate classification with reasoning
4. WHEN content is very short THEN the system SHALL distinguish between loglines, premises, and incomplete content
5. WHEN content is very long THEN the system SHALL distinguish between detailed outlines, treatments, and manuscript excerpts
6. WHEN classification is complete THEN the system SHALL provide feedback on why the content was classified as it was
7. WHEN the system performs content analysis THEN the system SHALL use both rule-based heuristics and LLM-based classification for optimal accuracy

### Requirement 8: Universal Export and Integration

**User Story:** As a content creator, I want to export any CodexObject in formats appropriate for its type and stage so that I can use the content in external tools and workflows.

#### Acceptance Criteria

1. WHEN exporting CodexObjects THEN the system SHALL provide format options appropriate for each content type (plain text, structured JSON, formatted document)
2. WHEN exporting mixed content types THEN the system SHALL provide unified export formats that preserve type information
3. WHEN exporting for external tools THEN the system SHALL provide integration formats for common writing software (Scrivener, Final Draft, etc.)
4. WHEN exporting workflow results THEN the system SHALL include content type information in all export formats
5. WHEN importing content THEN the system SHALL accept and properly classify content from various sources and formats
6. WHEN content is shared between users THEN the system SHALL preserve all type and stage information across sharing boundaries

### Requirement 9: Progressive Enhancement Based on Content Maturity

**User Story:** As a content developer, I want the interface to progressively show more advanced options and workflows as my content becomes more developed so that I'm not overwhelmed with irrelevant features for early-stage content.

#### Acceptance Criteria

1. WHEN content is classified as early-stage (idea, logline) THEN the system SHALL emphasize basic development workflows and hide advanced manuscript features
2. WHEN content reaches intermediate stages (synopsis, outline) THEN the system SHALL reveal structural analysis and development planning tools
3. WHEN content is advanced (draft, manuscript) THEN the system SHALL show full editing, revision, and publication preparation features
4. WHEN content stage is manually overridden THEN the system SHALL respect user choice and show all requested features
5. WHEN content evolves through stages THEN the system SHALL automatically unlock new features and notify users of new capabilities
6. WHEN users are experienced THEN the system SHALL provide options to show all features regardless of content stage

### Requirement 10: Correct Multi-Object Generation and Display

**User Story:** As a user requesting multiple ideas or objects, I want to receive the exact number I requested and view them in an efficient, scannable format so that I can quickly review and work with large sets of generated content.

#### Acceptance Criteria

1. WHEN a user requests N ideas/objects THEN the system SHALL generate and return exactly N objects, not fewer
2. WHEN the LLM generates fewer objects than requested THEN the system SHALL make additional calls to reach the requested count
3. WHEN multiple objects are displayed THEN the system SHALL use a dataframe-like, tabular view with key fields visible (title, type, genre, word count)
4. WHEN viewing multiple objects THEN the system SHALL provide scrollable interfaces that can handle hundreds of objects efficiently
5. WHEN objects are listed THEN the system SHALL provide sortable columns and filtering options for easy navigation
6. WHEN users want to view full content THEN the system SHALL provide expandable rows or modal dialogs rather than individual expanders for each object
7. WHEN working with large object sets THEN the system SHALL implement pagination or virtual scrolling for performance
8. WHEN objects are selected from lists THEN the system SHALL provide bulk selection capabilities with checkboxes

### Requirement 11: Contextual Help and Guidance

**User Story:** As a user working with different content types, I want contextual help and guidance that's specific to my content type and chosen workflow so that I understand how to best use the system for my specific situation.

#### Acceptance Criteria

1. WHEN users interact with type-specific fields THEN the system SHALL provide tooltips and help text relevant to that content type
2. WHEN workflows are selected THEN the system SHALL explain how the workflow will handle the specific content types involved
3. WHEN content type is detected THEN the system SHALL provide suggestions for appropriate next steps and workflows
4. WHEN errors or warnings occur THEN the system SHALL provide type-specific guidance for resolution
5. WHEN users are new to a content type THEN the system SHALL offer guided tours and examples specific to that type
6. WHEN advanced features are used THEN the system SHALL provide detailed explanations of how features work with different content types

### Requirement 12: Command Line Interface Support

**User Story:** As a developer or power user, I want to access all stage-agnostic UI functionality through command line interfaces so that I can automate workflows and integrate with external tools.

#### Acceptance Criteria

1. WHEN using the command line interface THEN the system SHALL provide CLI commands for all content input, transformation, and workflow operations
2. WHEN running CLI commands THEN the system SHALL support batch processing of multiple files and objects
3. WHEN using CLI for content detection THEN the system SHALL output content type classifications in machine-readable formats (JSON, CSV)
4. WHEN running CLI workflows THEN the system SHALL provide progress indicators and detailed logging
5. WHEN CLI operations complete THEN the system SHALL return appropriate exit codes and structured output
6. WHEN CLI help is requested THEN the system SHALL provide comprehensive documentation for all available commands and options