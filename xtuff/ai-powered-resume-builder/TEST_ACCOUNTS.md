# Test Accounts Quick Reference

## Starting the Services

```bash
# Terminal 1 - Start central auth/main dashboard
cd /Users/fred/xcu_my_apps/all_applications_runner
uv run streamlit run main.py --server.port=8500

# Terminal 2 - Start AI Resume Builder
cd /Users/fred/xcu_my_apps/xtuff/ai-powered-resume-builder
uv run streamlit run app.py --server.port=8512
```

## URLs
- **Main Dashboard:** http://localhost:8500
- **AI Resume Builder:** http://localhost:8512

## Test Accounts

### 👑 Admin Account
```
Username: admin
Password: hotdogtoy
Role: admin
Tier: premium
Access: All apps, all features
```

### 🆓 Free Tier User
```
Username: johndoe
Password: footballfoot
Role: user
Tier: free
Access: All apps
Features: basic_resume, team_browse only
```

### 💼 Basic Tier User
```
Username: basicbob
Password: basicbob
Role: user
Tier: basic
Access: All apps
Features: basic_resume, team_browse, team_create, ai_generation, document_upload
```

### ⭐ Premium Tier User
```
Username: priscilla
Password: premiumprice
Role: user
Tier: premium
Access: All apps
Features: All features including validation, advanced_ai, priority_support
```

### 🔒 Restricted Access User
```
Username: xtraxtuff
Password: xtraonly
Role: user
Tier: basic
Access: xtuff_ai apps ONLY
Features: Basic tier features, but only for xtuff apps
```

## Testing Scenarios

### Scenario 1: Free User Limitations
1. Login as `johndoe` / `footballfoot`
2. Navigate to AI Resume Builder
3. Try to create a team → Should show "Upgrade to Basic" message
4. Try to generate AI resume → Should show "Upgrade to Basic" message

### Scenario 2: Basic User Capabilities
1. Login as `basicbob` / `basicbob`
2. Create a team → Should work ✅
3. Generate AI resume → Should work with gpt-4o-mini ✅
4. Try advanced AI models → Should show "Upgrade to Premium" ❌

### Scenario 3: Premium User Full Access
1. Login as `priscilla` / `premiumprice`
2. Access all features → Everything should work ✅
3. Use GPT-4 for resume generation → Should work ✅
4. Access validation features → Should work ✅

### Scenario 4: Organization Restrictions
1. Login as `xtraxtuff` / `xtraonly`
2. Go to main dashboard (port 8500)
3. Verify: Only xtuff.ai apps visible
4. Nimble Books apps should not be visible

## Feature Access Matrix

| Feature | Free | Basic | Premium | Admin |
|---------|------|-------|---------|-------|
| basic_resume | ✅ | ✅ | ✅ | ✅ |
| team_browse | ✅ | ✅ | ✅ | ✅ |
| team_create | ❌ | ✅ | ✅ | ✅ |
| ai_generation | ❌ | ✅ | ✅ | ✅ |
| document_upload | ❌ | ✅ | ✅ | ✅ |
| validation | ❌ | ❌ | ✅ | ✅ |
| advanced_ai | ❌ | ❌ | ✅ | ✅ |
| priority_support | ❌ | ❌ | ✅ | ✅ |

## Quick Verification

Run the test script:
```bash
cd /Users/fred/xcu_my_apps/xtuff/ai-powered-resume-builder
python3 test_auth_integration.py
```

## Configuration Files

- **Auth Config:** `/Users/fred/my-apps/all_applications_runner/resources/yaml/config.yaml`
- **Apps Config:** `/Users/fred/my-apps/all_applications_runner/apps_config.json`
- **AI Resume Builder:** `/Users/fred/my-apps/xtuff/ai-powered-resume-builder/app.py`
