# Nimble LLM Caller Package Design

## Package Architecture

### Package Name: `nimble-llm-caller`

```
nimble-llm-caller/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── src/
│   └── nimble_llm_caller/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── llm_caller.py          # Multi-model LLM interface
│       │   ├── prompt_manager.py      # JSON prompt handling
│       │   ├── config_manager.py      # Configuration & secrets
│       │   └── retry_handler.py       # Retry logic & error handling
│       ├── engines/
│       │   ├── __init__.py
│       │   ├── content_engine.py      # High-level content generation
│       │   ├── batch_processor.py     # Multi-prompt batch jobs
│       │   └── reprompt_manager.py    # Reprompting with context
│       ├── exporters/
│       │   ├── __init__.py
│       │   ├── json_exporter.py       # JSON result handling
│       │   ├── text_exporter.py       # Plain text export
│       │   ├── markdown_exporter.py   # Markdown export
│       │   ├── latex_exporter.py      # LaTeX export
│       │   └── document_assembler.py  # Document assembly
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base_model.py          # Base model interface
│       │   ├── openai_model.py        # OpenAI integration
│       │   ├── anthropic_model.py     # Anthropic integration
│       │   ├── google_model.py        # Google integration
│       │   └── model_registry.py      # Model registration
│       └── utils/
│           ├── __init__.py
│           ├── logging_utils.py       # Logging configuration
│           ├── validation_utils.py    # Input validation
│           └── file_utils.py          # File operations
├── tests/
│   ├── __init__.py
│   ├── test_core/
│   ├── test_engines/
│   ├── test_exporters/
│   ├── test_models/
│   └── fixtures/
├── examples/
│   ├── basic_usage.py
│   ├── batch_processing.py
│   ├── reprompting_example.py
│   └── export_formats.py
└── docs/
    ├── api_reference.md
    ├── configuration.md
    ├── examples.md
    └── migration_guide.md
```

## Core API Design

### High-Level Interface

```python
from nimble_llm_caller import ContentEngine

# Simple usage
engine = ContentEngine()
result = engine.generate_content(
    prompt="Write a summary of quantum computing",
    model="gpt-4o",
    output_format="markdown"
)

# Batch processing
results = engine.batch_generate(
    prompts_file="prompts.json",
    models=["gpt-4o", "claude-3-sonnet"],
    output_dir="results/"
)

# Advanced usage with reprompting
context = engine.create_context()
first_result = engine.generate_with_context(
    context=context,
    prompt_key="initial_analysis",
    substitutions={"topic": "AI ethics"}
)

second_result = engine.generate_with_context(
    context=context,
    prompt_key="detailed_analysis",
    previous_results=[first_result]
)
```

### Core Components

#### 1. LLM Caller (`core/llm_caller.py`)

```python
class LLMCaller:
    """Multi-model LLM interface with retry logic"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.models = ModelRegistry()
        self.retry_handler = RetryHandler()
    
    async def call_model(
        self,
        model_name: str,
        messages: List[Dict],
        parameters: Optional[Dict] = None,
        response_format: str = "json_object"
    ) -> ModelResponse:
        """Call a specific model with retry logic"""
    
    async def batch_call(
        self,
        requests: List[ModelRequest]
    ) -> List[ModelResponse]:
        """Process multiple requests concurrently"""
```

#### 2. Prompt Manager (`core/prompt_manager.py`)

```python
class PromptManager:
    """JSON-based prompt handling with substitutions"""
    
    def load_prompts(
        self,
        prompt_file: str,
        prompt_keys: List[str]
    ) -> Dict[str, PromptConfig]:
        """Load and validate prompts from JSON"""
    
    def prepare_prompts(
        self,
        prompts: Dict[str, PromptConfig],
        substitutions: Dict[str, Any]
    ) -> List[PreparedPrompt]:
        """Apply substitutions and prepare for LLM"""
```

#### 3. Content Engine (`engines/content_engine.py`)

```python
class ContentEngine:
    """High-level content generation interface"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = ConfigManager(config_path)
        self.llm_caller = LLMCaller(self.config)
        self.prompt_manager = PromptManager()
        self.exporters = ExporterRegistry()
    
    def generate_content(
        self,
        prompt: Union[str, Dict],
        model: str,
        output_format: str = "json",
        **kwargs
    ) -> ContentResult:
        """Generate content with single prompt"""
    
    def batch_generate(
        self,
        prompts_file: str,
        models: List[str],
        output_dir: str,
        **kwargs
    ) -> BatchResult:
        """Generate content with multiple prompts and models"""
```

## Configuration System

### Configuration File Structure

```json
{
  "models": {
    "gpt-4o": {
      "provider": "openai",
      "api_key_env": "OPENAI_API_KEY",
      "default_params": {
        "temperature": 0.7,
        "max_tokens": 2000
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
        "max_tokens": 2000
      }
    }
  },
  "output": {
    "default_format": "json",
    "save_raw_responses": true,
    "timestamp_results": true
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

### Prompt File Structure

```json
{
  "analyze_topic": {
    "messages": [
      {
        "role": "system",
        "content": "You are an expert analyst."
      },
      {
        "role": "user",
        "content": "Analyze the following topic: {topic}\\n\\nProvide insights on: {focus_areas}"
      }
    ],
    "params": {
      "temperature": 0.5,
      "max_tokens": 1500
    },
    "output_schema": {
      "type": "object",
      "properties": {
        "analysis": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "recommendations": {"type": "array", "items": {"type": "string"}}
      }
    }
  },
  "expand_analysis": {
    "messages": [
      {
        "role": "user",
        "content": "Based on this previous analysis:\\n{previous_analysis}\\n\\nProvide a detailed expansion focusing on: {expansion_focus}"
      }
    ],
    "depends_on": ["analyze_topic"]
  }
}
```

## Data Models

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

@dataclass
class ModelRequest:
    model_name: str
    messages: List[Dict[str, str]]
    parameters: Optional[Dict[str, Any]] = None
    response_format: str = "json_object"
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ModelResponse:
    request: ModelRequest
    content: Union[str, Dict[str, Any]]
    raw_response: str
    execution_time: float
    timestamp: datetime
    success: bool
    error: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None

@dataclass
class ContentResult:
    prompt_key: str
    model_name: str
    response: ModelResponse
    exported_formats: Dict[str, str]  # format -> file_path
    metadata: Dict[str, Any]

@dataclass
class BatchResult:
    results: List[ContentResult]
    summary: Dict[str, Any]
    output_directory: str
    execution_time: float
```

## Export System

### Exporter Interface

```python
class BaseExporter:
    """Base class for all exporters"""
    
    def export(
        self,
        content: Union[str, Dict],
        output_path: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Export content to specified format"""
        raise NotImplementedError

class MarkdownExporter(BaseExporter):
    """Export content to Markdown format"""
    
    def export(self, content, output_path, metadata=None):
        # Convert structured content to Markdown
        pass

class LaTeXExporter(BaseExporter):
    """Export content to LaTeX format"""
    
    def export(self, content, output_path, metadata=None):
        # Convert structured content to LaTeX
        pass
```

## Security & Secrets Management

```python
class ConfigManager:
    """Secure configuration and secrets management"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config()
        self.config = self._load_config()
        self._validate_config()
    
    def get_api_key(self, provider: str) -> str:
        """Securely retrieve API key from environment"""
        env_var = self.config["models"][provider]["api_key_env"]
        api_key = os.getenv(env_var)
        if not api_key:
            raise ConfigurationError(f"API key not found in environment variable: {env_var}")
        return api_key
    
    def get_model_params(
        self,
        model_name: str,
        prompt_params: Optional[Dict] = None,
        call_params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Merge parameters with proper precedence"""
        # call_params > prompt_params > model_defaults
        pass
```

## Migration Strategy

### Step 1: Extract Core Components
1. Copy `llm_caller.py` and `prompt_manager.py`
2. Create clean interfaces
3. Add proper error handling
4. Implement configuration system

### Step 2: Create High-Level API
1. Implement `ContentEngine` class
2. Add batch processing capabilities
3. Create export system
4. Add reprompting support

### Step 3: Package for Distribution
1. Create proper package structure
2. Add comprehensive tests
3. Write documentation
4. Set up CI/CD for PyPI

### Step 4: Integration
1. Update existing projects
2. Remove duplicate code
3. Validate functionality
4. Performance testing

## Usage Examples

### Basic Content Generation

```python
from nimble_llm_caller import ContentEngine

engine = ContentEngine()

# Simple text generation
result = engine.generate_content(
    prompt="Explain quantum computing in simple terms",
    model="gpt-4o",
    output_format="markdown"
)

print(result.exported_formats["markdown"])  # Path to markdown file
```

### Batch Processing with JSON Prompts

```python
# prompts.json
{
  "introduction": {
    "messages": [{"role": "user", "content": "Write an introduction to {topic}"}]
  },
  "detailed_analysis": {
    "messages": [{"role": "user", "content": "Provide detailed analysis of {topic}"}]
  }
}

# Python code
results = engine.batch_generate(
    prompts_file="prompts.json",
    models=["gpt-4o", "claude-3-sonnet"],
    substitutions={"topic": "artificial intelligence"},
    output_dir="ai_analysis/",
    export_formats=["json", "markdown", "latex"]
)
```

### Reprompting with Context

```python
context = engine.create_context()

# First round
analysis = engine.generate_with_context(
    context=context,
    prompt_key="initial_analysis",
    model="gpt-4o",
    substitutions={"topic": "climate change"}
)

# Second round using first result
detailed = engine.generate_with_context(
    context=context,
    prompt_key="expand_analysis",
    model="claude-3-sonnet",
    substitutions={
        "previous_analysis": analysis.response.content,
        "expansion_focus": "economic impacts"
    }
)

# Export complete analysis
final_doc = engine.assemble_document(
    results=[analysis, detailed],
    template="analysis_template.md",
    output_format="pdf"
)
```

This design provides a clean, reusable package that can be used across all your Python projects while maintaining the flexibility and power of the current system.