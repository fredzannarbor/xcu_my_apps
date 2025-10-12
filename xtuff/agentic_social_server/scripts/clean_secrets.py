#!/usr/bin/env python3
"""
Security Cleanup Script for AI Social Server

Removes secrets, PII, and sensitive data from the codebase before committing.
This ensures the repository is safe for public release.
"""

import os
import re
import shutil
import glob
from pathlib import Path
from typing import List, Set


class SecurityCleaner:
    """Cleans secrets and PII from the codebase."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.issues_found = []

        # Patterns that indicate secrets or PII
        self.secret_patterns = [
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI keys
            r'AIza[a-zA-Z0-9]{35}',  # Google API keys
            r'gsk_[a-zA-Z0-9]{20,}',  # Groq keys
            r'whsec_[a-zA-Z0-9]{20,}',  # Webhook secrets
            r'pk_test_[a-zA-Z0-9]{20,}',  # Stripe test keys
            r'sk_test_[a-zA-Z0-9]{20,}',  # Stripe secret keys
            r'xai-[a-zA-Z0-9]{20,}',  # xAI keys
            r'claude-[a-zA-Z0-9]{20,}',  # Anthropic keys
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email addresses
        ]

        # Files/directories to exclude from checks
        self.exclude_paths = {
            '.venv', '.git', '__pycache__', '.pytest_cache',
            'node_modules', '.claude', '.env'
        }

        # Test/debug files that should be removed
        self.test_file_patterns = [
            'debug_*.py',
            'test_*_key*.py',
            'test_*_secret*.py',
            '*_debug.py',
            'temp_*.py',
            'scratch_*.py'
        ]

    def scan_for_secrets(self, file_path: Path) -> List[str]:
        """Scan a file for potential secrets."""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            for i, line in enumerate(content.split('\n'), 1):
                for pattern in self.secret_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        # Skip obvious examples/placeholders
                        matched_text = match.group().lower()
                        if any(placeholder in matched_text for placeholder in [
                            'example', 'placeholder', 'your_', 'test@', 'user@'
                        ]):
                            continue

                        issues.append(f"{file_path}:{i} - Potential secret: {match.group()[:20]}...")

        except Exception as e:
            issues.append(f"{file_path} - Error reading file: {e}")

        return issues

    def update_gitignore(self) -> bool:
        """Ensure .gitignore has all necessary exclusions."""
        gitignore_path = self.project_root / '.gitignore'

        required_entries = [
            '# Environment and Secrets',
            '.env',
            '.env.local',
            '.env.production',
            '*.env',
            '',
            '# Claude Code Configuration (contains sensitive data)',
            '.claude/',
            '',
            '# Temporary and debug files',
            'debug_*.py',
            'test_*_key*.py',
            'test_*_secret*.py',
            '*_debug.py',
            'temp_*.py',
            'scratch_*.py',
            '',
            '# Log files that might contain sensitive data',
            '*.jsonl',
            'ai_interactions.jsonl',
            'llm_interactions.jsonl',
            'logs/',
            '*.log',
        ]

        try:
            if gitignore_path.exists():
                with open(gitignore_path, 'r') as f:
                    current_content = f.read()
            else:
                current_content = ""

            # Add missing entries
            for entry in required_entries:
                if entry and entry not in current_content:
                    current_content += f"\n{entry}"

            with open(gitignore_path, 'w') as f:
                f.write(current_content)

            print("✅ Updated .gitignore with security exclusions")
            return True

        except Exception as e:
            print(f"❌ Error updating .gitignore: {e}")
            return False

    def create_env_example(self) -> bool:
        """Create .env.example file if it doesn't exist."""
        env_example_path = self.project_root / '.env.example'
        env_path = self.project_root / '.env'

        if env_example_path.exists():
            print("✅ .env.example already exists")
            return True

        template = """# AI Social Server Environment Configuration
# Copy this file to .env and fill in your actual values

# ======================
# LLM API KEYS
# ======================

# Google Gemini API Key (for native Gemini integration)
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_API_KEY=your_google_api_key_here

# OpenAI API Key (for GPT models via litellm)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key (for Claude models via litellm)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Groq API Key (for fast inference)
GROQ_API_KEY=your_groq_api_key_here

# Other LLM providers (optional)
REPLICATE_API_TOKEN=your_replicate_token_here
XAI_API_KEY=your_xai_api_key_here

# ======================
# APPLICATION SETTINGS
# ======================

# Local host URL for development
LOCAL_HOST=http://localhost:8501

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# ======================
# NOTES
# ======================
#
# Required for basic functionality:
# - GOOGLE_API_KEY or GEMINI_API_KEY (for Gemini 2.5 Pro integration)
# - At least one other LLM API key (OpenAI, Anthropic, etc.)
"""

        try:
            with open(env_example_path, 'w') as f:
                f.write(template)
            print("✅ Created .env.example file")
            return True
        except Exception as e:
            print(f"❌ Error creating .env.example: {e}")
            return False

    def remove_test_files(self) -> int:
        """Remove test and debug files that might contain secrets."""
        removed_count = 0

        for pattern in self.test_file_patterns:
            for file_path in glob.glob(str(self.project_root / pattern)):
                try:
                    Path(file_path).unlink()
                    print(f"🗑️  Removed test file: {file_path}")
                    removed_count += 1
                except Exception as e:
                    print(f"❌ Error removing {file_path}: {e}")

        # Remove specific log files
        log_files = ['*.jsonl', 'ai_interactions.jsonl', 'llm_interactions.jsonl']
        for pattern in log_files:
            for file_path in glob.glob(str(self.project_root / pattern)):
                try:
                    Path(file_path).unlink()
                    print(f"🗑️  Removed log file: {file_path}")
                    removed_count += 1
                except Exception as e:
                    print(f"❌ Error removing {file_path}: {e}")

        return removed_count

    def scan_codebase(self) -> bool:
        """Scan the entire codebase for secrets."""
        print("🔍 Scanning codebase for secrets and PII...")

        file_extensions = ['.py', '.json', '.md', '.txt', '.yaml', '.yml', '.js', '.ts']

        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_paths]

            for file in files:
                file_path = Path(root) / file

                # Check file extensions
                if file_path.suffix in file_extensions:
                    issues = self.scan_for_secrets(file_path)
                    self.issues_found.extend(issues)

        return len(self.issues_found) == 0

    def create_security_doc(self) -> bool:
        """Create SECURITY.md documentation."""
        security_path = self.project_root / 'SECURITY.md'

        content = """# Security Configuration

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
"""

        try:
            with open(security_path, 'w') as f:
                f.write(content)
            print("✅ Created/updated SECURITY.md")
            return True
        except Exception as e:
            print(f"❌ Error creating SECURITY.md: {e}")
            return False

    def run(self) -> bool:
        """Run the complete security cleanup process."""
        print("🛡️  Starting security cleanup...")
        print(f"📁 Project root: {self.project_root}")

        success = True

        # 1. Update .gitignore
        success &= self.update_gitignore()

        # 2. Create .env.example
        success &= self.create_env_example()

        # 3. Remove test files
        removed_count = self.remove_test_files()
        if removed_count > 0:
            print(f"✅ Removed {removed_count} test/debug files")

        # 4. Scan for secrets
        clean = self.scan_codebase()
        if clean:
            print("✅ No secrets found in source code")
        else:
            print("❌ Found potential secrets:")
            for issue in self.issues_found:
                print(f"  {issue}")
            success = False

        # 5. Create security documentation
        success &= self.create_security_doc()

        if success:
            print("\n🎉 Security cleanup completed successfully!")
            print("✅ Repository is safe for public release")
        else:
            print("\n⚠️  Security cleanup completed with warnings")
            print("❌ Please review the issues above before committing")

        return success


def main():
    """Main entry point for the security cleanup script."""
    import sys

    # Get project root from command line argument or use current directory
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."

    cleaner = SecurityCleaner(project_root)
    success = cleaner.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()