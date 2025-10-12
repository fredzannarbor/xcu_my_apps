# Installation Guide

## Overview

nimble-llm-caller is available in multiple installation configurations to suit different needs:

- **Basic**: Core LLM calling functionality
- **Enhanced**: Full context management and file processing capabilities
- **Development**: All features plus development tools

## Installation Options

### Basic Installation

For basic LLM calling functionality:

```bash
pip install nimble-llm-caller
```

### Enhanced Installation (Recommended)

For full context management, file processing, and advanced features:

```bash
pip install nimble-llm-caller[enhanced]
```

### All Features

To install all optional dependencies:

```bash
pip install nimble-llm-caller[all]
```

### Development Installation

For development and testing:

```bash
pip install nimble-llm-caller[dev,enhanced]
```

## Private PyPI Installation

If you're installing from a private PyPI repository:

### Option 1: Using pip with index URL

```bash
pip install --index-url https://your-private-pypi.com/simple/ nimble-llm-caller[enhanced]
```

### Option 2: Using pip with extra index URL

```bash
pip install --extra-index-url https://your-private-pypi.com/simple/ nimble-llm-caller[enhanced]
```

### Option 3: Using pip configuration

Create or edit `~/.pip/pip.conf` (Linux/Mac) or `%APPDATA%\pip\pip.ini` (Windows):

```ini
[global]
extra-index-url = https://your-private-pypi.com/simple/
```

Then install normally:

```bash
pip install nimble-llm-caller[enhanced]
```

## Pyx Installation

If using Pyx package manager:

```bash
pyx install nimble-llm-caller[enhanced]
```

## Verification

After installation, verify that the package is working:

```python
import nimble_llm_caller

# Check version
print(nimble_llm_caller.__version__)

# Test basic functionality
from nimble_llm_caller import LLMCaller
caller = LLMCaller()
print("Basic installation successful")

# Test enhanced functionality (if installed)
try:
    from nimble_llm_caller import EnhancedLLMCaller
    enhanced_caller = EnhancedLLMCaller()
    print("Enhanced features available")
except ImportError:
    print("Enhanced features not installed")
```

## Dependencies

### Core Dependencies

- `litellm>=1.0.0` - Multi-provider LLM interface
- `python-dotenv>=1.0.0` - Environment variable management
- `json-repair>=0.25.0` - JSON parsing and repair
- `jinja2>=3.1.0` - Template processing
- `pydantic>=2.0.0` - Data validation
- `typing-extensions>=4.0.0` - Type hints
- `tiktoken>=0.5.0` - Token counting

### Enhanced Dependencies (Optional)

File Processing:
- `PyPDF2>=3.0.0` - PDF text extraction
- `pdfplumber>=0.9.0` - Advanced PDF processing
- `python-docx>=0.8.11` - Word document processing
- `striprtf>=0.0.26` - RTF document processing
- `Pillow>=9.0.0` - Image processing
- `openpyxl>=3.0.0` - Excel file processing

Advanced Tokenization:
- `anthropic>=0.25.0` - Anthropic tokenizer
- `google-generativeai>=0.3.0` - Google tokenizer

Configuration:
- `PyYAML>=6.0.0` - YAML configuration support

## System Requirements

- Python 3.9 or higher
- Operating System: Windows, macOS, or Linux
- Memory: Minimum 512MB RAM (2GB+ recommended for file processing)
- Disk Space: 100MB for basic installation, 500MB for enhanced features

## Troubleshooting

### Common Installation Issues

#### 1. Permission Errors

If you encounter permission errors:

```bash
pip install --user nimble-llm-caller[enhanced]
```

#### 2. SSL Certificate Issues

If you have SSL certificate issues with private PyPI:

```bash
pip install --trusted-host your-private-pypi.com nimble-llm-caller[enhanced]
```

#### 3. Dependency Conflicts

If you have dependency conflicts, try using a virtual environment:

```bash
python -m venv nimble-env
source nimble-env/bin/activate  # On Windows: nimble-env\Scripts\activate
pip install nimble-llm-caller[enhanced]
```

#### 4. Missing System Dependencies

Some optional dependencies may require system libraries:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3-dev libffi-dev libssl-dev
```

**CentOS/RHEL:**
```bash
sudo yum install python3-devel libffi-devel openssl-devel
```

**macOS:**
```bash
brew install libffi openssl
```

### Feature-Specific Issues

#### PDF Processing Issues

If PDF processing fails:

1. Install additional PDF libraries:
   ```bash
   pip install PyPDF2 pdfplumber
   ```

2. For encrypted PDFs, you may need additional tools

#### Image Processing Issues

If image processing fails:

1. Install Pillow with additional image format support:
   ```bash
   pip install Pillow[all]
   ```

2. On some systems, you may need system image libraries:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libjpeg-dev libpng-dev libtiff-dev
   
   # macOS
   brew install jpeg libpng libtiff
   ```

## Environment Setup

### API Keys

Set up your API keys as environment variables:

```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"
```

Or create a `.env` file in your project directory:

```env
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
```

### Configuration

Create a configuration file (optional):

```json
{
  "models": {
    "gpt-4o": {
      "provider": "openai",
      "api_key_env": "OPENAI_API_KEY"
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
  }
}
```

## Next Steps

After installation:

1. Read the [Quick Start Guide](QUICKSTART.md)
2. Check out the [Examples](examples/)
3. Review the [Configuration Guide](CONFIGURATION.md)
4. See the [Migration Guide](MIGRATION.md) if upgrading from an older version

## Support

If you encounter issues:

1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review the [FAQ](FAQ.md)
3. Search existing [GitHub Issues](https://github.com/nimblebooks/nimble-llm-caller/issues)
4. Create a new issue with detailed information about your problem