# Stage-Agnostic UI Implementation Tasks

## Progressive Implementation Plan

This document outlines a progressive implementation approach where each task delivers a working UI component that users can immediately see and use. Each task builds on the previous ones, revealing new capabilities incrementally.

## Phase 1: Foundation & Basic Input (Tasks 1-3)

- [x] 1. **DELIVERABLE: Basic Text Input Interface** - Create a working text input that accepts any content
  - Create the UI module directory structure under `src/codexes/modules/ideation/ui/`
  - Create basic Streamlit page at `src/codexes/pages/16_Stage_Agnostic_UI.py`
  - Implement simple text area input that accepts any creative content
  - Add basic "Create CodexObject" button that creates objects with minimal metadata
  - Create basic CodexObject display showing title, type, and content preview
  - Set up standardized model list configuration: ollama/mistral, ollama/deepseek-r1:latest, gemini/gemini-2.5-flash, gemini/gemini-2.5-pro, openai/gpt-5-mini, xai/grok-3-latest, anthropic/claude-4, ollama/gpt-oss:20b, ollama/gemma3:270m
  - **USER CAN**: Enter text content and create basic CodexObjects
  - _Requirements: 1.1, 1.4_

- [x] 2. **DELIVERABLE: Intelligent Content Type Detection** - Add automatic content type detection with confidence display
  - Create `RuleBasedClassifier` with word count and structure analysis
  - Implement basic pattern matching for ideas, synopses, outlines, and drafts
  - Add confidence scoring and display detection results to user
  - Create `ModelConfigManager` with standardized model list and selection UI
  - Integrate LLM-based classification using existing `IdeationLLMService`
  - Add model selection dropdown for content detection
  - Show detection results with confidence percentage and manual override option
  - **USER CAN**: See automatic content type detection with confidence scores and override if needed
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [x] 3. **DELIVERABLE: File Upload & Multi-Format Support** - Add file upload capabilities with format support
  - Create `FileHandler` component supporting .txt, .docx, .pdf, .md formats
  - Add file upload interface with drag-and-drop support
  - Implement ZIP archive extraction and batch processing
  - Add directory browser for data/ and output/ directories
  - Show file processing progress and results for multiple files
  - Display batch content type detection results for uploaded files
  - **USER CAN**: Upload files, folders, and archives to create multiple CodexObjects at once
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.6, 8.1, 8.5_

## Phase 2: Smart Forms & Object Management (Tasks 4-6)

- [x] 4. **DELIVERABLE: Adaptive Metadata Forms** - Add smart forms that adapt to detected content types
  - Create field configuration system for different content types
  - Implement `FormAdapter` that shows relevant fields based on detected type
  - Add intelligent field suggestions (auto-generated titles, genre suggestions, tag recommendations)
  - Create form validation and field dependencies
  - Show different form layouts for Ideas vs Synopses vs Outlines vs Drafts
  - **USER CAN**: Fill out smart forms that adapt to their content type with helpful suggestions
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 5. **DELIVERABLE: Object Collection Display** - Add a data table to view and manage created objects
  - Create `ObjectDataTable` component using Streamlit's data_editor
  - Display all created CodexObjects in a sortable, filterable table
  - Add bulk selection with checkboxes
  - Show object details in expandable rows or modal views
  - Add basic export functionality (JSON, CSV)
  - Implement search across object titles and content
  - **USER CAN**: View, search, filter, and select from their collection of created objects
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

- [x] 6. **DELIVERABLE: Advanced Filtering & Search** - Add powerful filtering and search capabilities
  - Implement advanced filtering by type, genre, date, tags, word count
  - Add full-text search across object content and metadata
  - Create saved filter presets and search history
  - Add filter state persistence across sessions
  - Show filter results count and clear filters option
  - **USER CAN**: Find specific objects quickly using advanced search and filtering
  - _Requirements: 5.1, 5.2, 5.4, 5.6_

## Phase 3: Content Transformation (Tasks 7-8)

- [x] 7. **DELIVERABLE: Content Transformation Interface** - Add the ability to transform content between types
  - Create `TransformationInterface` with transformation type selection
  - Implement transformation approach selection (planning vs gardening)
  - Add transformation parameters (expand vs condense)
  - Integrate with existing transformation engine and prompt system
  - Show transformation preview and progress
  - Display transformation results with before/after comparison
  - **USER CAN**: Transform their content from one type to another (e.g., Idea → Synopsis → Outline)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10_

- [x] 8. **DELIVERABLE: Batch Transformation & History** - Add batch processing and transformation tracking
  - Implement batch transformation for multiple selected objects
  - Add transformation history and lineage tracking
  - Create transformation rollback capabilities
  - Show transformation progress for large batches
  - Add transformation result comparison and quality assessment
  - **USER CAN**: Transform multiple objects at once and track transformation history
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

## Phase 4: Workflow Integration (Tasks 9-10)

- [x] 9. **DELIVERABLE: Universal Workflow Interface** - Add workflow execution capabilities
  - Create workflow selection interface (Tournament, Reader Panel, Series Generation)
  - Implement workflow adapters for existing systems
  - Add mixed-type handling for workflows processing different content types
  - Show workflow configuration options that adapt to selected content
  - Display workflow progress and results
  - **USER CAN**: Run tournaments, reader panels, and other workflows on their content
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  INTERIM FIX: add ".csv" to supported file formats that can be imported

- [x] 10. **DELIVERABLE: Advanced Workflow Features** - Add sophisticated workflow capabilities
  - Implement mixed-type evaluation and fair comparison algorithms
  - Add workflow result export and sharing
  - Create workflow templates and saved configurations
  - Add workflow scheduling and automation options
  - Show detailed workflow analytics and insights
  - **USER CAN**: Run sophisticated workflows with mixed content types and get detailed analytics
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

## Phase 5: Imprint Integration (Tasks 11-12)

- [ ] 11. **DELIVERABLE: Imprint Selection & Context** - Add imprint integration with selectable modes
  - Create `ImprintIdeationBridge` infrastructure
  - Add imprint selection dropdown to the interface
  - Implement selectable integration modes (Imprint-driven, Export to Pipeline, Bidirectional Sync)
  - Show imprint-specific guidance and constraints when selected
  - Add imprint branding and validation features
  - **USER CAN**: Select an imprint context and choose which integration features to use
  - _Requirements: System integration between publishing and ideation workflows_

- [ ] 12. **DELIVERABLE: Full Imprint Workflow Integration** - Complete the imprint-ideation bridge
  - Implement imprint-driven content generation with brand guidelines
  - Add export functionality to convert ideation outputs to book pipeline format
  - Create bidirectional metadata synchronization
  - Add imprint-aware content validation and quality checks
  - Show imprint publishing calendar integration
  - **USER CAN**: Generate content aligned with imprint brands and export to book production
  - _Requirements: User-selectable brand-consistent content generation and workflow integration_

## Phase 6: Advanced Features (Tasks 13-15)

- [ ] 13. **DELIVERABLE: Progressive Enhancement & Help** - Add adaptive UI and contextual help
  - Implement content maturity assessment and progressive feature unlocking
  - Create contextual help system with tooltips and guidance
  - Add user experience level detection and UI adaptation
  - Implement interactive tutorials for different content types
  - Show feature recommendations based on content development stage
  - **USER CAN**: Get contextual help and see features unlock as their content matures
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [ ] 14. **DELIVERABLE: Export & External Integration** - Add comprehensive export and integration options
  - Create universal export system for different formats (JSON, CSV, TXT, DOCX)
  - Add integration with external tools (Scrivener, Final Draft)
  - Implement sharing capabilities with type and lineage preservation
  - Add API endpoints for external system integration
  - Create export templates for different use cases
  - **USER CAN**: Export their work in multiple formats and integrate with external writing tools
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ] 15. **DELIVERABLE: Command Line Interface** - Add CLI for power users and automation
  - Create `StageAgnosticCLI` with command parsing and routing
  - Implement CLI commands for content detection, transformation, and workflows
  - Add batch processing for directory operations
  - Create progress indicators and structured output (JSON/CSV)
  - Add configuration file support for automated workflows
  - **USER CAN**: Use command line tools for batch processing and automation
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

## Implementation Approach

### Progressive Reveal Strategy
Each task delivers a complete, working UI component that users can immediately interact with:

1. **Task 1**: Users can enter text and create basic objects
2. **Task 2**: Users see intelligent content detection with confidence scores  
3. **Task 3**: Users can upload files and process batches
4. **Task 4**: Users get smart forms that adapt to their content
5. **Task 5**: Users can view and manage their object collection
6. **And so on...**

### Key Principles
- **Immediate Value**: Every task produces something users can see and use
- **Incremental Complexity**: Each task builds on previous functionality
- **User-Centric**: Focus on user-visible features rather than internal architecture
- **Testable Milestones**: Each deliverable can be tested and validated independently

## Implementation Notes

### Dependencies
- All LLM interactions must use existing `enhanced_llm_caller.py`
- File operations must integrate with existing storage systems
- UI components must follow existing Streamlit patterns and styling
- Configuration must use existing multi-level config system

### Testing Strategy
- Unit tests for all individual components
- Integration tests for component interactions
- Performance tests for large dataset handling
- User acceptance tests for all requirements
- Regression tests for existing functionality

### Performance Considerations
- Implement caching for content type detection results
- Use lazy loading for large object collections
- Optimize file processing for large uploads
- Implement background processing for time-intensive operations

### Security Requirements
- Validate all file uploads and restrict file types
- Sanitize all user input and content
- Restrict directory access to allowed paths only
- Implement rate limiting for LLM calls and file processing