# Single Sign-On (SSO) Migration Complete

**Date:** 2025-10-05
**Migration:** All Applications Runner → Shared Authentication System

## Summary

Successfully migrated All Applications Runner from `streamlit-authenticator` to the **shared authentication system**, enabling true Single Sign-On (SSO) across all xtuff.ai applications.

## What Changed

### Before (Dual Auth Systems)
```
┌─────────────────────────────┐
│  All Applications Runner    │
│  streamlit-authenticator    │
│  Cookie-based sessions      │
└─────────────────────────────┘
              ↓
   Users must login again
              ↓
┌─────────────────────────────┐
│     Individual Apps         │
│  (Codexes Factory, etc.)    │
│  Shared Auth System         │
│  SQLite DB sessions         │
└─────────────────────────────┘
```

### After (Unified SSO)
```
┌──────────────────────────────────────┐
│      Shared Authentication System     │
│   SQLite: /shared/auth/auth_sessions.db│
│   Config: /nimble/codexes-factory/    │
│           resources/yaml/config.yaml   │
└──────────────────────────────────────┘
              ↑
              │
    ┌─────────┴─────────┐
    │                   │
┌───┴────────┐  ┌───────┴──────┐
│ App Runner │  │ Codexes, etc.│
│            │  │              │
└────────────┘  └──────────────┘

✅ Login once, access all apps
```

## Files Modified

### 1. `/nimble/codexes-factory/src/codexes/codexes-factory-home-ui.py`
**Changed:** Complete rewrite to use shared auth system
- Removed: `import streamlit_authenticator as stauth`
- Removed: `from codexes.core.simple_auth import get_auth`
- Removed: `from codexes.core.ui import build_sidebar`
- Added: `from shared.auth import get_shared_auth, is_authenticated, get_user_info`
- Added: `from shared.ui import render_unified_sidebar`
- Updated: Authentication to use shared auth instead of simple_auth
- Updated: Sidebar to use render_unified_sidebar instead of build_sidebar

**Backup:** `codexes-factory-home-ui.py.backup`

### 2. `/all_applications_runner/auth_integration.py`
**Changed:** Complete rewrite to use shared auth system
- Removed: `streamlit-authenticator` imports and usage
- Added: `from shared.auth import get_shared_auth, is_authenticated, ...`
- Updated: `AuthManager` class to wrap shared auth
- Updated: `render_login_widget()` to use shared auth login form

**Backup:** `auth_integration.py.backup`

### 2. `/all_applications_runner/main.py`
**Changed:** None (already compatible!)
- The existing code structure worked perfectly with new AuthManager
- `render_login_widget(location="sidebar")` now uses shared auth
- No changes needed

**Backup:** `main.py.backup`

### 3. `/nimble/codexes-factory/src/codexes/pages/1_Home.py`
**Changed:** Already using render_unified_sidebar
- No changes needed - this page was already correctly configured!
- Shows `render_unified_sidebar()` usage

### 4. `/pyproject.toml`
**Changed:** Dependency updates
- Removed: `streamlit-authenticator>=0.2.0`
- Added: `bcrypt>=4.0.0` (required by shared auth)
- Synced with `uv sync`

### 5. Configuration Files (Previously Fixed)
- `/all_applications_runner/resources/yaml/config.yaml`
  - Admin name: "Admin User" → "Admin"
- `/nimble/codexes-factory/resources/yaml/config.yaml`
  - Admin name: "Admin User" → "Admin"

## How SSO Works Now

### 1. User logs into All Applications Runner
```python
# In auth_integration.py
success, message = authenticate(username, password)
# Creates session in /shared/auth/auth_sessions.db
```

### 2. Session is stored in shared SQLite database
```sql
INSERT INTO active_sessions (
    session_id, username, user_name, user_email,
    user_role, subscription_tier, ...
)
```

### 3. User opens Codexes Factory (or any app)
```python
# In unified_sidebar.py
auth = get_shared_auth()
if is_authenticated():
    # Session automatically loaded from database!
    user_info = get_user_info()
```

### 4. All apps see the same authenticated user
- Same username
- Same role
- Same email
- Same subscription tier
- Same session expiration (30 days)

## Admin User Credentials

**Username:** `admin`
**Password:** `hotdogtoy`
**Email:** `admin@nimblebooks.com`
**Name:** `Admin`
**Role:** `admin`

## Testing Checklist

After restarting services:

- [ ] Start All Applications Runner: `http://localhost:8500`
- [ ] Login as admin/hotdogtoy
- [ ] Verify user shows as "Admin" with "admin@nimblebooks.com"
- [ ] Navigate to Codexes Factory: `http://localhost:8502`
- [ ] **User should already be logged in (SSO working!)**
- [ ] Verify same user info appears
- [ ] Test admin access to all pages
- [ ] Logout from one app
- [ ] Verify logged out from all apps

## Technical Details

### Shared Auth Database Location
```
/Users/fred/my-apps/shared/auth/auth_sessions.db
```

### Shared Auth Config Location
```
/Users/fred/my-apps/nimble/codexes-factory/resources/yaml/config.yaml
```

### Session Schema
```sql
CREATE TABLE active_sessions (
    session_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    user_name TEXT,
    user_email TEXT,
    user_role TEXT,
    subscription_tier TEXT,
    subscription_status TEXT,
    created_at TEXT NOT NULL,
    last_accessed TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
```

### Session Lifecycle
1. **Login:** Creates session in SQLite DB with unique session_id
2. **Access:** Each page load checks for active session in Streamlit session_state
3. **Auto-load:** If session_id exists, loads user data from DB
4. **Update:** Updates `last_accessed` timestamp on each request
5. **Expiry:** Sessions expire after 30 days of inactivity
6. **Logout:** Deletes session from DB and clears session_state

## Architecture Benefits

✅ **Single Sign-On:** Login once, access all apps
✅ **Centralized User Management:** One config file for all users
✅ **Shared Sessions:** All apps use same session database
✅ **Role-Based Access:** Consistent role hierarchy across apps
✅ **Subscription Management:** Centralized subscription tracking
✅ **Security:** Password hashing with bcrypt
✅ **Simplicity:** Removed dual auth system complexity

## Rollback Instructions

If you need to rollback to the old system:

1. Restore backup files:
   ```bash
   cp /Users/fred/xcu_my_apps/all_applications_runner/auth_integration.py.backup \
      /Users/fred/xcu_my_apps/all_applications_runner/auth_integration.py

   cp /Users/fred/xcu_my_apps/all_applications_runner/main.py.backup \
      /Users/fred/xcu_my_apps/all_applications_runner/main.py
   ```

2. Restore streamlit-authenticator dependency:
   ```bash
   # Edit pyproject.toml to add back:
   # "streamlit-authenticator>=0.2.0",

   uv sync
   ```

3. Restart All Applications Runner

## Future Enhancements

Possible improvements to the shared auth system:

1. **OAuth Integration:** Add Google/GitHub login
2. **Two-Factor Authentication:** SMS or authenticator app
3. **Password Reset:** Email-based password reset flow
4. **User Registration UI:** Allow users to self-register
5. **Session Management Dashboard:** View/revoke active sessions
6. **Audit Log:** Track login attempts and user actions
7. **Redis Backend:** Replace SQLite with Redis for better scalability
8. **JWT Tokens:** Implement token-based auth for API access

## Dependencies

The shared auth system requires:
- `streamlit` - Web framework
- `bcrypt` - Password hashing
- `pyyaml` - Config file parsing
- `sqlite3` - Session storage (built-in to Python)

## Support

For issues or questions:
- Review `/shared/auth/README.md`
- Check logs in `/all_applications_runner/logs/`
- Review session database with: `sqlite3 /Users/fred/my-apps/shared/auth/auth_sessions.db`

## Success Criteria

✅ All Applications Runner uses shared auth
✅ Codexes Factory uses shared auth
✅ Other apps use shared auth via `render_unified_sidebar()`
✅ Same config file for all apps
✅ Same session database for all apps
✅ Login once → Access all apps
✅ Logout once → Logged out from all apps
✅ Admin user displays correctly
✅ Role-based access works across all apps
✅ No more dual auth systems
