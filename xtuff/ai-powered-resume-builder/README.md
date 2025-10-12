# AI-Powered Resume Builder

An AI-powered resume and team profile builder integrated with the my-apps framework.

## Features

### Free Tier
- Browse public teams
- View basic resume templates
- Join open teams

### Basic Tier ($9/month)
- AI-powered resume generation
- Create and manage teams
- Upload documents (resumes, work samples)
- Generate team profiles
- Team collaboration features

### Premium Tier ($19/month)
- All Basic tier features
- Advanced AI models (GPT-4, GPT-4 Turbo)
- Resume validation and verification
- Priority support
- API access (planned)

## Key Capabilities

### Individual Resumes
- AI-generated professional resumes
- Customized for specific opportunities
- Multiple AI model options (Premium)
- Markdown format with easy export

### Team Profiles
- Collaborative team resume building
- Combined skills and experience showcase
- Team management and organization
- Multiple team types supported

### Team Management
- Create public or private teams
- Invite-only, request-based, or open joining
- Team captain controls
- Skills-based matching
- Team discovery and browsing

## Technology Stack

- **Framework**: Streamlit
- **LLM Integration**: nimble-llm-caller (wrapper for litellm)
- **Subscription**: Stripe integration
- **Logging**: Centralized to `logs/resume_builder/`
- **UI**: Unified my-apps sidebar

## Installation

1. Ensure you're in the my-apps workspace:
```bash
cd /Users/fred/xcu_my_apps
```

2. Install dependencies:
```bash
uv sync
```

3. Set up environment variables in `.env`:
```bash
OPENAI_API_KEY=your_openai_key_here
STRIPE_SECRET_KEY=your_stripe_key_here
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key_here
```

## Running the Application

### Via All Applications Runner
The preferred method is to use the unified application runner:
```bash
cd /Users/fred/xcu_my_apps/all_applications_runner
python main.py
```
Then navigate to the AI Resume Builder from the dashboard.

### Standalone
```bash
cd /Users/fred/xcu_my_apps/xtuff/ai-powered-resume-builder
uv run streamlit run app.py --server.port=8512
```

## Configuration

The app is registered in `/Users/fred/my-apps/all_applications_runner/apps_config.json`:

```json
{
  "ai_resume_builder": {
    "name": "AI Resume Builder",
    "port": 8512,
    "path": "/Users/fred/xcu_my_apps/xtuff/ai-powered-resume-builder",
    "entry": "app.py",
    "description": "AI-powered resume builder with team collaboration",
    "subscription_tier": "free",
    "domain_name": "resume.xtuff.ai"
  }
}
```

## Subscription Tiers

### Feature Matrix

| Feature | Free | Basic | Premium |
|---------|------|-------|---------|
| Basic resume templates | ✅ | ✅ | ✅ |
| Browse teams | ✅ | ✅ | ✅ |
| Join open teams | ✅ | ✅ | ✅ |
| AI resume generation | ❌ | ✅ | ✅ |
| Create teams | ❌ | ✅ | ✅ |
| Document upload | ❌ | ✅ | ✅ |
| Team profiles | ❌ | ✅ | ✅ |
| Advanced AI models | ❌ | ❌ | ✅ |
| Resume validation | ❌ | ❌ | ✅ |
| Priority support | ❌ | ❌ | ✅ |

## Team Types

Supported team categories:
- Startup Team
- Consulting Group
- Research Collaboration
- Industry Expertise
- Alumni Network
- Project-Based Team
- Skill-Based Collective
- Geographic Network
- Domain Experts
- Open Source Contributors
- Other

## Logging

All logs are centralized to:
```
/Users/fred/my-apps/all_applications_runner/logs/resume_builder/
```

Log files are named: `resume_builder_YYYYMMDD.log`

## Integration with my-apps Framework

### Unified Sidebar
Uses the shared sidebar component from `/Users/fred/my-apps/shared/ui/unified_sidebar.py`

### Subscription Management
Integrates with `/Users/fred/my-apps/all_applications_runner/subscription_manager.py`

### LLM Calls
Uses nimble-llm-caller for consistent LLM integration across all apps

### Logging
Follows centralized logging pattern to `logs/{app_name}/`

## Development

### Adding New Features

1. Update subscription tier access in `check_subscription_access()` function
2. Add feature UI in main content area
3. Test with different subscription tiers
4. Update this README with feature documentation

### Testing Different Tiers

To test subscription tiers, modify session state:
```python
st.session_state.subscription_tier = 'basic'  # or 'premium'
```

## Future Enhancements

- API access for programmatic resume generation
- Integration with LinkedIn for profile import
- ATS (Applicant Tracking System) optimization
- Resume version history
- Team analytics dashboard
- Export to multiple formats (PDF, DOCX)
- Resume templates library
- Skills verification system

## Support

For issues or questions:
- Check logs in `/Users/fred/my-apps/all_applications_runner/logs/resume_builder/`
- Contact via the app's contact widget
- Email: [contact method from footer]

## License

Part of the xtuff.ai platform.
