# ArXiv Writer

A standalone Python package for AI-assisted academic paper generation in arXiv format.

## Overview

ArXiv Writer is extracted from the Codexes Factory codebase to provide a clean, configurable API for generating academic papers using Large Language Models (LLMs). It supports multiple LLM providers, template-based content generation, and produces publication-ready LaTeX output.

## Features

- **Multi-LLM Support**: Works with OpenAI GPT, Anthropic Claude, Google Gemini, and more via LiteLLM
- **Template-Based Generation**: Configurable prompt templates for different paper sections
- **Plugin Architecture**: Extensible system for custom functionality
- **LaTeX Output**: Generates publication-ready LaTeX with PDF compilation
- **Validation**: Built-in content validation and quality assessment
- **Configuration Management**: Multi-level configuration system
- **Retry Logic**: Robust error handling with exponential backoff

## Installation

```bash
pip install arxiv-writer
```

For development:
```bash
git clone https://github.com/fredzannarbor/arxiv-writer
cd arxiv-writer
uv sync --dev
```

## Quick Start

```python
from arxiv_writer import ArxivPaperGenerator, PaperConfig

# Load configuration
config = PaperConfig.from_file("config.json")

# Initialize generator
generator = ArxivPaperGenerator(config)

# Generate paper
context_data = {
    "title": "My Research Paper",
    "authors": ["John Doe"],
    "abstract": "This paper presents...",
    # ... additional context
}

result = generator.generate_paper(context_data)
print(f"Paper generated: {result.output_path}")
```

## Configuration

Create a configuration file:

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "${OPENAI_API_KEY}"
  },
  "templates": {
    "prompts_file": "templates/default_prompts.json"
  },
  "output": {
    "format": "latex",
    "compile_pdf": true
  }
}
```

## CLI Usage

```bash
# Generate a paper
arxiv-writer generate --config config.json --context data.json

# Validate configuration
arxiv-writer validate --config config.json

# List available templates
arxiv-writer template list
```

## Documentation

- [User Guide](docs/user_guide.md)
- [API Reference](docs/api_reference.md)
- [Plugin Development](docs/plugin_development.md)
- [Configuration Reference](docs/configuration.md)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.
