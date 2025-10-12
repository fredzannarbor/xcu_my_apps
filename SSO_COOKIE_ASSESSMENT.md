# SSO Cookie-Based Authentication Assessment

**Date:** 2025-10-05
**Issue:** Daily Engine shows "not logged in" when launched from All Applications Runner despite active session in database

## Current State

### What Works ✅
1. **Shared Session Database** - `/Users/fred/my-apps/shared/auth/auth_sessions.db`
   - Stores active sessions with 30-day expiration
   - Contains username, role, email, subscription tier
   - Currently has 5 active admin sessions

2. **Unified Sidebar** - `shared/ui/unified_sidebar.py`
   - Shows auth status across all apps
   - Provides login/logout UI
   - Displays user info when authenticated

3. **Within-App SSO** - Works perfectly within same browser tab
   - All Applications Runner: Login persists across page changes
   - Codexes Factory: Login persists across page changes

### What Doesn't Work ❌
1. **Cross-App/Cross-Tab SSO** - Opening new apps in new tabs shows "not logged in"
   - Root cause: `shared_session_id` stored in `st.session_state` (per-tab)
   - Each new tab/window starts fresh Streamlit session
   - No browser cookie to identify which DB session belongs to user

2. **Cross-Port Authentication** - Different ports don't share session
   - All Apps Runner: localhost:8500
   - Codexes Factory: localhost:8502
   - Daily Engine: localhost:8509
   - Each is a separate Streamlit app instance

## Root Cause Analysis

### Current Implementation (Incomplete)
```python
# Line 97-101 in shared/auth/shared_auth.py
if 'shared_session_id' not in st.session_state:
    # Try to find any active session for this browser
    # In production, this would use cookies or similar
    self._initialize_empty_session()
    return
```

**Problem:** Comment says "this would use cookies" but it doesn't. Uses `st.session_state` which is:
- Unique per browser tab
- Unique per Streamlit app instance
- Lost when tab closes or new tab opens
- NOT accessible across different ports

### What's Needed
Browser cookies to store `shared_session_id` so:
1. User logs in on localhost:8500 (All Apps Runner)
2. Cookie saved: `shared_session_id=mWveSV3aR4XXi4teVgKU8pvFTwr4l8R5g3ykK-tuSGo`
3. Cookie domain: `localhost` (works across all ports)
4. User opens localhost:8509 (Daily Engine)
5. Daily Engine reads cookie, loads session from database
6. User automatically logged in

## Solution Options

### Option A: Use extra-streamlit-components (Recommended)
**Library:** `extra-streamlit-components`
**Pros:**
- Popular Streamlit cookie library
- Simple API: `cookie_manager.get()`, `cookie_manager.set()`
- Works across different Streamlit ports on same domain
- Well-maintained, widely used

**Cons:**
- External dependency
- Adds JavaScript component
- Slight overhead

**Implementation:**
```python
import extra_streamlit_components as stx

# In _check_active_session()
cookie_manager = stx.CookieManager()
session_id = cookie_manager.get('shared_session_id')

if session_id:
    # Load from database
    self._load_session_from_db(session_id)
else:
    # No cookie, user not logged in
    self._initialize_empty_session()

# In authenticate()
cookie_manager.set('shared_session_id', new_session_id,
                   max_age=30*24*60*60,  # 30 days
                   domain='localhost')    # Works across ports
```

**Effort:** 2-3 hours
- Add dependency to pyproject.toml
- Update `shared_auth.py` (3 methods)
- Test across apps
- Update documentation

### Option B: Use streamlit-cookies-manager
**Library:** `streamlit-cookies-manager`
**Pros:**
- Another popular option
- Similar API

**Cons:**
- Less active maintenance than extra-streamlit-components
- Similar overhead

**Effort:** 2-3 hours (same as Option A)

### Option C: Custom JavaScript Cookie Implementation
**Approach:** Use `st.components.v1.html()` with custom JavaScript

**Pros:**
- No external dependencies
- Full control

**Cons:**
- More complex to implement
- Harder to maintain
- Need to handle cookie encoding/security manually
- More prone to bugs

**Effort:** 4-6 hours

### Option D: Query Parameter Session Passing
**Approach:** Pass session_id in URL when launching apps

**Example:**
```
localhost:8509/?session_id=mWveSV3aR4XXi4teVgKU8pvFTwr4l8R5g3ykK-tuSGo
```

**Pros:**
- No dependencies
- Simple to implement
- Works immediately

**Cons:**
- ❌ **SECURITY RISK** - Session ID visible in URL
- ❌ Session ID appears in browser history
- ❌ Can be accidentally shared/leaked
- ❌ Not suitable for production
- Only works for direct links (not manual navigation)

**Effort:** 1 hour
**Recommendation:** ❌ **DO NOT USE** - Security risk

### Option E: Keep Current State (No Cross-App SSO)
**Approach:** Accept limitation, require login per app

**Pros:**
- Zero effort
- No changes needed
- Still works within each app

**Cons:**
- Poor user experience
- Defeats purpose of SSO
- Users must login separately in each app

**Recommendation:** ❌ Not acceptable for production

## Recommended Implementation Plan

### Phase 1: Add Cookie Support (Option A)
**Timeline:** 1 sprint / 2-3 hours

1. **Add Dependency**
   ```bash
   uv add extra-streamlit-components
   ```

2. **Update `shared/auth/shared_auth.py`**
   - Import `extra_streamlit_components as stx`
   - Initialize `CookieManager` in `__init__`
   - Update `_check_active_session()` to read from cookie
   - Update `authenticate()` to set cookie
   - Update `logout()` to clear cookie

3. **Test SSO Flow**
   - Login on All Apps Runner (port 8500)
   - Verify cookie set in browser DevTools
   - Open Codexes Factory (port 8502) - should auto-login
   - Open Daily Engine (port 8509) - should auto-login
   - Logout from any app - should clear cookie everywhere

4. **Update Documentation**
   - Update FINAL_SSO_STATUS.md with cookie implementation
   - Document cookie security settings
   - Add troubleshooting guide

### Phase 2: Security Hardening
**Timeline:** 1 sprint / 2-3 hours

1. **Cookie Security Settings**
   ```python
   cookie_manager.set('shared_session_id', session_id,
                      max_age=30*24*60*60,     # 30 days
                      domain='localhost',       # All ports
                      path='/',                 # All paths
                      secure=False,             # True in production with HTTPS
                      same_site='Lax')          # CSRF protection
   ```

2. **Session Validation**
   - Check session expiration
   - Verify session exists in database
   - Handle corrupted cookies gracefully

3. **Production Preparation**
   - Use `secure=True` with HTTPS
   - Use proper domain (`.xtuff.ai`)
   - Add session rotation
   - Add CSRF tokens for mutations

### Phase 3: Production Deployment
**Timeline:** Ongoing

1. **Domain Configuration**
   ```python
   # Development
   domain = 'localhost'

   # Production
   domain = '.xtuff.ai'  # Works for all *.xtuff.ai subdomains
   ```

2. **HTTPS Requirements**
   - Enable `secure=True` flag
   - Requires valid SSL certificate
   - Cookies won't work over HTTP in production

## Code Changes Required

### File: `/Users/fred/my-apps/pyproject.toml`
```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "extra-streamlit-components>=0.1.56",
]
```

### File: `/Users/fred/my-apps/shared/auth/shared_auth.py`

**Add Import:**
```python
import extra_streamlit_components as stx
```

**Update `__init__` method:**
```python
def __init__(self):
    self.db_path = SHARED_AUTH_DB
    self.config_path = SHARED_CONFIG_PATH
    self._ensure_db_exists()
    self.config = self._load_config()

    # Initialize cookie manager
    self.cookie_manager = stx.CookieManager()

    # Initialize session state if needed
    if 'auth_checked' not in st.session_state:
        self._check_active_session()
```

**Replace `_check_active_session` method:**
```python
def _check_active_session(self):
    """Check if there's an active session using browser cookie."""
    st.session_state.auth_checked = True

    # Try to get session ID from cookie
    session_id = self.cookie_manager.get('shared_session_id')

    if not session_id:
        self._initialize_empty_session()
        return

    # Load session from database
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, user_name, user_email, user_role,
               subscription_tier, subscription_status, expires_at
        FROM active_sessions
        WHERE session_id = ?
    """, (session_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        username, user_name, user_email, user_role, sub_tier, sub_status, expires_at = row

        # Check if session expired
        if datetime.fromisoformat(expires_at) < datetime.now():
            self._delete_session(session_id)
            self.cookie_manager.delete('shared_session_id')
            self._initialize_empty_session()
            return

        # Load session data into st.session_state
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.user_name = user_name
        st.session_state.user_email = user_email
        st.session_state.user_role = user_role
        st.session_state.subscription_tier = sub_tier or 'free'
        st.session_state.subscription_status = sub_status or 'inactive'
        st.session_state.shared_session_id = session_id

        # Update last accessed time
        self._update_session_access(session_id)

        logger.info(f"Loaded session from cookie for user: {username}")
    else:
        # Session ID in cookie but not in database (expired/deleted)
        self.cookie_manager.delete('shared_session_id')
        self._initialize_empty_session()
```

**Update `authenticate` method** (add cookie setting):
```python
def authenticate(self, username: str, password: str) -> Tuple[bool, str]:
    """Authenticate user and create session."""
    # ... existing validation code ...

    # Create session
    session_id = self._generate_session_id()

    # ... existing database insert code ...

    # Set browser cookie for cross-app SSO
    self.cookie_manager.set(
        'shared_session_id',
        session_id,
        max_age=30*24*60*60,  # 30 days in seconds
        domain='localhost',    # Works across all ports
        path='/',
        same_site='Lax'
    )

    logger.info(f"Session cookie set for user: {username}")

    return True, "Login successful"
```

**Update `logout` method** (add cookie clearing):
```python
def logout(self):
    """Logout user and clear session."""
    if st.session_state.get('shared_session_id'):
        # Delete from database
        self._delete_session(st.session_state.shared_session_id)

        # Delete browser cookie
        self.cookie_manager.delete('shared_session_id')

    # Clear session state
    self._initialize_empty_session()

    logger.info("User logged out, cookie cleared")
```

## Testing Plan

### Test Case 1: Cross-App Login
1. Open All Applications Runner (localhost:8500)
2. Login as admin/hotdogtoy
3. Verify login successful
4. Open Codexes Factory (localhost:8502) in NEW TAB
5. **Expected:** Automatically logged in as admin
6. **Verify:** User info shows "👤 Admin" in sidebar

### Test Case 2: Cross-App Logout
1. With both apps open and logged in
2. Logout from Codexes Factory
3. **Expected:** Both apps show logged out
4. Refresh All Applications Runner
5. **Expected:** Still logged out

### Test Case 3: Session Expiration
1. Login to any app
2. Manually update database: `UPDATE active_sessions SET expires_at = '2020-01-01' WHERE username='admin'`
3. Refresh page
4. **Expected:** Logged out, cookie deleted

### Test Case 4: Cookie Persistence
1. Login to All Apps Runner
2. Close browser completely
3. Reopen browser to localhost:8500
4. **Expected:** Still logged in (cookie persists)

### Test Case 5: Daily Engine Integration
1. Login to All Apps Runner
2. Click "Nimble Books" button → opens Daily Engine
3. **Expected:** Daily Engine shows logged in
4. **Verify:** Can access all features

## Migration Strategy

### Zero-Downtime Migration
1. **Add Cookie Support** (backward compatible)
   - New code reads from cookie OR st.session_state
   - Existing sessions continue working
   - New logins use cookies

2. **Deploy to All Apps** (gradually)
   - Update All Applications Runner first
   - Update Codexes Factory
   - Update Daily Engine
   - Update other apps

3. **Monitor and Validate**
   - Check browser DevTools for cookies
   - Verify database sessions
   - Test cross-app navigation

## Security Considerations

### Development (localhost)
```python
cookie_manager.set('shared_session_id', session_id,
                   max_age=30*24*60*60,
                   domain='localhost',   # All ports
                   secure=False,         # HTTP ok for dev
                   same_site='Lax')
```

### Production (xtuff.ai)
```python
cookie_manager.set('shared_session_id', session_id,
                   max_age=30*24*60*60,
                   domain='.xtuff.ai',   # All subdomains
                   secure=True,          # HTTPS only
                   same_site='Strict',   # CSRF protection
                   http_only=True)       # JavaScript can't access
```

### Additional Security
1. **Session Rotation** - Generate new session_id periodically
2. **IP Validation** - Store and validate user IP (optional)
3. **User Agent Validation** - Detect session hijacking
4. **CSRF Tokens** - For state-changing operations
5. **Audit Logging** - Track all auth events

## Cost-Benefit Analysis

### Benefits of Implementation
- ✅ True SSO across all apps
- ✅ Better user experience
- ✅ Production-ready authentication
- ✅ Standard industry practice
- ✅ Enables future multi-server deployment

### Costs
- ⏱️ 2-3 hours implementation
- 📦 One additional dependency
- 🧪 Testing and validation time
- 📝 Documentation updates

### ROI
**High** - This is a critical feature for multi-app ecosystem

## Recommendation

**✅ PROCEED with Option A (extra-streamlit-components)**

**Rationale:**
1. Current implementation is incomplete (noted in code comments)
2. Small effort (2-3 hours) for major UX improvement
3. Industry-standard approach (cookies for SSO)
4. Well-supported library
5. Enables future production deployment

**Next Steps:**
1. User approves this assessment
2. Add `extra-streamlit-components` to dependencies
3. Implement cookie-based session management
4. Test across all apps
5. Update documentation
6. Deploy to all applications

## Alternative: Why NOT Query Parameters?

While query parameters (`?session_id=...`) are simpler to implement, they are **NOT recommended** because:

1. **Security Risk** - Session ID visible in:
   - Browser address bar
   - Browser history
   - Server logs
   - Referrer headers when clicking external links
   - Shared screenshots/recordings

2. **Session Hijacking** - Anyone with the URL can impersonate the user

3. **Not Standard** - Industry practice is cookies/localStorage for sessions

4. **Limited Scope** - Only works for direct navigation, not manual URL entry

**Verdict:** ❌ Do not use query parameters for session management

## Conclusion

The current SSO implementation has the right architecture (shared database) but is missing the critical piece: **browser cookies** to persist session_id across tabs and apps.

Implementing cookie-based authentication using `extra-streamlit-components` is:
- ✅ Low effort (2-3 hours)
- ✅ High value (true SSO)
- ✅ Industry standard
- ✅ Production ready
- ✅ Secure when properly configured

**Recommendation: Implement Option A immediately**
