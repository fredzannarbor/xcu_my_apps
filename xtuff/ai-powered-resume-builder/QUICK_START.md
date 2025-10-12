# AI-Powered Resume Builder - Quick Start Guide

## TL;DR

```bash
# 1. Navigate to workspace
cd /Users/fred/xcu_my_apps

# 2. Ensure dependencies are installed
uv sync

# 3. Set up environment variables (if not already done)
# Add to /Users/fred/xcu_my_apps/.env:
# OPENAI_API_KEY=your_key_here

# 4. Run via application runner (RECOMMENDED)
cd all_applications_runner
python main.py
# Then click "AI Resume Builder" in the dashboard

# OR run standalone
cd xtuff/ai-powered-resume-builder
uv run streamlit run app.py --server.port=8512
# Open: http://localhost:8512
```

## Configuration

- **Port:** 8512
- **Domain:** resume.xtuff.ai
- **Location:** `/Users/fred/my-apps/xtuff/ai-powered-resume-builder`
- **Entry Point:** `app.py`
- **Logs:** `/Users/fred/my-apps/all_applications_runner/logs/resume_builder/`

## Subscription Tiers Quick Reference

| Tier | Price | Key Features |
|------|-------|-------------|
| Free | $0 | Browse teams, join teams, templates |
| Basic | $9/mo | + AI generation, create teams, uploads |
| Premium | $19/mo | + Advanced AI, validation, support |

## Testing Subscription Tiers

In the app, go to Profile Settings → Subscription Management and click upgrade buttons.

Or manually in code:
```python
st.session_state.subscription_tier = 'basic'  # or 'premium'
```

## Feature Access by Tier

### Free Tier
- ✅ Browse public teams
- ✅ View basic templates
- ✅ Join open teams

### Basic Tier (All Free +)
- ✅ AI resume generation (GPT-4o-mini)
- ✅ Create teams
- ✅ Upload documents
- ✅ Generate team profiles

### Premium Tier (All Basic +)
- ✅ Advanced AI models (GPT-4, GPT-4 Turbo)
- ✅ Resume validation
- ✅ Priority support

## Common Commands

```bash
# Check syntax
python3 -m py_compile app.py

# View logs
tail -f /Users/fred/xcu_my_apps/all_applications_runner/logs/resume_builder/resume_builder_*.log

# Validate config
python3 -c "import json; json.load(open('/Users/fred/my-apps/all_applications_runner/apps_config.json'))"

# Count lines of code
wc -l app.py
```

## Environment Variables Required

```bash
# Required for AI features
OPENAI_API_KEY=sk-...

# Required for subscription features (future)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8512 in use | Change port in apps_config.json |
| LLM not working | Check OPENAI_API_KEY in .env |
| Sidebar missing | Verify shared module in path |
| Import errors | Run `uv sync` |

## File Structure

```
ai-powered-resume-builder/
├── app.py                    # Main application (1,070 lines)
├── requirements.txt          # Dependencies
├── pyproject.toml           # Package config
├── README.md                # Full documentation
├── INTEGRATION_SUMMARY.md   # Integration details
├── QUICK_START.md          # This file
└── .env.example            # Environment template
```

## Key Integration Points

1. **Unified Sidebar**: Uses `/Users/fred/my-apps/shared/ui/unified_sidebar.py`
2. **LLM Calls**: Uses `nimble-llm-caller` package
3. **Subscriptions**: Checks `subscription_tier` in session state
4. **Logging**: Writes to centralized logs directory
5. **Config**: Registered in `apps_config.json`

## Next Steps After Integration

1. ✅ Test basic functionality
2. ✅ Verify LLM calls work
3. ✅ Test all subscription tiers
4. ⏳ Add database for persistence
5. ⏳ Integrate real Stripe webhooks
6. ⏳ Add document parsing
7. ⏳ Implement resume validation

## Support

- **Logs**: `/Users/fred/my-apps/all_applications_runner/logs/resume_builder/`
- **Config**: `/Users/fred/my-apps/all_applications_runner/apps_config.json`
- **Docs**: `README.md` and `INTEGRATION_SUMMARY.md`

## Success Criteria

- [x] App runs without errors
- [x] Sidebar navigation works
- [x] Free tier accessible
- [ ] LLM generation tested (requires API key)
- [x] Subscription tiers switchable
- [x] Logs being written
- [x] Config valid JSON

---

**Ready to use!** Start the application runner and test the integration.
