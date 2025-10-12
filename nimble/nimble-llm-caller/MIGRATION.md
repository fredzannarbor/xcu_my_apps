# Migration Guide

## Overview

This guide helps you migrate from older versions of nimble-llm-caller to the latest version with enhanced context management features.

## Version Compatibility

### From v0.1.x to v0.2.x (Current)

The v0.2.x series introduces intelligent context management while maintaining backward compatibility with v0.1.x APIs.

## Breaking Changes

### None for Basic Usage

**Good news!** If you're using basic LLMCaller functionality, no code changes are required. Your existing code will continue to work exactly as before.

### Optional Enhanced Features

Enhanced features are opt-in and don't affect existing code unless explicitly enabled.

## Migration Paths

### Path 1: No Changes Required (Recommended for Most Users)

If your current code works and you don't need enhanced features:

```python
# This continues to work exactly as before
from nimble_llm_caller import LLMCaller, LLMRequest

caller = LLMCaller()
request = LLMRequest(prompt_key="my_prompt", model="gpt-4")
response = caller.call(request)
```

### Path 2: Gradual Enhancement

Enable enhanced features selectively:

```python
# Old way (still works)
from nimble_llm_caller import LLMCaller

# New way with enhanced features
from nimble_llm_caller import EnhancedLLMCaller

# Enable only the features you want
caller = EnhancedLLMCaller(
    enable_context_management=True,  # Auto-upshift and chunking
    enable_file_processing=False,    # Keep disabled for now
    enable_interaction_logging=False # Keep disabled for now
)
```

### Path 3: Full Enhancement

Use all new features:

```python
from nimble_llm_caller import EnhancedLLMCaller, LLMRequest, FileAttachment

# Full-featured caller
caller = EnhancedLLMCaller(
    enable_context_management=True,
    enable_file_processing=True,
    enable_interaction_logging=True
)

# Enhanced request with file attachments
request = LLMRequest(
    prompt_key="analyze_document",
    model="gpt-4",
    file_attachments=[
        FileAttachment(file_path="document.pdf", content_type="application/pdf")
    ]
)

response = caller.call(request)
```

## Configuration Migration

### Old Configuration Format (Still Supported)

```json
{
  "models": {
    "gpt-4": {
      "provider": "openai",
      "api_key_env": "OPENAI_API_KEY",
      "default_params": {
        "temperature": 0.7
      }
    }
  }
}
```

### Enhanced Configuration Format

```json
{
  "models": {
    "gpt-4": {
      "provider": "openai",
      "api_key_env": "OPENAI_API_KEY",
      "default_params": {
        "temperature": 0.7
      },
      "capacity": {
        "max_context_tokens": 8192,
        "supports_vision": false,
        "cost_multiplier": 1.0
      }
    }
  },
  "context_management": {
    "enable_auto_upshift": true,
    "default_strategy": "upshift_first",
    "max_cost_multiplier": 3.0
  },
  "file_processing": {
    "enable_file_processing": true,
    "max_file_size": 10485760
  },
  "interaction_logging": {
    "enable_logging": true,
    "log_file_path": "llm_interactions.jsonl"
  }
}
```

### Automatic Configuration Migration

Use the ConfigManager to automatically migrate:

```python
from nimble_llm_caller import ConfigManager

# Load old configuration
config = ConfigManager("old_config.json")

# Export enhanced configuration
enhanced_config = config.export_enhanced_config()

# Save enhanced configuration
config.save_enhanced_config("new_config.json")
```

## API Changes

### New Classes (Additive)

These are new classes that don't affect existing code:

- `EnhancedLLMCaller` - Enhanced caller with context management
- `TokenEstimator` - Token counting utilities
- `ContextAnalyzer` - Context analysis
- `FileProcessor` - File processing
- `ContentChunker` - Content chunking
- `InteractionLogger` - Request/response logging

### New Request Fields (Optional)

`LLMRequest` has new optional fields:

```python
request = LLMRequest(
    prompt_key="my_prompt",
    model="gpt-4",
    # New optional fields
    file_attachments=[...],        # File attachments
    context_strategy="upshift_first",  # Context overflow strategy
    max_cost_multiplier=2.0        # Cost constraint for upshifting
)
```

### New Response Fields (Additive)

`LLMResponse` may include additional metadata:

```python
response = caller.call(request)

# New optional fields in response.metadata
if response.metadata:
    upshifted = response.metadata.get("upshifted", False)
    chunked = response.metadata.get("chunked", False)
    files_processed = response.metadata.get("files_processed", 0)
```

## Common Migration Scenarios

### Scenario 1: Large Context Handling

**Before (manual handling):**
```python
# You had to manually handle context limits
def handle_large_content(content, model):
    if len(content) > 10000:  # Rough estimate
        # Manual chunking or model switching
        return process_in_chunks(content, model)
    return normal_process(content, model)
```

**After (automatic handling):**
```python
from nimble_llm_caller import EnhancedLLMCaller

caller = EnhancedLLMCaller(enable_context_management=True)

# Automatic context management
request = LLMRequest(
    prompt_key="process_content",
    model="gpt-4",
    substitutions={"content": very_large_content}
)

# Automatically handles upshifting or chunking
response = caller.call(request)
```

### Scenario 2: File Processing

**Before (manual file handling):**
```python
# You had to manually read and process files
with open("document.pdf", "rb") as f:
    # Manual PDF processing
    content = extract_pdf_text(f)

request = LLMRequest(
    prompt_key="analyze_document",
    model="gpt-4",
    substitutions={"document_content": content}
)
```

**After (automatic file processing):**
```python
from nimble_llm_caller import EnhancedLLMCaller, FileAttachment

caller = EnhancedLLMCaller(enable_file_processing=True)

request = LLMRequest(
    prompt_key="analyze_document",
    model="gpt-4",
    file_attachments=[
        FileAttachment(file_path="document.pdf", content_type="application/pdf")
    ]
)

# Automatic file processing and context management
response = caller.call(request)
```

### Scenario 3: Request Logging

**Before (manual logging):**
```python
import logging

logger = logging.getLogger(__name__)

def call_with_logging(request):
    logger.info(f"Calling {request.model} with {request.prompt_key}")
    response = caller.call(request)
    logger.info(f"Response: {len(response.content)} characters")
    return response
```

**After (automatic logging):**
```python
from nimble_llm_caller import EnhancedLLMCaller

caller = EnhancedLLMCaller(enable_interaction_logging=True)

# Automatic detailed logging of all interactions
response = caller.call(request)

# View recent interactions
recent = caller.get_recent_interactions(10)
```

## Compatibility Utilities

### Legacy Request Format Support

If you have old dictionary-based requests:

```python
from nimble_llm_caller.compatibility import migrate_request_format

# Old format
old_request = {
    "prompt": "my_prompt",
    "llm_model": "gpt-4",
    "variables": {"key": "value"}
}

# Convert to new format
new_request = migrate_request_format(old_request)
```

### Compatibility Checking

Check if your code is compatible:

```python
from nimble_llm_caller.compatibility import check_compatibility

report = check_compatibility(your_request)
print(f"Compatible: {report['compatible']}")
print(f"Warnings: {report['warnings']}")
print(f"Recommendations: {report['recommendations']}")
```

### Global Feature Enablement (Deprecated)

For quick migration, you can globally enable enhanced features:

```python
from nimble_llm_caller.compatibility import enable_context_features_globally

# This makes all LLMCaller instances use enhanced features
# WARNING: This is deprecated and not recommended for new code
enable_context_features_globally()
```

## Testing Your Migration

### Basic Compatibility Test

```python
def test_basic_compatibility():
    from nimble_llm_caller import LLMCaller, LLMRequest
    
    caller = LLMCaller()
    request = LLMRequest(prompt_key="test", model="gpt-4")
    
    # This should work exactly as before
    response = caller.call(request)
    assert response is not None
    print("✓ Basic compatibility confirmed")

test_basic_compatibility()
```

### Enhanced Features Test

```python
def test_enhanced_features():
    from nimble_llm_caller import EnhancedLLMCaller, LLMRequest
    
    caller = EnhancedLLMCaller(
        enable_context_management=True,
        enable_file_processing=True
    )
    
    request = LLMRequest(prompt_key="test", model="gpt-4")
    response = caller.call(request)
    
    assert response is not None
    print("✓ Enhanced features working")

test_enhanced_features()
```

## Performance Considerations

### Memory Usage

Enhanced features may use more memory:

- **Token estimation**: Minimal overhead
- **File processing**: Memory usage scales with file size
- **Interaction logging**: Configurable, can be disabled
- **Context analysis**: Minimal overhead

### Startup Time

First import may be slightly slower due to additional dependencies, but runtime performance is similar or better.

### Disk Usage

Enhanced installation requires more disk space:

- Basic: ~50MB
- Enhanced: ~200MB (due to file processing libraries)

## Rollback Plan

If you need to rollback:

### Option 1: Disable Enhanced Features

```python
# Use basic caller instead of enhanced
from nimble_llm_caller import LLMCaller  # Instead of EnhancedLLMCaller

caller = LLMCaller()  # No enhanced features
```

### Option 2: Install Basic Version

```bash
pip uninstall nimble-llm-caller
pip install nimble-llm-caller  # Without [enhanced]
```

### Option 3: Version Pinning

```bash
pip install nimble-llm-caller==0.1.0  # Pin to older version
```

## Getting Help

If you encounter issues during migration:

1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review the [FAQ](FAQ.md)
3. Use the compatibility utilities to identify issues
4. Create a GitHub issue with your migration scenario

## Migration Checklist

- [ ] Backup your current working code
- [ ] Test basic functionality with new version
- [ ] Update configuration if using enhanced features
- [ ] Test file processing if using file attachments
- [ ] Verify context management behavior
- [ ] Update documentation and comments
- [ ] Train team members on new features
- [ ] Monitor performance and error rates
- [ ] Update deployment scripts if needed