# System State Requirements and Compliance

This document defines the architecture requirements for all apps in the xcu_my_apps ecosystem and provides guidance on maintaining compliance.

## Overview

All apps must comply with a unified architecture to ensure:
- **Shared Authentication**: Single sign-on across all apps
- **Consistent UI**: Unified sidebar with platform navigation
- **Production Readiness**: Proper GCP deployment configuration
- **Dependency Management**: UV workspace for shared dependencies
- **Environment Configuration**: Shared or documented .env settings

## Critical Requirements

### 1. Shared Authentication (CRITICAL)

**Requirement**: All apps must use the shared authentication system for SSO.

**Implementation**:
```python
# In your main app file
from shared.auth import get_shared_auth, is_authenticated, get_user_info

# Check authentication
if is_authenticated():
    user_info = get_user_info()
    st.write(f"Welcome {user_info.get('user_name')}")
```

**Why Critical**: Without shared auth, users must log in separately to each app, breaking the unified platform experience.

**Fix**:
- Add `from shared.auth import get_shared_auth, is_authenticated` to your app entry file
- Replace any custom auth with shared auth system
- Ensure session state is preserved across navigation

**Current Compliance**: 22.2% (2/9 apps)

---

### 2. Port Binding to 0.0.0.0 (CRITICAL)

**Requirement**: All Streamlit apps must bind to 0.0.0.0 for GCP load balancer accessibility.

**Implementation**:
```json
// In apps_config.json
{
  "startup_command": "uv run streamlit run app.py --server.port=8501 --server.address=0.0.0.0"
}
```

**Why Critical**: Apps binding to localhost (127.0.0.1) are not accessible from GCP load balancer, causing production failures.

**Fix**:
- Add `--server.address=0.0.0.0` to all `startup_command` entries in apps_config.json
- For production deployment, this is mandatory

**Current Compliance**: 0% (0/9 apps) - **URGENT FIX NEEDED**

---

## Important Requirements

### 3. Unified Sidebar (WARNING)

**Requirement**: All apps should use the unified sidebar component for consistent UX.

**Implementation**:
```python
from shared.ui import render_unified_sidebar

# At the start of your app
render_unified_sidebar(
    app_name="My Application",
    nav_items=[
        ("Home", "pages/home.py"),
        ("Settings", "pages/settings.py"),
    ]
)
```

**Why Important**: Provides consistent navigation, branding, and user experience across all apps.

**Fix**:
- Install shared UI component: Add to PYTHONPATH or use `sys.path.insert(0, '/Users/fred/xcu_my_apps')`
- Replace custom sidebar code with `render_unified_sidebar()`
- See `/Users/fred/xcu_my_apps/shared/README.md` for details

**Current Compliance**: 55.6% (5/9 apps)

---

### 4. GCP Domain Mapping (INFO)

**Requirement**: Each app must have correct domain_name configured for production routing.

**Expected Mappings**:
```
Port 8500 → xtuff.ai (main/landing)
Port 8501 → social.xtuff.ai
Port 8502 → codexes.nimblebooks.com
Port 8504 → trillionsofpeople.info
Port 8509 → dailyengine.xtuff.ai
Port 8512 → resume.xtuff.ai
```

**Implementation**:
```json
// In apps_config.json
{
  "port": 8501,
  "domain_name": "social.xtuff.ai"
}
```

**Current Compliance**: 100% (9/9 apps) ✓

---

### 5. UV Workspace (WARNING)

**Requirement**: Apps should be in the UV workspace to inherit shared dependencies.

**Implementation**:
```toml
# In /Users/fred/xcu_my_apps/pyproject.toml
[tool.uv.workspace]
members = [
    "xtuff/*",
    "nimble/*",
    "shared",
    "all_applications_runner"
]
```

**Why Important**: Ensures consistent dependency versions, faster installs, and easier maintenance.

**Fix**:
- Add app directory to workspace.members in root pyproject.toml
- Run `uv sync` to synchronize dependencies
- Apps can have their own pyproject.toml for app-specific deps

**Current Compliance**: 66.7% (6/9 apps)

---

### 6. Environment Variables (INFO)

**Requirement**: Apps should use shared .env or document overrides.

**Implementation**:
```python
# Apps automatically inherit from /Users/fred/xcu_my_apps/.env
# For app-specific overrides, create .env in app directory
```

**Location**:
- Master: `/Users/fred/xcu_my_apps/.env`
- App override: `<app-path>/.env`

**Current Compliance**: 100% (9/9 apps) ✓

---

### 7. Health Endpoint (INFO)

**Requirement**: Apps must have health_endpoint configured for GCP health checks.

**Implementation**:
```json
// In apps_config.json
{
  "health_endpoint": "/"  // or "/health"
}
```

**Current Compliance**: 100% (9/9 apps) ✓

---

## Enforcement

The `ProcessManager` enforces critical requirements:

```python
# In process_manager.py
manager = ProcessManager(enforce_compliance=True)

# Apps with CRITICAL violations will not start
# Apps with WARNING violations will start but log warnings
```

**Bypass** (for testing only):
```python
manager.start_process("org.app", skip_compliance_check=True)
```

---

## Verification

### Command Line:
```bash
cd /Users/fred/xcu_my_apps/all_applications_runner
python3 system_state_verifier.py
```

### Dashboard:
1. Login as admin at http://localhost:8500
2. Navigate to "🔍 System State"
3. Click "🔄 Run Full Verification"
4. Review compliance scores and violations
5. Use "Enable Auto-Fix" to automatically fix config issues

---

## Quick Fixes

### Fix All Port Binding Issues (Urgent):
```bash
cd /Users/fred/xcu_my_apps/all_applications_runner

# Run the dashboard and enable auto-fix
# OR manually edit apps_config.json to add --server.address=0.0.0.0
```

### Fix Shared Auth Integration:
For each app missing shared auth:
1. Open the app's main/entry file
2. Add import: `from shared.auth import get_shared_auth, is_authenticated`
3. Replace any custom auth with shared auth calls
4. Test authentication flow

### Fix Unified Sidebar:
For each app missing unified sidebar:
1. Add to top of app: `from shared.ui import render_unified_sidebar`
2. Replace custom sidebar with: `render_unified_sidebar(app_name="App Name", nav_items=[...])`
3. Move any functional forms from sidebar to main page

---

## Current System Status

**Last Verified**: See verification timestamp

**Overall Compliance**: 63.5%

**Critical Issues**: 9 apps need port binding fixes

**Priority Fixes**:
1. ✗ Add --server.address=0.0.0.0 to ALL apps (0% compliance)
2. ✗ Add shared auth to 7 apps (22.2% → 100%)
3. ⚠ Add unified sidebar to 4 apps (55.6% → 100%)

---

## Automated Fixes

The system can auto-fix some issues:

1. **Port Binding**: Automatically adds `--server.address=0.0.0.0` to startup_command
2. **Health Endpoint**: Automatically adds default `/` endpoint
3. **Domain Names**: Can validate and suggest corrections

Manual fixes needed:
- Shared auth integration (requires code changes)
- Unified sidebar adoption (requires code changes)
- UV workspace membership (requires pyproject.toml updates)

---

## Monitoring

The system continuously monitors:
- App health status
- Compliance violations
- Authentication state
- Port availability

Alerts triggered for:
- Apps starting with critical violations
- Health check failures
- Authentication issues

---

## Support

For questions or issues:
- Review `/Users/fred/xcu_my_apps/shared/README.md`
- Check System State Dashboard for detailed diagnostics
- Run verifier CLI for detailed reports

**Documentation Updated**: October 2025
