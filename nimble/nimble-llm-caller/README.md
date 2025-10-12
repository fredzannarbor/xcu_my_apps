# Nimble LLM Caller

A robust, multi-model LLM calling package with **intelligent context management**, file processing, and advanced prompt handling capabilities.

## 🚀 Key Features

### Core Capabilities
- **Multi-Model Support**: Call multiple LLM providers (OpenAI, Anthropic, Google, etc.) through LiteLLM
- **Intelligent Context Management**: Automatic context-size-aware request handling with model upshifting
- **File Processing**: Support for 29+ file types (PDF, Word, images, JSON, CSV, XML, YAML, etc.)
- **Batch Processing**: Submit multiple prompts to multiple models efficiently
- **Robust JSON Parsing**: Multiple fallback strategies for parsing LLM responses
- **Retry Logic**: Exponential backoff with jitter for handling rate limits and transient errors

### Advanced Features
- **Context-Size-Aware Safe Submit**: Automatic overflow handling with model upshifting and content chunking
- **File Attachment Support**: Process and include files directly in LLM requests
- **Comprehensive Interaction Logging**: Detailed request/response tracking with metadata
- **Prompt Management**: JSON-based prompt templates with variable substitution
- **Document Assembly**: Built-in formatters for text, markdown, and LaTeX output
- **Graceful Degradation**: Fallback strategies for reliability
- **Full Backward Compatibility**: Existing code continues to work unchanged

## 📦 Installation

### Basic Installation
```bash
pip install nimble-llm-caller
```

### Enhanced Installation (Recommended)
```bash
# Install with enhanced file processing capabilities
pip install nimble-llm-caller[enhanced]
```

### All Features Installation
```bash
# Install with all optional dependencies
pip install nimble-llm-caller[all]
```

### Development Installation
```bash
# Clone the repository
git clone https://github.com/fredzannarbor/nimble-llm-caller.git
cd nimble-llm-caller

# Install in development mode with all features
pip install -e .[dev,enhanced]

# Run setup script
python setup_dev.py setup
```

### Installation Options Summary

| Installation | Command | Features |
|-------------|---------|----------|
| **Basic** | `pip install nimble-llm-caller` | Core LLM calling, basic context management |
| **Enhanced** | `pip install nimble-llm-caller[enhanced]` | + File processing (PDF, Word, images), advanced tokenization |
| **All** | `pip install nimble-llm-caller[all]` | + All optional features and dependencies |
| **Development** | `pip install -e .[dev,enhanced]` | + Testing, linting, documentation tools |

## ⚙️ Configuration

### 1. API Keys Setup
Set your API keys in environment variables:

```bash
# Required: At least one LLM provider
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"

# Optional: For enhanced features
export LITELLM_LOG="INFO"  # Enable LiteLLM logging
```

### 2. Environment File (.env)
Create a `.env` file in your project root:

```env
# LLM Provider API Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# Optional Configuration
LITELLM_LOG=INFO
NIMBLE_LOG_LEVEL=INFO
NIMBLE_DEFAULT_MODEL=gpt-4o
NIMBLE_MAX_RETRIES=3
```

### 3. Configuration File
Create a configuration file for advanced settings:

```python
# config.py
from nimble_llm_caller.models.context_config import ContextConfig, ContextStrategy

# Custom context configuration
context_config = ContextConfig(
    default_strategy=ContextStrategy.UPSHIFT,
    enable_chunking=True,
    chunk_overlap_tokens=100,
    max_cost_multiplier=3.0,
    enable_model_fallback=True
)
```

## 🚀 Quick Start

### Basic Usage (Backward Compatible)
```python
from nimble_llm_caller import LLMCaller, LLMRequest

# Traditional usage - still works!
caller = LLMCaller()
request = LLMRequest(
    prompt_key="summarize_text",
    model="gpt-4",
    substitutions={"text": "Your text here"}
)
response = caller.call(request)
print(f"Result: {response.content}")
```

### Enhanced Usage with Intelligent Context Management
```python
from nimble_llm_caller import EnhancedLLMCaller, LLMRequest, FileAttachment

# Enhanced caller with all intelligent features
caller = EnhancedLLMCaller(
    enable_context_management=True,
    enable_file_processing=True,
    enable_interaction_logging=True
)

# Request with file attachments and automatic context management
request = LLMRequest(
    prompt_key="analyze_document",
    model="gpt-4",
    file_attachments=[
        FileAttachment(file_path="document.pdf", content_type="application/pdf"),
        FileAttachment(file_path="data.csv", content_type="text/csv")
    ],
    substitutions={"analysis_type": "comprehensive"}
)

# Automatic context management, file processing, and logging
response = caller.call(request)
print(f"Analysis: {response.content}")
print(f"Files processed: {response.files_processed}")
print(f"Model used: {response.model} (original: {response.original_model})")
```

### Content Generation with File Processing
```python
from nimble_llm_caller import LLMContentGenerator

# Initialize with prompts and enhanced features
generator = LLMContentGenerator(
    prompt_file_path="prompts.json",
    enable_context_management=True,
    enable_file_processing=True
)

# Process multiple files with intelligent context handling
results = generator.call_batch(
    prompt_keys=["summarize_document", "extract_key_points"],
    models=["gpt-4o", "claude-3-sonnet"],
    shared_substitutions={
        "files": ["report.pdf", "data.xlsx", "presentation.pptx"]
    }
)

print(f"Success rate: {results.success_rate:.1f}%")
print(f"Total files processed: {sum(r.files_processed for r in results.responses)}")
```

## 📋 Usage Examples

### 1. Context-Size-Aware Processing
```python
from nimble_llm_caller import EnhancedLLMCaller, LLMRequest

caller = EnhancedLLMCaller(enable_context_management=True)

# Large content that might exceed context limits
large_content = "..." * 50000  # Very large text

request = LLMRequest(
    prompt_key="analyze_content",
    model="gpt-5-mini",  # Will automatically upshift if needed
    substitutions={"content": large_content}
)

# Automatic handling: upshift to gpt-4-turbo or chunk content
response = caller.call(request)

if response.upshift_reason:
    print(f"Upshifted from {response.original_model} to {response.model}")
    print(f"Reason: {response.upshift_reason}")

if response.was_chunked:
    print(f"Content was chunked: {response.chunk_info}")
```

### 2. File Processing with Multiple Formats
```python
from nimble_llm_caller import EnhancedLLMCaller, LLMRequest, FileAttachment

caller = EnhancedLLMCaller(
    enable_file_processing=True,
    enable_context_management=True
)

# Process multiple file types
files = [
    FileAttachment("report.pdf", content_type="application/pdf"),
    FileAttachment("data.xlsx", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    FileAttachment("image.png", content_type="image/png"),
    FileAttachment("config.yaml", content_type="application/x-yaml")
]

request = LLMRequest(
    prompt_key="comprehensive_analysis",
    model="gpt-4o",  # Vision-capable model for images
    file_attachments=files
)

response = caller.call(request)
print(f"Processed {response.files_processed} files")
print(f"Analysis: {response.content}")
```

### 3. Interaction Logging and Monitoring
```python
from nimble_llm_caller import EnhancedLLMCaller

# Enable comprehensive logging
caller = EnhancedLLMCaller(
    enable_interaction_logging=True,
    log_file_path="llm_interactions.log",
    log_content=True,
    log_metadata=True
)

# Make requests - all interactions are logged
response = caller.call(request)

# Access recent interactions
recent = caller.interaction_logger.get_recent_interactions(count=5)
for interaction in recent:
    print(f"Request: {interaction.prompt_key} -> {interaction.model}")
    print(f"Duration: {interaction.duration_ms}ms")
    print(f"Tokens: {interaction.token_usage}")

# Get statistics
stats = caller.interaction_logger.get_statistics()
print(f"Total requests: {stats['total_requests']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
print(f"Average duration: {stats['avg_duration_ms']:.1f}ms")
```

### 4. Custom Context Strategies
```python
from nimble_llm_caller import EnhancedLLMCaller, ContextConfig, ContextStrategy

# Custom context configuration
config = ContextConfig(
    default_strategy=ContextStrategy.CHUNK,  # Prefer chunking over upshifting
    enable_chunking=True,
    chunk_overlap_tokens=200,
    max_cost_multiplier=2.0,  # Limit cost increases
    enable_model_fallback=True
)

caller = EnhancedLLMCaller(
    enable_context_management=True,
    context_config=config
)

# Requests will use chunking strategy when context limits are exceeded
response = caller.call(large_request)
```

### 5. Batch Processing with Context Management
```python
from nimble_llm_caller import LLMContentGenerator

generator = LLMContentGenerator(
    prompt_file_path="prompts.json",
    enable_context_management=True,
    enable_file_processing=True
)

# Batch process with automatic context handling
results = generator.call_batch(
    prompt_keys=["analyze_document", "extract_insights", "generate_summary"],
    models=["gpt-4o", "claude-3-sonnet", "gemini-1.5-pro"],
    shared_substitutions={
        "documents": ["doc1.pdf", "doc2.docx", "doc3.txt"]
    },
    parallel=True,
    max_concurrent=3
)

# Results include context management information
for response in results.responses:
    print(f"Prompt: {response.prompt_key}")
    print(f"Model: {response.model} (original: {response.original_model})")
    print(f"Strategy: {response.context_strategy_used}")
    print(f"Files: {response.files_processed}")
    print("---")
```

## 📝 Prompt Format

### Basic Prompt Structure
```json
{
  "prompt_keys": ["summarize_text", "analyze_document"],
  "summarize_text": {
    "messages": [
      {
        "role": "system",
        "content": "You are a professional summarizer."
      },
      {
        "role": "user", 
        "content": "Summarize this text: {text}"
      }
    ],
    "params": {
      "temperature": 0.3,
      "max_tokens": 1000
    }
  }
}
```

### Enhanced Prompt with File Processing
```json
{
  "analyze_document": {
    "messages": [
      {
        "role": "system",
        "content": "You are a document analyst. Analyze the provided files and give insights."
      },
      {
        "role": "user",
        "content": "Please analyze the attached files and provide {analysis_type} analysis. Focus on: {focus_areas}"
      }
    ],
    "params": {
      "temperature": 0.2,
      "max_tokens": 2000
    },
    "supports_files": true,
    "supports_vision": true
  }
}
```

## 🔧 Advanced Configuration

### Context Management Settings
```python
from nimble_llm_caller.models.context_config import ContextConfig, ContextStrategy

# Fine-tune context management
config = ContextConfig(
    # Strategy when context limit is exceeded
    default_strategy=ContextStrategy.UPSHIFT,  # or CHUNK, TRUNCATE, ERROR
    
    # Chunking settings
    enable_chunking=True,
    chunk_overlap_tokens=100,
    max_chunks=10,
    
    # Model upshifting settings
    enable_model_upshifting=True,
    max_cost_multiplier=3.0,
    enable_model_fallback=True,
    
    # Safety margins
    context_buffer_tokens=500,
    enable_token_estimation=True
)
```

### File Processing Configuration
```python
from nimble_llm_caller.core.file_processor import FileProcessor

# Custom file processor
processor = FileProcessor(
    max_file_size_mb=50,
    supported_formats=[
        "pdf", "docx", "txt", "md", "json", "csv", 
        "xlsx", "png", "jpg", "yaml", "xml"
    ],
    extract_metadata=True,
    preserve_formatting=True
)
```

### Logging Configuration
```python
from nimble_llm_caller.core.interaction_logger import InteractionLogger

# Custom interaction logger
logger = InteractionLogger(
    log_file_path="interactions.jsonl",
    log_content=True,
    log_metadata=True,
    async_logging=True,
    max_log_size_mb=100,
    max_files=10
)
```

## 🔍 Monitoring and Debugging

### Access Interaction Logs
```python
# Get recent interactions
recent = caller.interaction_logger.get_recent_interactions(count=10)

# Filter by model
gpt4_interactions = caller.interaction_logger.get_interactions_by_model("gpt-4o")

# Filter by time range
from datetime import datetime, timedelta
since = datetime.now() - timedelta(hours=1)
recent_hour = caller.interaction_logger.get_interactions_since(since)
```

### Performance Statistics
```python
stats = caller.interaction_logger.get_statistics()
print(f"""
Performance Statistics:
- Total Requests: {stats['total_requests']}
- Success Rate: {stats['success_rate']:.1f}%
- Average Duration: {stats['avg_duration_ms']:.1f}ms
- Total Tokens: {stats['total_tokens']}
- Average Cost: ${stats['avg_cost']:.4f}
""")
```

### Error Analysis
```python
# Get failed requests
failed = caller.interaction_logger.get_failed_interactions()
for failure in failed:
    print(f"Failed: {failure.prompt_key} -> {failure.error}")
    print(f"Model: {failure.model}, Duration: {failure.duration_ms}ms")
```

## 🔄 Migration Guide

### From v0.1.x to v0.2.x
Your existing code continues to work unchanged! New features are opt-in:

```python
# Old code (still works)
from nimble_llm_caller import LLMCaller, LLMRequest
caller = LLMCaller()
response = caller.call(request)

# New enhanced features (optional)
from nimble_llm_caller import EnhancedLLMCaller
caller = EnhancedLLMCaller(
    enable_context_management=True,
    enable_file_processing=True
)
```

See [MIGRATION.md](MIGRATION.md) for detailed migration instructions.

## 📚 Documentation

- **[Installation Guide](INSTALLATION.md)**: Detailed installation instructions
- **[Migration Guide](MIGRATION.md)**: Upgrading from previous versions  
- **[API Reference](docs/api/)**: Complete API documentation
- **[Examples](examples/)**: Working code examples
- **[Configuration](docs/configuration.md)**: Advanced configuration options

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/nimblebooks/nimble-llm-caller/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nimblebooks/nimble-llm-caller/discussions)
- **Documentation**: [Full Documentation](https://nimble-llm-caller.readthedocs.io)

## 🏷️ Version

Current version: **0.2.2** - Intelligent Context Management Release

### Recent Updates
- 📖 **v0.2.2**: Improved README
- ✅ **v0.2.1**: Bug fixes for InteractionLogger
- 🚀 **v0.2.0**: Intelligent context management, file processing, enhanced logging
- 📦 **v0.1.0**: Initial release with basic LLM calling capabilities