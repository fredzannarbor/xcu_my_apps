# Design Document: LSI Field Enhancement Phase 3

## Overview

LSI Field Enhancement Phase 3 builds upon the existing field mapping and completion infrastructure to implement three key features:

1. **ISBN Database Management**: A system to track, manage, and automatically assign ISBNs from publisher-owned inventory.
2. **Series Metadata Management**: A framework for managing book series metadata with proper sequencing and publisher isolation.
3. **Enhanced Field Completion**: Improvements to the existing LLM-based field completion system for LSI metadata fields.

This design document outlines the architecture, components, data models, and implementation approach for each of these features.

## Architecture

The Phase 3 enhancements will integrate with the existing LSI field mapping and completion system while adding new components for ISBN and series management. The overall architecture follows the established pattern of the Codexes Factory platform:

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│                     │     │                     │     │                     │
│  ISBN Database      │     │  Series Metadata    │     │  Enhanced Field     │
│  Manager            │     │  Manager            │     │  Completion         │
│                     │     │                     │     │                     │
└─────────┬───────────┘     └─────────┬───────────┘     └─────────┬───────────┘
          │                           │                           │
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                       LSI Field Mapping Registry                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                       LSI ACS Generator                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Modularity**: Each component is designed to be independent but interoperable.
2. **Extensibility**: The system can be extended to support additional features in future phases.
3. **Configurability**: All components are configurable through JSON configuration files.
4. **Validation**: Robust validation ensures data integrity throughout the process.
5. **Logging**: Comprehensive logging provides visibility into the system's operation.

## Components and Interfaces

### 1. ISBN Database Manager

The ISBN Database Manager will handle the storage, tracking, and assignment of ISBNs.

#### Key Components:

- **ISBNDatabase**: Core class for managing the ISBN database
- **ISBNImporter**: Handles importing ISBNs from Bowker spreadsheets
- **ISBNAssigner**: Assigns ISBNs to books based on availability
- **ISBNStatusTracker**: Tracks the status of ISBNs (available, privately assigned, publicly assigned)

#### Interface:

```python
class ISBNDatabase:
    def import_from_bowker(self, file_path: str) -> Dict[str, Any]:
        """Import ISBNs from a Bowker spreadsheet."""
        pass
        
    def get_next_available_isbn(self, publisher_id: str = None) -> str:
        """Get the next available ISBN for a publisher."""
        pass
        
    def assign_isbn(self, isbn: str, book_id: str) -> bool:
        """Assign an ISBN to a book (private assignment)."""
        pass
        
    def mark_as_published(self, isbn: str) -> bool:
        """Mark an ISBN as publicly assigned (published)."""
        pass
        
    def release_isbn(self, isbn: str) -> bool:
        """Release a privately assigned ISBN back to the available pool."""
        pass
        
    def get_isbn_status(self, isbn: str) -> str:
        """Get the status of an ISBN (available, privately assigned, publicly assigned)."""
        pass
```

### 2. Series Metadata Manager

The Series Metadata Manager will handle the creation, tracking, and assignment of series metadata.

#### Key Components:

- **SeriesRegistry**: Core class for managing series metadata
- **SeriesAssigner**: Assigns books to series and manages sequence numbers
- **SeriesValidator**: Validates series metadata for consistency
- **SeriesUIIntegration**: Integrates with the UI for series selection and creation

#### Interface:

```python
class SeriesRegistry:
    def create_series(self, name: str, publisher_id: str, multi_publisher: bool = False) -> str:
        """Create a new series and return its ID."""
        pass
        
    def add_book_to_series(self, series_id: str, book_id: str, sequence_number: int = None) -> bool:
        """Add a book to a series with an optional sequence number."""
        pass
        
    def get_next_sequence_number(self, series_id: str) -> int:
        """Get the next available sequence number for a series."""
        pass
        
    def get_series_by_name(self, name: str, publisher_id: str = None) -> List[Dict[str, Any]]:
        """Get series by name, optionally filtered by publisher."""
        pass
        
    def get_series_by_id(self, series_id: str) -> Dict[str, Any]:
        """Get series metadata by ID."""
        pass
        
    def update_series(self, series_id: str, updates: Dict[str, Any]) -> bool:
        """Update series metadata."""
        pass
        
    def delete_series(self, series_id: str) -> bool:
        """Delete a series (if no books are assigned to it)."""
        pass
```

### 3. Enhanced Field Completion

The Enhanced Field Completion system will build upon the existing LLMFieldCompleter to improve field completion for various LSI metadata fields.

#### Key Components:

- **EnhancedLLMFieldCompleter**: Extended version of the existing LLMFieldCompleter
- **FieldCompletionStrategies**: Specialized strategies for different field types
- **FieldCompletionReporter**: Generates reports on field completion status
- **ValidationFramework**: Validates completed fields against LSI requirements

#### Interface:

```python
class EnhancedLLMFieldCompleter(LLMFieldCompleter):
    def complete_annotation_summary(self, metadata: CodexMetadata) -> str:
        """Complete the Annotation/Summary field with enhanced formatting."""
        pass
        
    def suggest_bisac_codes(self, metadata: CodexMetadata) -> List[str]:
        """Suggest BISAC codes with category overrides support."""
        pass
        
    def suggest_thema_codes(self, metadata: CodexMetadata) -> List[str]:
        """Suggest Thema subject codes."""
        pass
        
    def extract_lsi_contributor_info(self, metadata: CodexMetadata) -> Dict[str, Any]:
        """Extract comprehensive contributor information."""
        pass
        
    def get_illustration_info(self, metadata: CodexMetadata) -> Dict[str, Any]:
        """Get illustration count and notes."""
        pass
        
    def create_simple_toc(self, metadata: CodexMetadata, book_content: str = None) -> str:
        """Create a simple table of contents."""
        pass
```

## Data Models

### 1. ISBN Database Model

```python
@dataclass
class ISBN:
    isbn: str
    publisher_id: str
    status: str  # "available", "privately_assigned", "publicly_assigned"
    assigned_to: Optional[str] = None  # book_id if assigned
    assignment_date: Optional[datetime] = None
    publication_date: Optional[datetime] = None
    notes: Optional[str] = None
```

### 2. Series Metadata Model

```python
@dataclass
class Series:
    id: str
    name: str
    publisher_id: str
    multi_publisher: bool = False
    creation_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
@dataclass
class SeriesBook:
    series_id: str
    book_id: str
    sequence_number: int
    addition_date: datetime = field(default_factory=datetime.now)
```

### 3. Enhanced Field Completion Models

```python
@dataclass
class FieldCompletionResult:
    field_name: str
    value: Any
    completion_method: str  # "llm", "direct", "computed", etc.
    confidence_score: float = 1.0
    completion_time: datetime = field(default_factory=datetime.now)
    
@dataclass
class FieldCompletionReport:
    metadata_id: str
    completed_fields: List[FieldCompletionResult]
    missing_fields: List[str]
    error_fields: Dict[str, str]  # field_name -> error_message
    completion_time: datetime = field(default_factory=datetime.now)
```

## Error Handling

### ISBN Database Errors

- **ISBNNotFoundError**: Raised when an ISBN is not found in the database
- **ISBNAlreadyAssignedError**: Raised when attempting to assign an already assigned ISBN
- **ISBNPublishedError**: Raised when attempting to release a publicly assigned ISBN
- **BowkerImportError**: Raised when there's an error importing ISBNs from a Bowker spreadsheet

### Series Metadata Errors

- **SeriesNotFoundError**: Raised when a series is not found
- **SeriesAccessDeniedError**: Raised when a publisher attempts to access another publisher's series
- **SequenceNumberConflictError**: Raised when there's a conflict in sequence numbers
- **SeriesDeleteError**: Raised when attempting to delete a series with assigned books

### Field Completion Errors

- **FieldCompletionError**: Base error for field completion issues
- **ValidationError**: Raised when a completed field fails validation
- **LLMCallError**: Raised when there's an error calling the LLM
- **FieldFormatError**: Raised when a field cannot be formatted correctly

## Testing Strategy

### Unit Tests

1. **ISBN Database Tests**:
   - Test importing ISBNs from various Bowker spreadsheet formats
   - Test ISBN assignment and status tracking
   - Test edge cases like releasing already published ISBNs

2. **Series Metadata Tests**:
   - Test series creation and book assignment
   - Test sequence number management
   - Test multi-publisher series functionality
   - Test CRUD operations on series

3. **Field Completion Tests**:
   - Test each field completion strategy
   - Test validation of completed fields
   - Test integration with the existing LLMFieldCompleter

### Integration Tests

1. **End-to-End ISBN Management**:
   - Test the full ISBN lifecycle from import to assignment to publication

2. **Series Management Integration**:
   - Test series creation and assignment through the UI
   - Test series metadata in LSI CSV generation

3. **Field Completion Pipeline**:
   - Test the complete field completion pipeline with real book data
   - Test integration with the LSI ACS Generator

### Mock Tests

1. **LLM Mock Tests**:
   - Test field completion with mocked LLM responses
   - Test error handling with simulated LLM failures

2. **Database Mock Tests**:
   - Test ISBN and series operations with a mocked database
   - Test concurrent operations with simulated race conditions

## Implementation Plan

The implementation will follow a phased approach, with each component being developed and tested independently before integration.

### Phase 3.1: ISBN Database Management

1. Implement the core ISBNDatabase class
2. Develop the Bowker spreadsheet importer
3. Implement ISBN assignment and status tracking
4. Create the ISBN database schema and storage mechanism
5. Develop the ISBN management UI
6. Integrate with the LSI ACS Generator

### Phase 3.2: Series Metadata Management

1. Implement the core SeriesRegistry class
2. Develop the series assignment and sequence number management
3. Implement multi-publisher series support
4. Create the series metadata schema and storage mechanism
5. Develop the series management UI
6. Integrate with the LSI ACS Generator

### Phase 3.3: Enhanced Field Completion

1. Extend the LLMFieldCompleter with enhanced strategies
2. Implement specialized field completion for each required field
3. Develop the field completion reporter
4. Enhance the validation framework
5. Update the field mapping registry with new strategies
6. Integrate with the LSI ACS Generator

## Conclusion

The LSI Field Enhancement Phase 3 design builds upon the existing infrastructure to provide comprehensive ISBN management, series metadata management, and enhanced field completion. These features will significantly improve the automation and quality of LSI metadata generation, reducing manual effort and ensuring consistent, high-quality metadata for book distribution.

The modular design ensures that each component can be developed, tested, and deployed independently, while still working together seamlessly in the overall system. The robust error handling and testing strategy will ensure reliability and maintainability as the system evolves.