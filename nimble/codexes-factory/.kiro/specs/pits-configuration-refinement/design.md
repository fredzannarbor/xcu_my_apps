# PITS Configuration Refinement Design

## Overview

This design refines the existing PITS (Publisher, Imprint, Tranche, Series) configuration system to provide a robust, scalable, and maintainable multi-tenant publishing platform. The system builds upon the existing partial implementation while addressing inconsistencies, adding missing functionality, and improving developer experience.

## Architecture

### Current State Analysis

The system currently has:
```
configs/
├── publishers/          # Publisher-level configs
├── imprints/           # Imprint-level configs  
├── tranches/           # Tranche-level configs
├── default_lsi_config.json
└── llm_monitoring_config.json

imprints/
├── xynapse_traces/     # Imprint assets (templates, scripts)
├── admin/              # Another imprint
└── jp_cross/           # Another imprint
```

### Target Architecture

```
configs/
├── system/
│   ├── default_lsi_config.json
│   ├── llm_monitoring_config.json
│   └── schema/
│       ├── publisher.schema.json
│       ├── imprint.schema.json
│       ├── tranche.schema.json
│       └── series.schema.json
├── publishers/
│   ├── nimble_books/
│   │   ├── publisher.json
│   │   ├── imprints/
│   │   │   ├── xynapse_traces/
│   │   │   │   ├── imprint.json
│   │   │   │   ├── assets/
│   │   │   │   │   ├── templates/
│   │   │   │   │   ├── prompts/
│   │   │   │   │   └── scripts/
│   │   │   │   ├── tranches/
│   │   │   │   │   └── tranche_1/
│   │   │   │   │       ├── tranche.json
│   │   │   │   │       └── series/
│   │   │   │   │           └── ai_philosophy/
│   │   │   │   │               └── series.json
│   │   │   │   └── data/
│   │   │   │       ├── books.csv
│   │   │   │       └── schedule.json
│   │   │   └── admin/
│   │   │       └── [similar structure]
│   │   └── global/
│   │       ├── lsi_config.json
│   │       └── model_params.json
│   └── templates/
│       ├── publisher_template.json
│       ├── imprint_template.json
│       ├── tranche_template.json
│       └── series_template.json
```

## Components and Interfaces

### Core Configuration Manager

```python
class PITSConfigurationManager:
    """Central manager for PITS configuration hierarchy."""
    
    def __init__(self, config_root: Path = Path("configs")):
        self.config_root = config_root
        self.cache = {}
        self.schema_validator = ConfigSchemaValidator()
    
    def get_configuration(self, 
                         publisher: str, 
                         imprint: str = None, 
                         tranche: str = None, 
                         series: str = None) -> PITSConfiguration:
        """Get merged configuration for specified entity."""
        pass
    
    def validate_configuration(self, config_path: Path) -> ValidationResult:
        """Validate configuration file against schema."""
        pass
    
    def reload_configuration(self, entity_path: str) -> None:
        """Reload specific configuration and invalidate cache."""
        pass
```

### Configuration Inheritance Engine

```python
class ConfigurationInheritanceEngine:
    """Handles configuration merging and inheritance."""
    
    def merge_configurations(self, 
                           configs: List[Dict[str, Any]], 
                           merge_strategy: MergeStrategy = MergeStrategy.CHILD_OVERRIDES) -> Dict[str, Any]:
        """Merge configurations according to inheritance rules."""
        pass
    
    def resolve_inheritance_chain(self, 
                                publisher: str, 
                                imprint: str = None, 
                                tranche: str = None, 
                                series: str = None) -> List[Path]:
        """Resolve the inheritance chain for given entity."""
        pass
    
    def validate_inheritance_chain(self, chain: List[Path]) -> ValidationResult:
        """Validate inheritance chain for circular dependencies."""
        pass
```

### Asset Management System

```python
class PITSAssetManager:
    """Manages imprint-specific assets and templates."""
    
    def get_asset_path(self, 
                      publisher: str, 
                      imprint: str, 
                      asset_type: AssetType, 
                      asset_name: str) -> Path:
        """Get path to specific asset with fallback logic."""
        pass
    
    def copy_template_assets(self, 
                           source_imprint: str, 
                           target_imprint: str) -> None:
        """Copy assets from template or existing imprint."""
        pass
    
    def validate_assets(self, publisher: str, imprint: str) -> ValidationResult:
        """Validate that required assets exist."""
        pass
```

## Data Models

### Configuration Entities

```python
@dataclass
class PITSConfiguration:
    """Merged configuration for a specific PITS entity."""
    publisher: str
    imprint: Optional[str] = None
    tranche: Optional[str] = None
    series: Optional[str] = None
    
    # Merged configuration data
    lsi_config: Dict[str, Any] = field(default_factory=dict)
    llm_config: Dict[str, Any] = field(default_factory=dict)
    publishing_config: Dict[str, Any] = field(default_factory=dict)
    asset_paths: Dict[str, Path] = field(default_factory=dict)
    
    # Metadata
    inheritance_chain: List[Path] = field(default_factory=list)
    last_modified: datetime = field(default_factory=datetime.now)
    
    def get_asset_path(self, asset_type: str, asset_name: str) -> Path:
        """Get path to specific asset."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        pass

@dataclass
class PublisherConfiguration:
    """Publisher-level configuration."""
    name: str
    display_name: str
    contact_info: Dict[str, str]
    default_settings: Dict[str, Any]
    branding: Dict[str, Any]
    
    # Global publisher settings
    territory_rights: str = "World"
    return_policy: str = "Standard"
    discount_code: str = "45"

@dataclass
class ImprintConfiguration:
    """Imprint-level configuration."""
    name: str
    display_name: str
    publisher: str
    
    # Imprint-specific overrides
    branding: Dict[str, Any] = field(default_factory=dict)
    publishing_settings: Dict[str, Any] = field(default_factory=dict)
    asset_overrides: Dict[str, str] = field(default_factory=dict)
    
    # Workflow configuration
    prepress_workflow: str = "standard"
    cover_workflow: str = "standard"
    distribution_workflow: str = "standard"

@dataclass
class TrancheConfiguration:
    """Tranche-level configuration."""
    name: str
    display_name: str
    publisher: str
    imprint: str
    
    # Tranche-specific settings
    publication_schedule: Dict[str, Any] = field(default_factory=dict)
    isbn_block: Optional[str] = None
    pricing_strategy: str = "standard"
    
    # Content configuration
    content_guidelines: Dict[str, Any] = field(default_factory=dict)
    quality_standards: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SeriesConfiguration:
    """Series-level configuration."""
    name: str
    display_name: str
    publisher: str
    imprint: str
    tranche: str
    
    # Series-specific settings
    series_metadata: Dict[str, Any] = field(default_factory=dict)
    numbering_scheme: str = "sequential"
    branding_overrides: Dict[str, Any] = field(default_factory=dict)
```

### Configuration Schema

```json
{
  "publisher_schema": {
    "type": "object",
    "required": ["name", "display_name", "contact_info"],
    "properties": {
      "name": {"type": "string", "pattern": "^[a-z_]+$"},
      "display_name": {"type": "string"},
      "contact_info": {
        "type": "object",
        "required": ["email"],
        "properties": {
          "email": {"type": "string", "format": "email"},
          "website": {"type": "string", "format": "uri"},
          "address": {"type": "string"}
        }
      },
      "default_settings": {"type": "object"},
      "branding": {"type": "object"}
    }
  },
  "imprint_schema": {
    "type": "object",
    "required": ["name", "display_name", "publisher"],
    "properties": {
      "name": {"type": "string", "pattern": "^[a-z_]+$"},
      "display_name": {"type": "string"},
      "publisher": {"type": "string"},
      "branding": {"type": "object"},
      "publishing_settings": {"type": "object"},
      "asset_overrides": {"type": "object"}
    }
  }
}
```

## Error Handling

### Configuration Loading Errors

1. **Missing Configuration Files**
   - Fallback to parent configuration
   - Log warnings for missing optional configs
   - Fail fast for missing required configs

2. **Invalid JSON/Schema Errors**
   - Provide detailed validation error messages
   - Show file path and line number for JSON errors
   - Suggest corrections for common schema violations

3. **Circular Dependency Detection**
   - Detect inheritance loops during chain resolution
   - Provide clear error messages showing the circular path
   - Prevent infinite recursion with cycle detection

### Asset Management Errors

1. **Missing Assets**
   - Fallback to template assets
   - Log warnings for missing optional assets
   - Fail with clear messages for required assets

2. **Asset Conflicts**
   - Detect conflicting asset names across imprints
   - Provide resolution strategies
   - Log conflicts for manual resolution

## Testing Strategy

### Unit Testing

1. **Configuration Loading Tests**
   - Test individual configuration file loading
   - Test schema validation
   - Test error handling for malformed files

2. **Inheritance Engine Tests**
   - Test configuration merging logic
   - Test inheritance chain resolution
   - Test circular dependency detection

3. **Asset Management Tests**
   - Test asset path resolution
   - Test fallback mechanisms
   - Test asset copying and templating

### Integration Testing

1. **End-to-End Configuration Tests**
   - Test complete PITS hierarchy loading
   - Test configuration changes and cache invalidation
   - Test performance with large configuration sets

2. **Migration Testing**
   - Test migration from current structure
   - Test backward compatibility
   - Test migration rollback scenarios

### Performance Testing

1. **Configuration Loading Performance**
   - Benchmark configuration loading times
   - Test cache effectiveness
   - Test memory usage with large configurations

2. **Scalability Testing**
   - Test with multiple publishers/imprints
   - Test concurrent configuration access
   - Test configuration hot-reloading performance

## Migration Strategy

### Phase 1: Schema and Validation
1. Create configuration schemas
2. Implement validation framework
3. Add validation to existing configurations

### Phase 2: Inheritance Engine
1. Implement configuration merging logic
2. Add inheritance chain resolution
3. Test with existing configurations

### Phase 3: Asset Reorganization
1. Move imprint assets to new structure
2. Update asset path resolution
3. Implement fallback mechanisms

### Phase 4: Integration and Testing
1. Integrate with existing systems
2. Add comprehensive testing
3. Performance optimization

### Phase 5: Migration Tools and Documentation
1. Create migration utilities
2. Add CLI tools for configuration management
3. Complete documentation and examples

## Security Considerations

### Configuration Security
- Validate all configuration inputs
- Sanitize file paths to prevent directory traversal
- Implement access controls for configuration modification
- Audit configuration changes

### Asset Security
- Validate asset file types and contents
- Prevent asset path injection attacks
- Implement secure asset copying mechanisms
- Monitor asset access patterns

## Performance Optimization

### Caching Strategy
- Cache parsed configurations in memory
- Implement cache invalidation on file changes
- Use lazy loading for large configuration sets
- Provide cache warming for critical paths

### I/O Optimization
- Batch configuration file reads
- Use efficient JSON parsing libraries
- Implement configuration file watching
- Optimize asset path resolution

## Deployment Considerations

### Configuration Management
- Version control for all configurations
- Configuration deployment pipelines
- Environment-specific configuration overrides
- Configuration backup and recovery

### Monitoring and Observability
- Configuration loading metrics
- Error rate monitoring
- Performance dashboards
- Configuration change auditing