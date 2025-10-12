# Shared Authentication System for xtuff.ai

## Overview

This shared authentication system allows users to log in once and access all xtuff.ai applications with their credentials, role, and subscription entitlements maintained across apps.

## How It Works

1. **Shared Database**: Uses SQLite database at `/Users/fred/my-apps/shared/auth/auth_sessions.db`
2. **User Credentials**: Stored in `/Users/fred/my-apps/nimble/codexes-factory/resources/yaml/config.yaml`
3. **Session Persistence**: Active sessions stored in database, accessible by all apps
4. **Auto-Login**: When you open any app, it checks for active sessions and auto-loads user data

## Features

- ✅ Single sign-on across all xtuff.ai apps
- ✅ Role-based access control (public, user, subscriber, admin)
- ✅ Subscription tier tracking
- ✅ 30-day session persistence
- ✅ Automatic session cleanup
- ✅ Integrated with unified sidebar

## Usage in Apps

### Basic Integration

All apps using `render_unified_sidebar()` automatically get the shared auth system:

```python
from shared.ui import render_unified_sidebar

render_unified_sidebar(
    app_name="My App",
    nav_items=[]
)
```

### Manual Integration

For custom authentication needs:

```python
from shared.auth import get_shared_auth, is_authenticated, get_user_info

# Check authentication
if is_authenticated():
    user_info = get_user_info()
    print(f"Welcome {user_info['user_name']}")
    print(f"Role: {user_info['user_role']}")
    print(f"Subscription: {user_info['subscription_tier']}")
```

### Programmatic Login/Logout

```python
from shared.auth import authenticate, logout

# Login
success, message = authenticate("admin", "hotdogtoy")
if success:
    print(message)  # "Welcome back, Admin User!"

# Logout
logout()
```

## User Data Structure

Each authenticated user has:

- `username`: Login username
- `user_name`: Display name
- `user_email`: Email address
- `user_role`: Access level (public, user, subscriber, admin)
- `subscription_tier`: Subscription level (free, pro, enterprise)
- `subscription_status`: Status (active, inactive)

## Test Accounts

From `config.yaml`:

| Username | Password | Role | Name |
|----------|----------|------|------|
| admin | hotdogtoy | admin | Admin User |
| top | (hashed) | admin | Fred |
| rroe | (hashed) | subscriber | Rebecca Roe |
| jsmith | (hashed) | user | John Smith |

## Database Schema

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

## Session Lifecycle

1. **Login**: User logs in via unified sidebar → Session created in database
2. **Navigation**: User navigates to different app → Session auto-loaded from database
3. **Activity**: Each page load updates `last_accessed` timestamp
4. **Expiration**: Sessions expire after 30 days of inactivity
5. **Logout**: Manual logout deletes session from database

## Security Notes

⚠️ **Current Implementation**: Development mode
- Sessions stored in local SQLite database
- Suitable for single-machine deployment
- Not suitable for production multi-server deployment

🔒 **Production Recommendations**:
- Use Redis or similar for session storage
- Implement HTTPS for all apps
- Use secure cookies for session ID
- Add CSRF protection
- Implement rate limiting
- Use proper token-based auth (JWT)

## Troubleshooting

### Session Not Persisting

Check if `PYTHONPATH` includes `/Users/fred/my-apps`:
```bash
echo $PYTHONPATH
```

### Import Errors

Verify shared module is accessible:
```python
import sys
sys.path.insert(0, '/Users/fred/xcu_my_apps')
from shared.auth import get_shared_auth
```

### Database Locked

If database is locked, close all apps and delete lock file:
```bash
rm /Users/fred/xcu_my_apps/shared/auth/auth_sessions.db-journal
```

## Future Enhancements

- [ ] Integrate with Stripe for subscription management
- [ ] Add user registration through UI
- [ ] Implement password reset flow
- [ ] Add email verification
- [ ] Track login history and analytics
- [ ] Multi-factor authentication
- [ ] OAuth integration (Google, GitHub, etc.)
