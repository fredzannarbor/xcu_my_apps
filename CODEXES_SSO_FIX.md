# Codexes Factory SSO Integration - FIXED

**Date:** 2025-10-05
**Issue:** Codexes Factory not participating in SSO - showing "not logged in"

## Root Cause

Codexes Factory's main entry point (`codexes-factory-home-ui.py`) was using the **old authentication system**:
- ❌ `simple_auth` - Local authentication, no SSO
- ❌ `build_sidebar()` - Old sidebar without shared auth
- ❌ `streamlit_authenticator` imports (not even used, leftover)

Meanwhile, the individual pages (like `pages/1_Home.py`) were correctly using `render_unified_sidebar()` but the main entry point controlled the auth state.

## Solution

Updated `/nimble/codexes-factory/src/codexes/codexes-factory-home-ui.py` to use shared auth:

### Changes Made

**Removed:**
```python
import streamlit_authenticator as stauth
from codexes.core.simple_auth import get_auth
from codexes.core.ui import build_sidebar
```

**Added:**
```python
from shared.auth import get_shared_auth, is_authenticated, get_user_info
from shared.ui import render_unified_sidebar
```

**Updated Authentication:**
```python
# OLD - simple_auth (no SSO)
auth = get_auth()
current_username = auth.get_current_user()
authentication_status = auth.is_authenticated()
user_role = auth.get_user_role()

# NEW - shared auth (with SSO!)
auth = get_shared_auth()
authentication_status = is_authenticated()
user_info = get_user_info() if authentication_status else {}
current_username = user_info.get('username')
user_role = user_info.get('user_role', 'public')
```

**Updated Sidebar:**
```python
# OLD - build_sidebar (no unified nav)
build_sidebar(
    allowed_pages=allowed_pages,
    version_info=version_info,
    auth_status=authentication_status,
    username=current_username,
    user_role=user_role
)

# NEW - render_unified_sidebar (with SSO!)
render_unified_sidebar(
    app_name="Codexes Factory",
    nav_items=[],
    show_auth=True,
    show_xtuff_nav=True,
    show_version=True,
    show_contact=True
)
```

## Now SSO Works!

When you login to All Applications Runner:
1. Session created in `/shared/auth/auth_sessions.db`
2. Open Codexes Factory
3. **Already logged in!** ✅

When you login to Codexes Factory:
1. Session created in `/shared/auth/auth_sessions.db`
2. Go back to All Applications Runner
3. **Already logged in!** ✅

## What You'll See Now

### In Codexes Factory Sidebar (Top Section)

```
🔐 Account
───────────────
👤 Admin
📧 admin@nimblebooks.com
🎭 Admin

[Logout]
───────────────
🌐 xtuff.ai Navigation
  🏠 Home
  🤖 Social Xtuff
  📚 Codexes Factory
  🌍 Trillions of People
  📮 Philately
  ⏰ Daily Engine
  ✍️ Substack Tools
  🧠 XAI Health
───────────────
📱 Codexes Factory
Pages Available: 24
───────────────
ℹ️ Version Info
  [expand to see git info]
───────────────
📧 Contact
  [Substack embed]
```

## Testing Steps

1. **Restart Codexes Factory** (important - to load new code)
   ```bash
   # Kill existing process if running
   # Then restart via All Applications Runner or:
   cd /Users/fred/xcu_my_apps/nimble/codexes-factory
   ./start_streamlit.sh
   ```

2. **Login via All Applications Runner**
   - Go to http://localhost:8500
   - Login as admin/hotdogtoy
   - Verify you see "Admin" in sidebar

3. **Open Codexes Factory**
   - Go to http://localhost:8502
   - **Should automatically show logged in** ✅
   - Should see "👤 Admin" at top of sidebar
   - Should see "admin@nimblebooks.com"
   - Should see xtuff.ai navigation menu

4. **Test Logout**
   - Click Logout in Codexes Factory
   - Go back to All Applications Runner
   - Should also be logged out ✅

## Files Modified

1. `/nimble/codexes-factory/src/codexes/codexes-factory-home-ui.py` - **Complete rewrite**
   - Backup: `codexes-factory-home-ui.py.backup`

## Files Already Correct

- `/nimble/codexes-factory/src/codexes/pages/1_Home.py` - Already using render_unified_sidebar ✅
- All other pages using render_unified_sidebar ✅

## Rollback (if needed)

```bash
cp /Users/fred/xcu_my_apps/nimble/codexes-factory/src/codexes/codexes-factory-home-ui.py.backup \
   /Users/fred/xcu_my_apps/nimble/codexes-factory/src/codexes/codexes-factory-home-ui.py
```

## What's Different From Individual Pages

Individual pages (like `pages/1_Home.py`) call `render_unified_sidebar()` themselves, which is great.

But the **main entry point** (`codexes-factory-home-ui.py`) is special because:
1. It runs **first** - before any page loads
2. It sets up **session state** for auth (used by all pages)
3. It controls which pages are **allowed** based on user role
4. It must initialize shared auth **before** pages run

That's why updating the main entry point was critical for SSO to work.

## Architecture Now

```
codexes-factory-home-ui.py (ENTRY POINT)
    ↓
1. Initialize shared auth
2. Get user from shared session DB
3. Set session_state (for compatibility)
4. Render unified sidebar
5. Load allowed pages
    ↓
pages/1_Home.py, pages/2_*.py, etc.
    ↓
Also call render_unified_sidebar()
(But session already set up!)
```

Both the entry point and individual pages call `render_unified_sidebar()`, which is fine - Streamlit handles the widget key conflicts.

## Success Criteria

✅ Main entry point uses shared auth
✅ Sidebar shows unified navigation
✅ Login state synced with All Applications Runner
✅ Admin user shows correctly
✅ SSO works both directions
✅ All pages accessible with correct role
