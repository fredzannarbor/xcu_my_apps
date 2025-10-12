# Centralized Environment Configuration

This module provides centralized environment variable management for the my-apps workspace.

## Overview

All applications in the my-apps workspace share a common set of environment variables (API keys, credentials, etc.) stored in `/Users/fred/my-apps/.env`. Individual applications can override specific variables by creating a local `.env` file in their application directory.

## Loading Pattern

The environment loader implements a two-tier loading strategy:

1. **Load workspace-level defaults** from `/Users/fred/my-apps/.env`
2. **Load app-specific overrides** from `<app-dir>/.env` (if it exists)

Values in the app-specific `.env` file override the corresponding values from the central `.env` file.

## Usage

### Basic Usage

In your application's main entry point (e.g., `main.py`, `app.py`, or `__init__.py`):

```python
from shared.env import load_env

# Load central .env + local overrides (recommended)
load_env()

# Now you can use os.getenv() as usual
import os
api_key = os.getenv("OPENAI_API_KEY")
```

### Advanced Usage

```python
from shared.env import load_env, get_env

# Load only central .env without overrides
load_env(allow_override=False)

# Load central + overrides from specific directory
load_env(app_dir="/path/to/app")

# Enable verbose logging
load_env(verbose=True)

# Get environment variable with default
api_key = get_env("OPENAI_API_KEY", default="")

# Get required environment variable (raises if missing)
api_key = get_env("OPENAI_API_KEY", required=True)
```

### Debug Information

```python
from shared.env import print_env_info

# Print environment configuration details
print_env_info()
```

## Creating App-Specific Overrides

If your application needs to override specific environment variables:

1. Create a `.env` file in your application's root directory
2. Add only the variables you want to override
3. Call `load_env()` in your application's entry point

### Example: Codexes Factory Override

`/Users/fred/my-apps/nimble/codexes-factory/.env`:
```bash
# Override only the OpenAI API base URL for this app
OPENAI_API_BASE=https://api.helicone.ai/v1

# Override logging level
LOG_LEVEL=DEBUG
```

All other variables will still be loaded from the central `/Users/fred/my-apps/.env` file.

## Best Practices

1. **Keep the central `.env` file for shared credentials**: API keys, database URLs, and other values used across multiple apps

2. **Use app-specific `.env` files sparingly**: Only override when necessary (e.g., different API endpoints, debug settings)

3. **Never commit `.env` files to git**: Both central and app-specific `.env` files should be in `.gitignore`

4. **Use `.env.example` files for documentation**: Create a `.env.example` file with dummy values to show what variables are needed

5. **Call `load_env()` early**: Load environment variables before importing other application modules that might depend on them

## Environment Variables Reference

See `/Users/fred/my-apps/.env.example` for a complete list of available environment variables and their descriptions.

## Common Variables

### LLM API Keys
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic (Claude) API key
- `XAI_API_KEY` - xAI (Grok) API key
- `GROQ_API_KEY` - Groq API key
- `GEMINI_API_KEY` - Google Gemini API key

### Payment Processing
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable key

### External Services
- `ZOTERO_API_KEY` - Zotero API key
- `GITHUB_PAT` - GitHub Personal Access Token
- `ZYTE_API_KEY` - Zyte web scraping API key

## Migration Guide

If you're migrating an existing app to use the centralized `.env`:

1. **Install the shared module** (if not already in workspace):
   ```bash
   # Ensure /Users/fred/xcu_my_apps is in your Python path
   ```

2. **Replace existing dotenv calls**:
   ```python
   # Before:
   from dotenv import load_dotenv
   load_dotenv()

   # After:
   from shared.env import load_env
   load_env()
   ```

3. **Move common variables to central `.env`**: Copy variables that are shared across apps to `/Users/fred/my-apps/.env`

4. **Keep app-specific overrides local**: Leave app-specific values in your local `.env` file

5. **Test**: Verify that all environment variables are loaded correctly

## Troubleshooting

### Variables not loading

1. Verify the central `.env` file exists:
   ```bash
   ls -la /Users/fred/xcu_my_apps/.env
   ```

2. Check your Python path includes `/Users/fred/my-apps`:
   ```python
   import sys
   print('/Users/fred/xcu_my_apps' in sys.path)
   ```

3. Enable verbose mode to see which files are being loaded:
   ```python
   load_env(verbose=True)
   ```

### Override not working

- Ensure `allow_override=True` (this is the default)
- Verify the local `.env` file exists in the expected directory
- Check variable names match exactly (case-sensitive)

### Import errors

- Ensure `/Users/fred/my-apps` is in `PYTHONPATH` or `sys.path`
- For uv projects, check `pyproject.toml` workspace configuration
