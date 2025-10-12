# Stripe Testing Guide - xtuff.ai V2 Revenue

## 🎯 Objective
Test the complete $49/mo Premium subscription checkout flow using Stripe test mode.

---

## 🔧 Configuration Status

### ✅ Environment Variables Set:
```bash
STRIPE_SECRET_KEY=sk_test_51HSpP0EkhPBoRSzt...
STRIPE_PUBLISHABLE_KEY=pk_test_51HSpP0EkhPBoRSzt...
STRIPE_PREMIUM_ALL_ACCESS_PRICE_ID=price_1SGDm6EkhPBoRSztHrI6sYBq
```

### ✅ Stripe Product Created:
- **Product:** xtuff.ai Premium Architect
- **Price:** $49.00 USD/month
- **Price ID:** price_1SGDm6EkhPBoRSztHrI6sYBq
- **Mode:** Test (recurring subscription)

---

## 🧪 Complete Testing Workflow

### Phase 1: Free User Journey (Minutes 0-5)

**Step 1.1: Visit Home Page**
- Navigate to http://localhost:8500
- Verify hero section displays:
  - "Your Personal AI Multiverse"
  - "The Last Platform You'll Ever Need. Because It Builds The Others."
  - Early access urgency banner: "🔥 EARLY ACCESS PRICING: Lock in $49/mo forever"

**Step 1.2: Create Test Account**
- In sidebar, create account with test email:
  - Email: `test+stripe001@example.com`
  - Name: `Test User Premium`
  - Password: `TestPassword123!`
- Verify account creation successful
- Check sidebar shows "🆓 Free Explorer" status

**Step 1.3: Explore Free Features**
- Click through each of the 4 featured apps:
  - 🧠 Agentic Social Server
  - 👤 AI Resume Builder
  - 🌍 TrillionsOfPeople
  - ⚡ Daily Engine
- Verify free tier limitations are shown:
  - "✅ 3 AI personas" (Social)
  - "✅ 1 basic resume" (Resume Builder)
  - "✅ Browse 100 sample personas" (Trillions)
  - "✅ Basic task management" (Daily Engine)

**Step 1.4: Hit Paywalls**
- Verify "🔒 Unlock with Premium" sections appear
- Verify locked features listed:
  - "🔒 All 147 personas"
  - "🔒 Unlimited resumes"
  - "🔒 All 118,000,000,000 personas"
  - "🔒 AI optimization"

---

### Phase 2: Conversion Journey (Minutes 5-10)

**Step 2.1: Navigate to Pricing**
- Click "💎 Go Premium" in sidebar OR
- Click "💳 Pricing" in navigation OR
- Click "⬆️ Upgrade to Premium" button on any app card

**Step 2.2: Review Pricing Page**
Verify all elements present:
- Hero: "Choose Your Reality"
- Urgency: "🔥 Early Access Pricing - Lock In Your Rate Forever"
- Guarantee badge: "🛡️ 30-Day Money-Back Guarantee"
- Three pricing tiers visible:
  - **Free Explorer** ($0)
  - **Premium Architect** ($49/mo) ⭐ BEST VALUE - highlighted
  - **Enterprise** (Custom)

**Step 2.3: Verify Premium Tier Details**
Check Premium column shows:
- Price: "$49/mo" with "~~$79/mo~~ Early access pricing"
- Features:
  - ✅ All apps - full access
  - ✅ Unlimited everything
  - ✅ 147 AI personas (Social)
  - ✅ 118 billion personas (Trillions)
  - ✅ Unlimited resumes (AI Builder)
  - ✅ Future apps - early access
  - ✅ Priority email support
  - ✅ Rate locked forever
- Button: "🚀 UNLOCK EVERYTHING" (primary, enabled)

**Step 2.4: Review Value Proposition**
Scroll down and verify:
- "Why Premium is a No-Brainer" section
- Math showing savings: "$91/month = $1,092/year"
- List of current apps + future apps (2026 dates)
- FAQ section with 5 questions answered

---

### Phase 3: Stripe Checkout Flow (Minutes 10-15)

**Step 3.1: Initiate Checkout**
- Click "🚀 UNLOCK EVERYTHING" button
- App should:
  - Create Stripe checkout session
  - Redirect to Stripe checkout page
  - Display loading message: "Redirecting to checkout..."

**Step 3.2: Stripe Checkout Page**
Verify Stripe hosted checkout shows:
- Logo/branding (if configured)
- Product: "xtuff.ai Premium Architect"
- Price: "$49.00 / month"
- Email pre-filled: `test+stripe001@example.com`
- Card payment form

**Step 3.3: Test Card Payment**
Use Stripe test cards (https://stripe.com/docs/testing):

**Success Test:**
```
Card number: 4242 4242 4242 4242
Expiry: Any future date (e.g., 12/30)
CVC: Any 3 digits (e.g., 123)
ZIP: Any 5 digits (e.g., 12345)
```

**Step 3.4: Complete Payment**
- Click "Subscribe" button
- Wait for processing
- Should redirect back to: http://localhost:8500?session_id={CHECKOUT_SESSION_ID}

---

### Phase 4: Post-Purchase Verification (Minutes 15-20)

**Step 4.1: Verify Premium Access**
After redirect, check:
- Sidebar status changed to: "💎 Premium Member"
- Early access urgency banner REMOVED (no longer shown)
- Navigate to "💳 Pricing" page

**Step 4.2: Check Subscription Status**
On Pricing page, verify:
- Green banner: "✅ You have 1 active subscription(s)"
- Expandable "View My Subscriptions" section shows:
  - Type: "All Access"
  - Status: "active"
  - Renewal date shown

**Step 4.3: Test Premium App Access**
Navigate back to "🏠 Home" and verify:
- All 4 apps show "🚀 Launch {AppName}" buttons (not locked)
- No more "🔒 Premium Features Locked" messages
- Can click through to any app

**Step 4.4: Verify in Stripe Dashboard**
- Go to https://dashboard.stripe.com/test/subscriptions
- Find subscription for test+stripe001@example.com
- Verify:
  - Status: Active
  - Amount: $49.00 USD
  - Interval: month
  - Metadata includes:
    - `user_email`: test+stripe001@example.com
    - `type`: all_access

---

### Phase 5: Edge Cases & Error Handling (Minutes 20-25)

**Test 5.1: Duplicate Subscription Attempt**
- While logged in with active subscription
- Navigate to Pricing page
- Try clicking "🚀 UNLOCK EVERYTHING" again
- Expected: Should still work (Stripe handles duplicates)

**Test 5.2: Failed Payment**
Create new test user: test+stripe002@example.com

Use decline test card:
```
Card: 4000 0000 0000 0002 (card declined)
```
- Expected: Stripe shows error, returns to form
- User remains on free tier

**Test 5.3: Insufficient Funds**
Create new test user: test+stripe003@example.com

Use insufficient funds card:
```
Card: 4000 0000 0000 9995
```
- Expected: Stripe shows error
- User can retry with valid card

**Test 5.4: Logout/Login Persistence**
- Logout from Premium account
- Login again with same credentials
- Verify Premium status persists
- Check subscription still active

---

## 🐛 Common Issues & Solutions

### Issue 1: "Coming Soon" Button Instead of Checkout
**Symptom:** Premium button says "Coming Soon" and is disabled

**Cause:** Stripe price ID not loaded properly

**Fix:**
```bash
# Check environment variable is set
grep STRIPE_PREMIUM_ALL_ACCESS_PRICE_ID .env

# Restart app to reload .env
pkill -f "streamlit run main.py"
uv run streamlit run main.py --server.port=8500
```

### Issue 2: Checkout Session Creation Fails
**Symptom:** Error message when clicking "UNLOCK EVERYTHING"

**Check:**
1. Stripe secret key valid and in test mode
2. Price ID exists in Stripe dashboard
3. Check logs for detailed error

### Issue 3: Redirect After Payment Fails
**Symptom:** Payment succeeds but doesn't return to app

**Fix:**
- Check success_url in subscription_manager.py (line 164)
- Should be: `http://localhost:8500?session_id={CHECKOUT_SESSION_ID}`
- Verify port matches running app

### Issue 4: Premium Access Not Granted
**Symptom:** Payment succeeds but user still sees free tier

**Debug Steps:**
1. Check Stripe subscription metadata includes user_email
2. Verify subscription status is "active"
3. Check subscription_manager.get_user_subscriptions() returns data
4. Ensure user is logged in with same email used for Stripe

---

## 📊 Success Metrics to Track

### Conversion Funnel:
1. **Visitors** → 100%
2. **Free Signups** → Target 20%
3. **View Pricing Page** → Target 60% of signups
4. **Start Checkout** → Target 30% of pricing page viewers
5. **Complete Payment** → Target 80% of checkout initiations
6. **Overall Conversion** → Target 10-15% (free → paid)

### Technical Checks:
- ✅ Checkout session creates successfully
- ✅ Payment processes without errors
- ✅ Subscription appears in Stripe dashboard
- ✅ User role updates to Premium
- ✅ App access gates unlock
- ✅ Subscription persists across sessions

---

## 🎯 Next Steps After Testing

### If All Tests Pass:
1. ✅ Document any bugs found
2. ✅ Test on mobile browser (responsive)
3. ✅ Test in different browsers (Chrome, Safari, Firefox)
4. ✅ Verify email notifications (if configured)
5. ✅ Test cancellation flow
6. ✅ Test failed payment recovery (dunning)

### Before Production:
1. 🔄 Switch Stripe keys from test to live mode
2. 🔄 Create live price in Stripe (same $49/mo)
3. 🔄 Update STRIPE_PREMIUM_ALL_ACCESS_PRICE_ID with live price ID
4. 🔄 Test once more with real card (small amount, then refund)
5. 🔄 Set up Stripe webhooks for subscription events
6. 🔄 Configure email notifications for payments

---

## 📧 Stripe Test Mode Resources

- **Dashboard:** https://dashboard.stripe.com/test/dashboard
- **Test Cards:** https://stripe.com/docs/testing
- **Webhooks:** https://dashboard.stripe.com/test/webhooks
- **Logs:** https://dashboard.stripe.com/test/logs

**Test Email Addresses:**
- Use `+` addressing: yourname+test001@gmail.com
- All go to same inbox but treated as unique by Stripe

**Test Card Numbers:**
- Success: 4242 4242 4242 4242
- Decline: 4000 0000 0000 0002
- Insufficient funds: 4000 0000 0000 9995
- Expired: 4000 0000 0000 0069
- 3DS required: 4000 0027 6000 3184

---

## ✅ Testing Checklist

Copy this checklist for each test run:

```
[ ] Created test user account
[ ] Explored free tier features
[ ] Hit paywalls (locked features visible)
[ ] Navigated to pricing page
[ ] Verified Premium tier details
[ ] Clicked "UNLOCK EVERYTHING"
[ ] Redirected to Stripe checkout
[ ] Completed payment with test card
[ ] Redirected back to app
[ ] Premium status shown in sidebar
[ ] All apps unlocked
[ ] Subscription visible on pricing page
[ ] Subscription shows in Stripe dashboard
[ ] Logged out and back in (status persists)
[ ] Tested failed payment card
[ ] Tested edge cases
```

---

**Last Updated:** 2025-10-09
**Version:** V2 Revenue-Focused
**Stripe Mode:** Test
**Price:** $49/mo (price_1SGDm6EkhPBoRSztHrI6sYBq)
