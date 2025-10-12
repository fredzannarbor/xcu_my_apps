# Security Configuration

## Environment Variables

This project requires several API keys to function properly. **Never commit these to version control.**

### Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your actual API keys in the `.env` file

### Required API Keys

- `GOOGLE_API_KEY` or `GEMINI_API_KEY` - For Gemini 2.5 Pro integration
- At least one additional LLM provider key (OpenAI, Anthropic, etc.)

### Security Notes

- The `.env` file is already in `.gitignore` and will not be committed
- The `.claude/` directory contains sensitive configuration and is excluded from git
- All test files with secrets have been removed from the repository
- Use environment variables for all API keys and sensitive configuration

### Best Practices

1. Use different API keys for development and production
2. Regularly rotate your API keys
3. Monitor API usage for unexpected activity
4. Never log or display API keys in application output
5. Run `python scripts/clean_secrets.py` before committing

### Automated Security

Use the security cleanup script before committing:

```bash
python scripts/clean_secrets.py
```

This script will:
- Scan for potential secrets in source code
- Remove test/debug files that might contain sensitive data
- Update .gitignore with security exclusions
- Create .env.example if missing
