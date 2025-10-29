# Testing Guide for Feature Branches

This guide explains how to ensure your feature branches don't break clean-production.

## Quick Start

Before merging any feature branch to clean-production:

```bash
cd /Users/fred/xcu_my_apps/nimble/codexes-factory
./test_before_merge.sh
```

If all tests pass ✅, safe to merge!

## What "Deploy to Production" Means

**Your Setup:**
- **Local:** Your Mac (development)
- **GitHub:** Code repository (github.com/fredzannarbor/xcu_my_apps)
- **GCP Production Server:** 34.172.181.254 (live server)

**Deployment Process:**
1. You push to `clean-production` branch on GitHub
2. GitHub Actions automatically runs (`.github/workflows/deploy.yml`)
3. GitHub SSHs into your GCP server
4. Runs `git pull origin clean-production` on the server
5. Server now has your latest code running

**Result:** Users accessing your apps on GCP get the new code immediately.

## Recommended Workflow

### 1. Create Feature Branch
```bash
git checkout clean-production
git checkout -b feature/my-new-feature
```

### 2. Develop & Test Locally
```bash
# Make changes
# Test on your Mac
```

### 3. Run Regression Tests
```bash
./test_before_merge.sh
```

### 4. If Tests Pass, Merge to clean-production
```bash
git checkout clean-production
git merge feature/my-new-feature
```

### 5. Test on clean-production
```bash
# Run your app locally on clean-production branch
# Verify everything works
```

### 6. Deploy to Production
```bash
git push origin clean-production
# GitHub Actions automatically deploys to GCP server
```

### 7. Update Source of Truth
```bash
git checkout main
git merge clean-production
git push origin main
```

### 8. Clean Up
```bash
git branch -d feature/my-new-feature
```

## Test Suite Components

### test_before_merge.sh
Runs 4 critical tests:

1. **Python Syntax** - Catches syntax errors
2. **Import Validation** - Ensures modules load
3. **Configuration Integrity** - Verifies Nimble Ultra settings
4. **Pipeline Smoke Test** - Checks pipeline loads

### Current Nimble Ultra Regression Tests

**Publishers Note:**
- ✅ Uses "publishers_note" (not "motivation")
- ✅ Field mapping present in llm_get_book_data.py
- ✅ Prepress has _format_publishers_note_signature()

**Structured Abstracts:**
- ✅ Prompt returns structured JSON
- ✅ Prepress has _render_structured_abstracts()
- ✅ Field mapping handles 'abstracts' key

**Structured Mnemonics:**
- ✅ Prompt returns structured JSON array
- ✅ Prepress has _render_structured_mnemonics()
- ✅ Proper spacing and alignment

**Page Layout:**
- ✅ Copyright on page ii
- ✅ TOC on page iii (unnumbered)
- ✅ No "Back Matter" in footer

## Adding New Tests

To add tests for your features, edit `test_before_merge.sh` and add a new TEST section:

```bash
# Test 5: My New Feature
echo "TEST 5: My New Feature Validation"
# ... your test code ...
```

## CI/CD Integration (Optional)

You can also add the test to GitHub Actions to run on every push:

```yaml
# .github/workflows/test.yml
name: Test Feature Branch
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          cd nimble/codexes-factory
          ./test_before_merge.sh
```

## Quick Reference

**Test before merge:**
```bash
./test_before_merge.sh
```

**Deploy to production:**
```bash
git push origin clean-production
```

**Check deployment status:**
- Go to: https://github.com/fredzannarbor/xcu_my_apps/actions
- Look for "Deploy to Production" workflow

## Troubleshooting

**Tests fail locally?**
- Fix the issues before merging
- Run tests again until they pass

**Deployment failed?**
- Check GitHub Actions logs
- SSH to server: `ssh wfzimmerman@34.172.181.254`
- Check logs on server

**Rollback if needed:**
```bash
git checkout clean-production
git reset --hard HEAD~1  # Go back one commit
git push origin clean-production --force  # Redeploy previous version
```

---

*Created: October 28, 2025*
*For: xcu_my_apps repository*
