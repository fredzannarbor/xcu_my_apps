# Testing Single Sign-On (SSO)

## Quick Test Guide

### Prerequisites

1. Restart All Applications Runner (to load new auth system)
2. Restart Codexes Factory (to ensure clean session)

### Test 1: Basic SSO Login

**Step 1: Login via All Applications Runner**
```
1. Open http://localhost:8500
2. Look for login form in sidebar
3. Enter credentials:
   Username: admin
   Password: hotdogtoy
4. Click Login
```

**Expected:**
- ✅ Success message appears
- ✅ Sidebar shows "👤 Admin"
- ✅ Email shows "admin@nimblebooks.com"
- ✅ Role shows "Admin"

**Step 2: Navigate to Codexes Factory**
```
1. Click "📚 Codexes Factory" link in xtuff.ai navigation
   OR go directly to http://localhost:8502
```

**Expected (SSO Working!):**
- ✅ **Already logged in** (no login prompt!)
- ✅ Sidebar shows same user: "👤 Admin"
- ✅ Email shows "admin@nimblebooks.com"
- ✅ Access to all pages

### Test 2: Cross-App Logout

**Step 1: Logout from Codexes Factory**
```
1. While in Codexes Factory (http://localhost:8502)
2. Click "Logout" button in sidebar
```

**Expected:**
- ✅ Logged out from Codexes Factory
- ✅ Login form appears

**Step 2: Check All Applications Runner**
```
1. Go back to http://localhost:8500
2. Refresh page
```

**Expected (SSO Working!):**
- ✅ **Also logged out** from All Applications Runner
- ✅ Login form appears in sidebar

### Test 3: Admin Access

**After logging in as admin:**

**Check in All Applications Runner:**
- ✅ See "🔧 Management" option
- ✅ See "📊 Monitoring" option
- ✅ See "⚙️ Settings" option
- ✅ Can access all pages

**Check in Codexes Factory:**
- ✅ See all admin-only pages
- ✅ See "Admin" imprint option (if applicable)
- ✅ Full access to all features

### Test 4: Session Persistence

**Step 1: Login**
```
1. Login via All Applications Runner
2. Navigate to Codexes Factory (should be logged in)
```

**Step 2: Close browser**
```
1. Close all browser tabs/windows
```

**Step 3: Reopen (within 30 days)**
```
1. Open http://localhost:8500
```

**Expected:**
- ✅ Still logged in (session persists)
- ✅ User info displayed correctly

### Test 5: Session Database Check

**Verify session was created:**
```bash
sqlite3 /Users/fred/xcu_my_apps/shared/auth/auth_sessions.db \
  "SELECT username, user_name, user_email, user_role FROM active_sessions;"
```

**Expected output:**
```
admin|Admin|admin@nimblebooks.com|admin
```

## Troubleshooting

### Issue: "Authentication system not available"

**Check:**
```bash
ls -la /Users/fred/xcu_my_apps/shared/auth/shared_auth.py
```

**Fix:**
```bash
# Ensure PYTHONPATH includes /Users/fred/xcu_my_apps
export PYTHONPATH=/Users/fred/xcu_my_apps:$PYTHONPATH
```

### Issue: Not staying logged in across apps

**Check session database:**
```bash
sqlite3 /Users/fred/xcu_my_apps/shared/auth/auth_sessions.db ".tables"
```

**Should see:**
```
active_sessions
```

**If table doesn't exist:**
```python
# Run once to initialize database
python3 -c "
import sys
sys.path.insert(0, '/Users/fred/xcu_my_apps')
from shared.auth import get_shared_auth
auth = get_shared_auth()
print('Database initialized')
"
```

### Issue: Login fails with "Invalid username or password"

**Check config file:**
```bash
cat /Users/fred/xcu_my_apps/nimble/codexes-factory/resources/yaml/config.yaml | grep -A5 "admin:"
```

**Should show:**
```yaml
admin:
  email: admin@nimblebooks.com
  name: Admin
  password: hotdogtoy
  role: admin
```

### Issue: User shows as "None" or wrong name

**This should be fixed now! But if it happens:**
1. Check config files have correct admin name ("Admin" not "Admin User")
2. Clear session database:
   ```bash
   rm /Users/fred/xcu_my_apps/shared/auth/auth_sessions.db
   # Will be recreated on next login
   ```

## Test Other Apps

Once SSO is confirmed working, test with other apps:

### Trillions of People (Port 8504)
```
1. Login via All Applications Runner
2. Navigate to Trillions of People
3. Should be automatically logged in
```

### Philately (Port 8507)
```
1. Login via All Applications Runner
2. Navigate to Philately
3. Should be automatically logged in
```

### Any app using `render_unified_sidebar()`
All apps that use the unified sidebar should now have SSO working automatically!

## Success Metrics

✅ **Login once** → Access all apps
✅ **Logout once** → Logged out from all apps
✅ **Session persists** across browser restarts
✅ **User info consistent** across all apps
✅ **Admin access** works in all apps
✅ **No dual login** required

## Performance Check

**Session lookup should be fast:**
```bash
time sqlite3 /Users/fred/xcu_my_apps/shared/auth/auth_sessions.db \
  "SELECT * FROM active_sessions WHERE username='admin';"
```

**Should complete in < 10ms**

## Logs

**Check for auth errors:**
```bash
# All Applications Runner
tail -f /Users/fred/xcu_my_apps/all_applications_runner/logs/*.log

# Streamlit logs
# Usually in ~/.streamlit/logs/
```

**Look for:**
- ✅ "User admin authenticated successfully"
- ✅ "Loaded active session for user: admin"
- ❌ Any errors about "shared auth not found"
- ❌ Any errors about "database locked"

## Next Steps After Testing

Once SSO is confirmed working:

1. Update `/all_applications_runner/ADMIN_CREDENTIALS.md`
2. Remove backup files (keep for 1 week):
   - `auth_integration.py.backup`
   - `main.py.backup`
3. Document SSO in user-facing documentation
4. Test with non-admin users (jsmith, rroe, etc.)
5. Consider implementing user registration UI
