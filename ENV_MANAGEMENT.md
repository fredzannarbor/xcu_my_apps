# Environment Variable Management

## Overview

The my-apps workspace uses a **centralized environment configuration** system with optional per-app overrides.

## Quick Start

### For Application Developers

Add this to your app's entry point (e.g., `main.py`, `app.py`, `__init__.py`):

```python
from shared.env import load_env

# Load central .env + local overrides
load_env()
```

That's it! All environment variables from `/Users/fred/my-apps/.env` are now available via `os.getenv()`.

### Creating App-Specific Overrides

If your app needs to override specific variables:

1. Create `.env` in your app's root directory
2. Add only the variables you want to override:
   ```bash
   # my-app/.env
   OPENAI_API_BASE=https://custom-endpoint.example.com
   LOG_LEVEL=DEBUG
   ```
3. The `load_env()` call will automatically load central values first, then your overrides

## File Structure

```
/Users/fred/my-apps/
├── .env                    # Central configuration (all shared API keys)
├── .env.example            # Template showing available variables
├── ENV_MANAGEMENT.md       # This file
├── shared/
│   └── env/
│       ├── __init__.py
│       ├── env_loader.py   # The load_env() utility
│       └── README.md       # Detailed documentation
│
├── all_applications_runner/
│   └── .env                # Optional: App-specific overrides
│
├── nimble/
│   └── codexes-factory/
│       └── .env            # Optional: App-specific overrides
│
└── xtuff/
    ├── agentic_social_server/
    │   └── .env            # Optional: App-specific overrides
    └── ...
```

## Loading Behavior

When you call `load_env()`:

1. **Loads** `/Users/fred/my-apps/.env` (central configuration)
2. **Then loads** `<app-dir>/.env` (if it exists)
3. **Variables in step 2 override** variables from step 1

## Migration Guide

### Migrating an Existing App

1. **Add the import** at the top of your main file:
   ```python
   from shared.env import load_env
   load_env()
   ```

2. **Remove old dotenv code**:
   ```python
   # Remove this:
   from dotenv import load_dotenv
   load_dotenv()
   ```

3. **Move shared variables** to `/Users/fred/my-apps/.env`
   - API keys used across multiple apps
   - Database credentials
   - Service endpoints

4. **Keep app-specific values** in local `.env`
   - App-specific API endpoints
   - Debug flags
   - Port numbers

## Best Practices

✅ **DO:**
- Store shared API keys in central `.env`
- Use local `.env` for app-specific overrides only
- Call `load_env()` early in your application
- Add `.env` to `.gitignore`
- Create `.env.example` files as templates

❌ **DON'T:**
- Commit `.env` files to version control
- Duplicate common variables across app `.env` files
- Override variables unnecessarily

## Available Variables

See `.env.example` for the complete list of available environment variables.

Common variables include:
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic/Claude API key
- `STRIPE_SECRET_KEY` - Stripe payment processing
- `ZOTERO_API_KEY` - Zotero reference management
- And many more...

## Detailed Documentation

For advanced usage, troubleshooting, and API reference, see:
- [`shared/env/README.md`](shared/env/README.md) - Complete documentation
- [`.env.example`](.env.example) - Template with all variables

## Backups

Historical `.env` files have been backed up to:
- `/Users/fred/my-apps/.env_backups/`

These backups are for reference only and are not loaded by the system.
