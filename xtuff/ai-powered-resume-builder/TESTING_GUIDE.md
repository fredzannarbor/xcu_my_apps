# AI Resume Builder - Authentication Testing Guide

## 🎯 Quick Start Testing

### Step 1: Start Both Services

Open two terminal windows:

**Terminal 1 - Central Auth Dashboard:**
```bash
cd /Users/fred/xcu_my_apps/all_applications_runner
uv run streamlit run main.py --server.port=8500
```

**Terminal 2 - AI Resume Builder:**
```bash
cd /Users/fred/xcu_my_apps/xtuff/ai-powered-resume-builder
uv run streamlit run app.py --server.port=8512
```

### Step 2: Access the Applications

- **Main Dashboard:** http://localhost:8500
- **AI Resume Builder:** http://localhost:8512

---

## 👥 Test Scenarios

### Scenario 1: Admin Access (Full Control)

**Login:** `admin` / `hotdogtoy`

**What to verify:**
1. Login at http://localhost:8500
2. ✅ See all apps from all organizations
3. Navigate to AI Resume Builder
4. ✅ See "Premium Tier" badge
5. ✅ All features accessible:
   - Create teams
   - AI resume generation
   - Advanced AI models (GPT-4)
   - Document upload
   - Validation features

**Expected Result:** Full access to everything

---

### Scenario 2: Free Tier Limitations

**Login:** `johndoe` / `footballfoot`

**What to verify:**
1. Login at http://localhost:8512
2. ✅ See "Free Tier" badge in sidebar
3. Go to "Resume Builder" tab:
   - ✅ Can see basic resume templates
   - ❌ AI generation button shows "Upgrade to Basic" warning
4. Go to "Team Management" tab:
   - ✅ Can browse teams
   - ❌ "Create Team" tab shows "Upgrade to Basic" warning
5. Go to "Document Upload" tab:
   - ❌ Shows "Upgrade to Basic" warning
6. Go to "Validation" tab:
   - ❌ Shows "Upgrade to Premium" warning

**Expected Result:** Limited to browsing only, upgrade prompts for paid features

---

### Scenario 3: Basic Tier Features

**Login:** `basicbob` / `basicbob`

**What to verify:**
1. Login at http://localhost:8512
2. ✅ See "Basic Tier" badge
3. Go to "Resume Builder" tab:
   - ✅ Can generate AI resumes
   - ✅ Model selection shows "gpt-4o-mini (Fast & Efficient)"
   - ❌ Advanced models show "Upgrade to Premium" message
4. Go to "Team Management" tab:
   - ✅ Can create teams
   - ✅ Can browse teams
   - ✅ Can join teams
   - ✅ Can generate team profiles
5. Go to "Document Upload" tab:
   - ✅ Can upload documents
6. Go to "Validation" tab:
   - ❌ Shows "Upgrade to Premium" warning

**Expected Result:** Standard features work, no advanced AI or validation

---

### Scenario 4: Premium Tier (All Features)

**Login:** `priscilla` / `premiumprice`

**What to verify:**
1. Login at http://localhost:8512
2. ✅ See "Premium Tier" badge
3. Go to "Resume Builder" tab:
   - ✅ Can generate AI resumes
   - ✅ Model selection includes:
     - gpt-4o-mini
     - gpt-4o (Advanced)
     - gpt-4-turbo (Balanced)
   - ✅ Can select advanced models
4. Go to "Team Management" tab:
   - ✅ All team features work
5. Go to "Document Upload" tab:
   - ✅ Can upload documents
6. Go to "Validation" tab:
   - ✅ Internal validation works
   - ✅ External verification works
   - ✅ Shows accuracy scores

**Expected Result:** All features fully accessible

---

### Scenario 5: Organization Restrictions

**Login:** `xtraxtuff` / `xtraonly`

**What to verify:**
1. Login at http://localhost:8500 (main dashboard)
2. ✅ See "Basic Tier" badge
3. ✅ In app list, ONLY xtuff.ai apps are visible:
   - Daily Engine
   - Social Xtuff
   - Trillions of People
   - AI Resume Builder
   - etc.
4. ❌ Nimble Books apps should NOT be visible:
   - Codexes Factory (hidden)
   - Max Bialystok (hidden)
5. Navigate to AI Resume Builder (http://localhost:8512)
6. ✅ Can access and use basic features (it's an xtuff app)

**Expected Result:** Only xtuff.ai apps accessible, basic tier features in those apps

---

## ✅ Verification Checklist

### Authentication Flow
- [ ] Login form appears in sidebar
- [ ] Correct credentials allow login
- [ ] Incorrect credentials are rejected
- [ ] Logout button works
- [ ] Session persists across page navigation

### Subscription Badges
- [ ] Free tier shows 🆓 badge
- [ ] Basic tier shows 💼 badge
- [ ] Premium tier shows ⭐ badge
- [ ] Admin shows 👑 or premium badge

### Feature Gating
- [ ] Free users see upgrade prompts for AI generation
- [ ] Free users see upgrade prompts for team creation
- [ ] Basic users can create teams
- [ ] Basic users can use standard AI
- [ ] Basic users see upgrade prompt for advanced AI
- [ ] Premium users can use all AI models
- [ ] Premium users can access validation

### Organization Access
- [ ] xtraxtuff only sees xtuff_ai apps in dashboard
- [ ] Other users see all apps
- [ ] Admin sees all apps

---

## 🔧 Run Automated Tests

```bash
cd /Users/fred/xcu_my_apps/xtuff/ai-powered-resume-builder
python3 test_auth_integration.py
```

Expected output:
```
================================================================================
TEST USER ACCOUNTS IN CONFIG
================================================================================

✅ admin: [all checks pass]
✅ johndoe: [all checks pass]
✅ basicbob: [all checks pass]
✅ priscilla: [all checks pass]
✅ xtraxtuff: [all checks pass]

✅ Configuration test completed successfully!
```

---

## 🐛 Troubleshooting

### Problem: Login doesn't work
**Solution:**
1. Check that main.py is running on port 8500
2. Verify config.yaml has the user account
3. Check browser console for errors

### Problem: Subscription tier not showing
**Solution:**
1. Check session_state.subscription_tier in debug
2. Verify config.yaml has subscription_tier field
3. Restart the app

### Problem: Features not restricted
**Solution:**
1. Review check_subscription_access() in app.py
2. Check subscription_features in apps_config.json
3. Verify tier detection is working

### Problem: xtraxtuff sees all apps
**Solution:**
1. Check app_access field in config.yaml
2. Verify has_app_access() in auth_integration.py
3. Check organization filtering in main.py

---

## 📊 Test Results Table

| Test | johndoe (free) | basicbob (basic) | priscilla (premium) | xtraxtuff (restricted) |
|------|----------------|------------------|---------------------|------------------------|
| Login | ✅ | ✅ | ✅ | ✅ |
| Browse teams | ✅ | ✅ | ✅ | ✅ |
| Create teams | ❌ | ✅ | ✅ | ✅ |
| AI generation | ❌ | ✅ (mini) | ✅ (all) | ✅ (mini) |
| Advanced AI | ❌ | ❌ | ✅ | ❌ |
| Document upload | ❌ | ✅ | ✅ | ✅ |
| Validation | ❌ | ❌ | ✅ | ❌ |
| All orgs | ✅ | ✅ | ✅ | ❌ (xtuff only) |

---

## 📁 Related Files

- **Test Accounts:** [TEST_ACCOUNTS.md](TEST_ACCOUNTS.md)
- **Integration Report:** [AUTH_INTEGRATION_REPORT.md](AUTH_INTEGRATION_REPORT.md)
- **Quick Summary:** [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)
- **Test Script:** [test_auth_integration.py](test_auth_integration.py)

---

**Last Updated:** October 4, 2025
