# Admin Credentials for All Applications Runner

**Date Updated:** 2025-10-03 06:40 UTC
**Server:** book-publisher-agi (Debian)
**Authentication:** streamlit-authenticator (centralized)

## Master Dashboard (All Applications Runner)

**Access URL:**
- Local: http://127.0.0.1:8500
- Public: http://xtuff.ai (when DNS configured)

**Authentication Method:** streamlit-authenticator (built-in)

**Admin Access:**
The All Applications Runner now has its own authentication system using streamlit-authenticator.

---

## Login Instructions

### How to Login:

1. Go to http://xtuff.ai (or http://127.0.0.1:8500)
2. Look at the **sidebar** - you'll see the login widget
3. Enter credentials:
   - **Username:** `admin` (NOT email - use username!)
   - **Password:** `hotdogtoy`
4. Click "Login"

### Admin Account

**Username:** `admin`
**Password:** `hotdogtoy`
**Email:** admin@nimblebooks.com
**Role:** admin

**Config Location:** `/home/wfz/bin/all_applications_runner/resources/yaml/config.yaml`

### Other Test Accounts

**Account: top**
- Username: `top`
- Password: (bcrypt hashed)
- Email: top@nimblebooks.com
- Name: Fred
- Role: user

**Account: publictest**
- Username: `publictest`
- Password: (bcrypt hashed)
- Email: fred@nimblebooks.com
- Name: public test account
- Role: public

**Account: rroe**
- Username: `rroe`
- Password: (bcrypt hashed)
- Email: rroe@example.com
- Name: Rebecca Roe
- Role: subscriber

**Account: jsmith**
- Username: `jsmith`
- Password: (bcrypt hashed)
- Email: jsmith@example.com
- Name: John Smith
- Role: user

---

## Admin Privileges

Once logged in as admin, you have access to:
- 🔧 **Management** - Process control (start/stop apps)
- 📊 **Monitoring** - System health and metrics
- ⚙️ **Settings** - Configuration management
- All public features

---

## Role Hierarchy

The system uses the following role hierarchy:

0. **anonymous** - Public access only
1. **registered** - Basic registered user
2. **subscriber** - Paid subscriber
3. **admin** - Administrator
4. **superadmin** - Super administrator

**Note:** The `admin` account provides level 3 access, granting full administrative privileges to the All Applications Runner.

---

## Services Status

### All Applications Runner
```bash
sudo systemctl status all-apps-runner.service
```

### Check Application
```bash
curl -I http://127.0.0.1:8500  # Should return HTTP 200
```

### View Logs
```bash
tail -f /home/wfz/bin/all_applications_runner/logs/runner.log
sudo journalctl -u all-apps-runner.service -f
```

---

## Security Notes

⚠️ **IMPORTANT:**
- The admin password `hotdogtoy` is stored in **plaintext** in config.yaml
- Other accounts use bcrypt hashed passwords
- For production, you should hash the admin password

### To Change Admin Password

1. Generate bcrypt hash:
```python
import bcrypt
password = "your_new_password"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
print(hashed.decode())
```

2. Update `/home/wfz/bin/all_applications_runner/resources/yaml/config.yaml`
3. Restart service:
```bash
sudo systemctl restart all-apps-runner.service
```

---

## Troubleshooting

### Login Not Working

1. **Check service is running:**
   ```bash
   sudo systemctl status all-apps-runner.service
   ```

2. **Verify config file exists:**
   ```bash
   cat /home/wfz/bin/all_applications_runner/resources/yaml/config.yaml
   ```

3. **Check logs for errors:**
   ```bash
   tail -f /home/wfz/bin/all_applications_runner/logs/runner-error.log
   sudo journalctl -u all-apps-runner.service -f
   ```

4. **Clear browser cookies** - streamlit-authenticator uses cookies

5. **Try incognito/private browsing** to test without cached cookies

### Adding New Users

Edit `/home/wfz/bin/all_applications_runner/resources/yaml/config.yaml`:

```yaml
credentials:
  usernames:
    newuser:
      email: newuser@example.com
      name: New User Name
      password: $2b$12$BCRYPT_HASH_HERE
      role: user  # or subscriber, admin, etc.
```

Then restart:
```bash
sudo systemctl restart all-apps-runner.service
```

---

**Last Updated:** 2025-10-03 06:40 UTC
**System:** All Applications Runner with streamlit-authenticator
