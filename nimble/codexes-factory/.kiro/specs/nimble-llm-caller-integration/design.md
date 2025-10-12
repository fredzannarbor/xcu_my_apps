# Nimble LLM Caller Integration Design

## Integration Architecture

### Current State Analysis

The codexes-factory project currently has LLM calling functionality in:
- `src/codexes/core/llm_caller.py` - Main LLM calling functions
- Various modules that import and use these functions
- Prompts scattered in different formats across the project
- Configuration mixed with business logic

### Target Architecture

```
codexes-factory/
├── requirements.txt (updated with nimble-llm-caller)
├── src/codexes/
│   ├── core/
│   │   ├── llm_integration.py (new - wrapper/adapter)
│   │   └── llm_caller.py (deprecated - to be removed)
│   ├── config/
│   │   └── llm_config.json (new - centralized LLM config)
│   └── prompts/
│       └── codexes_prompts.json (new - migrated prompts)
└── nimble-llm-caller/ (external package)
```

## Migration Strategy

### Phase 1: Package Installation and Setup

1. **Install nimble-llm-caller**
   - Add to requirements.txt
   - Install in development environment
   - Verify compatibility

2. **Create Integration Layer**
   - Create `src/codexes/core/llm_integration.py`
   - Provide compatibility wrapper for existing code
   - Maintain existing API interfaces

3. **Setup Configuration**
   - Create centralized LLM configuration file
   - Migrate existing configuration settings
   - Setup environment variables for API keys

### Phase 2: Prompt Migration

1. **Analyze Existing Prompts**
   - Identify all prompts in the codebase
   - Document current format and usage
   - Plan migration to JSON format

2. **Create Centralized Prompt File**
   - Convert prompts to nimble-llm-caller JSON format
   - Organize by functional area
   - Add proper metadata and parameters

3. **Update Prompt Loading**
   - Use nimble-llm-caller PromptManager
   - Update code to reference prompt keys
   - Test prompt substitution and formatting

### Phase 3: Core Function Migration

1. **Replace Core LLM Functions**
   - Update `call_model_with_prompt` function
   - Update `get_responses_from_multiple_models` function
   - Maintain backward compatibility

2. **Update Error Handling**
   - Use nimble-llm-caller error handling patterns
   - Improve retry logic and recovery
   - Enhance logging and monitoring

3. **Test Core Functionality**
   - Unit tests for new integration layer
   - Integration tests with real API calls
   - Performance benchmarking

### Phase 4: Module-by-Module Migration

1. **Identify Usage Patterns**
   - Find all modules using LLM functionality
   - Document current usage patterns
   - Plan migration approach for each

2. **Update High-Priority Modules**
   - Start with most critical modules
   - Update imports and function calls
   - Test functionality thoroughly

3. **Batch Update Remaining Modules**
   - Update remaining modules systematically
   - Ensure consistent patterns across codebase
   - Update tests and documentation

### Phase 5: Cleanup and Optimization

1. **Remove Deprecated Code**
   - Remove old `llm_caller.py` file
   - Clean up unused imports
   - Remove duplicate functionality

2. **Optimize Configuration**
   - Consolidate configuration files
   - Optimize for performance
   - Add monitoring and analytics

3. **Update Documentation**
   - Update API documentation
   - Create migration guide
   - Update examples and tutorials

## Integration Components

### LLM Integration Wrapper

```python
# src/codexes/core/llm_integration.py

from nimble_llm_caller import LLMContentGenerator, ConfigManager
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class CodexesLLMIntegration:
    """Integration wrapper for nimble-llm-caller in codexes-factory."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigManager(config_path)
        self.content_generator = LLMContentGenerator(
            prompt_file_path="src/codexes/prompts/codexes_prompts.json",
            config_manager=self.config_manager
        )
    
    def call_model_with_prompt(
        self, 
        model_name: str, 
        prompt_config: Dict[str, Any], 
        **kwargs
    ) -> Dict[str, Any]:
        """Backward compatibility wrapper for existing code."""
        # Convert old format to new format
        # Call nimble-llm-caller
        # Return in expected format
        pass
    
    def get_responses_from_multiple_models(
        self,
        prompt_configs: List[Dict[str, Any]],
        models: List[str],
        **kwargs
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Backward compatibility wrapper for batch calls."""
        # Convert old format to new format
        # Call nimble-llm-caller batch processing
        # Return in expected format
        pass
```

### Configuration Migration

```json
// src/codexes/config/llm_config.json
{
  "models": {
    "gpt-4o": {
      "provider": "openai",
      "api_key_env": "OPENAI_API_KEY",
      "default_params": {
        "temperature": 0.7,
        "max_tokens": 4000
      },
      "retry_config": {
        "max_retries": 3,
        "base_delay": 1.0,
        "max_delay": 60.0
      }
    },
    "claude-3-sonnet": {
      "provider": "anthropic", 
      "api_key_env": "ANTHROPIC_API_KEY",
      "default_params": {
        "temperature": 0.7,
        "max_tokens": 4000
      }
    }
  },
  "output": {
    "default_format": "json",
    "save_raw_responses": true,
    "output_directory": "./output/llm_responses"
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

### Prompt Migration Format

```json
// src/codexes/prompts/codexes_prompts.json
{
  "book_metadata_extraction": {
    "messages": [
      {
        "role": "system",
        "content": "You are an expert at extracting structured metadata from book content."
      },
      {
        "role": "user",
        "content": "Extract metadata from this book content:\n\n{content}\n\nReturn JSON with title, author, summary, keywords, and genre."
      }
    ],
    "params": {
      "temperature": 0.3,
      "max_tokens": 1000
    }
  },
  "lsi_field_completion": {
    "messages": [
      {
        "role": "system", 
        "content": "You are an expert at completing LSI (Lightning Source Inc.) metadata fields for book publishing."
      },
      {
        "role": "user",
        "content": "Complete the missing LSI fields for this book:\n\nExisting data: {existing_data}\n\nMissing fields: {missing_fields}\n\nReturn JSON with completed field values."
      }
    ],
    "params": {
      "temperature": 0.2,
      "max_tokens": 2000
    }
  }
}
```

## Implementation Plan

### Step 1: Environment Setup
```bash
# Add nimble-llm-caller to requirements
echo "nimble-llm-caller>=0.1.0" >> requirements.txt

# Install in development environment
pip install -r requirements.txt

# Verify installation
python -c "from nimble_llm_caller import LLMContentGenerator; print('✅ Installation successful')"
```

### Step 2: Create Integration Layer
1. Create `src/codexes/core/llm_integration.py`
2. Implement backward compatibility wrappers
3. Create configuration files
4. Test basic functionality

### Step 3: Migrate Prompts
1. Analyze existing prompts in codebase
2. Convert to JSON format
3. Test prompt loading and substitution
4. Update prompt references in code

### Step 4: Update Core Functions
1. Replace implementation in existing functions
2. Maintain API compatibility
3. Add comprehensive error handling
4. Test with existing code

### Step 5: Module Updates
1. Update imports across codebase
2. Test each module individually
3. Update tests and documentation
4. Performance validation

### Step 6: Cleanup
1. Remove deprecated code
2. Optimize configuration
3. Update documentation
4. Final testing and validation

## Testing Strategy

### Unit Tests
- Test integration wrapper functions
- Test prompt loading and formatting
- Test configuration management
- Test error handling scenarios

### Integration Tests
- Test with real API calls
- Test batch processing
- Test error recovery
- Test performance benchmarks

### Regression Tests
- Ensure all existing functionality works
- Compare outputs with previous implementation
- Validate performance metrics
- Test edge cases and error conditions

## Rollback Plan

If issues are discovered during integration:

1. **Immediate Rollback**
   - Revert to previous git commit
   - Restore original LLM calling code
   - Verify functionality restored

2. **Partial Rollback**
   - Keep nimble-llm-caller installed
   - Revert specific modules to old implementation
   - Fix issues and re-migrate incrementally

3. **Configuration Rollback**
   - Restore original configuration files
   - Revert environment variable changes
   - Test with original settings

## Success Criteria

- ✅ All existing LLM functionality works through nimble-llm-caller
- ✅ No regression in performance or reliability
- ✅ Improved error handling and logging
- ✅ Reduced code duplication
- ✅ Easier testing and debugging
- ✅ Better separation of concerns
- ✅ Comprehensive documentation updated