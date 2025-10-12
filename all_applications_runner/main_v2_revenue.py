#!/usr/bin/env python3
"""
xtuff.ai - Your Personal AI Multiverse
Revenue-Optimized V2 - The Last Platform You'll Ever Need

Focus: 4 working apps + algorithmic future
No fake social proof - honest conversion optimization
"""

import json
import streamlit as st
import requests
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import logging

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from process_manager import ProcessManager
from auth_integration import get_auth_manager, AuthManager
from subscription_manager import get_subscription_manager, SubscriptionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="xtuff.ai - Your Personal AI Multiverse",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Medium-bold visual design
st.markdown("""
<style>
    /* Color Palette */
    :root {
        --primary: #6366F1;
        --primary-dark: #4F46E5;
        --secondary: #8B5CF6;
        --accent: #F59E0B;
        --success: #10B981;
        --dark: #1F2937;
    }

    /* Hero Section */
    .hero-multiverse {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 60px 40px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 40px;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
    }

    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 16px;
        line-height: 1.1;
        background: linear-gradient(to right, #fff, #e0e7ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .hero-subtitle {
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 20px;
        opacity: 0.95;
    }

    .hero-description {
        font-size: 1.2rem;
        margin-bottom: 32px;
        opacity: 0.9;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
    }

    /* Urgency Banner */
    .urgency-banner {
        background: linear-gradient(90deg, #F59E0B, #EF4444);
        color: white;
        padding: 16px;
        border-radius: 12px;
        text-align: center;
        font-weight: 700;
        margin: 24px 0;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.9; }
    }

    /* App Card */
    .app-card {
        background: white;
        border: 2px solid #E5E7EB;
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 24px;
        transition: all 0.3s ease;
    }

    .app-card:hover {
        border-color: var(--primary);
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.2);
        transform: translateY(-4px);
    }

    .app-icon {
        font-size: 3rem;
        margin-bottom: 16px;
    }

    .app-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--dark);
        margin-bottom: 12px;
    }

    .app-tagline {
        font-size: 1.1rem;
        color: var(--primary);
        font-weight: 600;
        margin-bottom: 16px;
        font-style: italic;
    }

    /* Premium Lock Badge */
    .premium-lock {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        text-align: center;
        margin: 20px 0;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .premium-lock:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    }

    /* Feature List */
    .feature-list {
        margin: 16px 0;
    }

    .feature-item {
        padding: 8px 0;
        font-size: 1.05rem;
    }

    .feature-free {
        color: #10B981;
    }

    .feature-locked {
        color: #9CA3AF;
    }

    /* Pricing Table */
    .pricing-card {
        background: white;
        border: 3px solid #E5E7EB;
        border-radius: 20px;
        padding: 32px;
        text-align: center;
        transition: all 0.3s ease;
    }

    .pricing-card-premium {
        border-color: var(--primary);
        background: linear-gradient(to bottom, #EEF2FF, white);
        transform: scale(1.05);
        box-shadow: 0 20px 60px rgba(99, 102, 241, 0.3);
    }

    .pricing-badge {
        background: var(--accent);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 16px;
    }

    .price-amount {
        font-size: 4rem;
        font-weight: 800;
        color: var(--primary);
        margin: 16px 0;
    }

    .price-strikethrough {
        text-decoration: line-through;
        opacity: 0.5;
        font-size: 2rem;
    }

    /* Coming Soon Badge */
    .coming-soon {
        background: linear-gradient(135deg, #8B5CF6, #EC4899);
        color: white;
        padding: 24px;
        border-radius: 16px;
        margin: 16px 0;
    }

    /* Social Proof Placeholder */
    .social-proof-placeholder {
        background: #F9FAFB;
        border: 2px dashed #D1D5DB;
        border-radius: 12px;
        padding: 32px;
        text-align: center;
        color: #6B7280;
        margin: 24px 0;
    }

    /* Guarantee Badge */
    .guarantee {
        background: var(--success);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        font-weight: 600;
        margin: 24px 0;
    }
</style>
""", unsafe_allow_html=True)

def get_managers():
    """Initialize manager instances."""
    try:
        auth_manager = get_auth_manager()
        subscription_manager = get_subscription_manager()
        return auth_manager, subscription_manager
    except Exception as e:
        logger.error(f"Error initializing managers: {e}")
        return None, None

def load_config():
    """Load the applications configuration."""
    config_path = Path(__file__).parent / "apps_config.json"
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Configuration file not found: {config_path}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON in configuration: {e}")
        return None

def get_app_status():
    """Get current status of all applications."""
    try:
        manager = ProcessManager()
        manager.initialize_processes()
        return manager.get_status()
    except Exception as e:
        st.error(f"Error getting app status: {e}")
        return None

def render_sidebar(auth_manager: AuthManager, user_role: str):
    """Render the navigation sidebar."""
    st.sidebar.markdown("# 🌌 xtuff.ai")
    st.sidebar.markdown("**Your Personal AI Multiverse**")

    st.sidebar.markdown("---")

    # CTA Buttons
    col1, col2 = st.sidebar.columns([1, 1])
    with col1:
        if st.button("🚀 Explore Free", type="primary", use_container_width=True):
            st.session_state["selected_page"] = "🏠 Home"
            st.rerun()
    with col2:
        if st.button("💎 Go Premium", use_container_width=True):
            st.session_state["selected_page"] = "💳 Pricing"
            st.rerun()

    st.sidebar.markdown("---")

    # User info
    user = auth_manager.get_current_user() if auth_manager else None

    if user:
        st.sidebar.subheader("👤 Account")
        st.sidebar.write(f"**{user.get('name', 'User')}**")

        if user_role == "subscriber":
            st.sidebar.success("💎 Premium Member")
        elif user_role in ["admin", "superadmin"]:
            st.sidebar.success(f"🔧 {user_role.title()}")
        else:
            st.sidebar.info("🆓 Free Explorer")
            st.sidebar.caption("Upgrade to unlock everything")

        st.sidebar.markdown("---")

    # Navigation
    if user_role in ["admin", "superadmin"]:
        page = st.sidebar.selectbox(
            "Navigate:",
            ["🏠 Home", "💳 Pricing", "🔧 Management", "📊 Monitoring", "⚙️ Settings"]
        )
    else:
        page = st.sidebar.selectbox(
            "Navigate:",
            ["🏠 Home", "💳 Pricing"]
        )

    # Premium teaser
    if user_role not in ["subscriber", "admin", "superadmin"]:
        st.sidebar.markdown("---")
        st.sidebar.markdown("""
        ### 💎 Premium Benefits

        ✅ All 4 apps - full access
        ✅ Unlimited usage
        ✅ Future apps included
        ✅ Priority support

        **$49/mo** - Lock rate forever
        """)

    # Logout
    if user:
        st.sidebar.markdown("---")
        if st.sidebar.button("Logout", use_container_width=True):
            if auth_manager:
                auth_manager.logout()
            st.rerun()

    return page

def render_home_page(auth_manager: AuthManager, subscription_manager: SubscriptionManager, user_role: str):
    """Render the revenue-optimized home page."""

    # HERO SECTION
    st.markdown("""
    <div class="hero-multiverse">
        <h1 class="hero-title">Your Personal AI Multiverse</h1>
        <h2 class="hero-subtitle">The Last Platform You'll Ever Need.<br>Because It Builds The Others.</h2>
        <p class="hero-description">
            <strong>Revolutionary Apps Today.</strong> Infinite Possibilities Tomorrow.<br>
            Control your neurochemistry • Access 118 billion humans • Project infinite identities • Automate your life
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🚀 Explore Free", type="primary", use_container_width=True, key="hero_free"):
            st.info("👆 Create account in sidebar to start exploring")
    with col2:
        if st.button("💎 Unlock Everything", use_container_width=True, key="hero_premium"):
            st.session_state["selected_page"] = "💳 Pricing"
            st.rerun()
    with col3:
        st.markdown("**30-day guarantee**")

    # Early Access Urgency (only if not already premium)
    if user_role not in ["subscriber", "admin", "superadmin"]:
        st.markdown("""
        <div class="urgency-banner">
            🔥 EARLY ACCESS PRICING: Lock in $49/mo forever • Regular price $79/mo
        </div>
        """, unsafe_allow_html=True)

    # Get user access
    config = load_config()
    if not config:
        return

    status = get_app_status()
    if not status:
        st.warning("Checking app status...")
        return

    user_email = auth_manager.get_current_user().get("email") if auth_manager and auth_manager.get_current_user() else None
    user_app_access = []

    if user_email and subscription_manager:
        try:
            user_app_access = subscription_manager.get_app_access_list(user_email)
        except Exception as e:
            logger.error(f"Error getting user subscriptions: {e}")

    has_premium = '*' in user_app_access or user_role in ["admin", "superadmin"]

    # WORKING APPS SHOWCASE
    st.markdown("---")
    st.markdown("## Start Your Journey: Revolutionary Apps")
    st.markdown("*Algorithmic expansion coming soon to Premium members*")
    st.markdown("")

    # Define the 4 working apps in priority order
    featured_apps = [
        ("agentic_social_server", "🧠", "Agentic Social Server", "Neurochemical Content Control",
         "Don't just consume content. Engineer your consciousness.",
         "The world's first social platform where YOU control the neurochemical mix.",
         ["**Neurochemical optimization:** Control dopamine, norepinephrine, acetylcholine, serotonin",
          "**147 AI personas:** Pre-trained agents create content optimized for your brain",
          "**Gamma-burst insights:** Engineered 'aha!' moments through neuroscience"],
         ["3 AI personas, view-only feed"],
         ["All 147 personas", "Custom persona training", "Full neurochemical control", "Bulk scheduling"]),

        ("ai_resume_builder", "👤", "AI Resume Builder", "Quantum Professional Identity",
         "Your career isn't linear. Why should your resume be?",
         "Project infinite versions of yourself. Share professional narratives as teams.",
         ["**Narrative quantum field:** Multiple professional identities simultaneously",
          "**Team resume sharing:** Collaborate on group professional narratives",
          "**AI-powered generation:** Trained on 10,000+ successful resumes"],
         ["1 basic resume"],
         ["Unlimited resumes", "AI generation", "Team collaboration", "ATS optimization"]),

        ("trillionsofpeople", "🌍", "TrillionsOfPeople", "All 118 Billion Humans",
         "Human history isn't the past. It's 118 billion consultants.",
         "AI personas of every human who ever lived. For scenario analysis, worldbuilding, research.",
         ["**118 billion personas:** Everyone from 70,000 BCE to present",
          "**Scenario analysis:** Run historical what-ifs with real personas",
          "**API access:** Integrate human history into your workflows"],
         ["Browse 100 sample personas"],
         ["All 118,000,000,000 personas", "Advanced search & filtering", "CSV/JSON export", "Full API access"]),

        ("personal_time_management", "⚡", "Daily Engine", "Life Automation Intelligence",
         "Your AI life operating system.",
         "Automate tasks, track habits, advance SaaS projects, optimize your time.",
         ["**AI priority scoring:** Knows what matters most",
          "**Predictive scheduling:** Optimizes your day automatically",
          "**SaaS advancement:** Track startup/project milestones"],
         ["Basic task management", "Habit tracking"],
         ["AI optimization", "Integrations (Google Cal, Notion, Slack)", "SaaS project tracking"])
    ]

    organizations = config.get("organizations", {})
    app_statuses = status.get("organizations", {})

    for app_id, icon, name, subtitle, tagline, description, features, free_features, premium_features in featured_apps:
        # Find the app in config
        app_config = None
        app_status_data = None

        for org_id, org_data in organizations.items():
            if app_id in org_data.get("apps", {}):
                app_config = org_data["apps"][app_id]
                app_status_data = app_statuses.get(org_id, {}).get("apps", {}).get(app_id, {})
                org_key = org_id
                break

        if not app_config or not app_config.get("public_visible", False):
            continue

        # Render app card
        with st.expander(f"{icon} **{name}** - {subtitle}", expanded=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"### {tagline}")
                st.markdown(f"{description}")
                st.markdown("")

                for feature in features:
                    st.markdown(f"- {feature}")

                st.markdown("")
                st.markdown("**What you get FREE:**")
                for feat in free_features:
                    st.markdown(f"✅ {feat}")

                if not has_premium:
                    st.markdown("")
                    st.markdown("**Unlock with Premium:**")
                    for feat in premium_features:
                        st.markdown(f"🔒 {feat}")

            with col2:
                # Status
                is_running = app_status_data.get("running", False) if app_status_data else False
                health = app_status_data.get("health_status", "unknown") if app_status_data else "unknown"

                if is_running and health == "healthy":
                    st.success("✅ Online")
                elif is_running:
                    st.warning("⚠️ Starting")
                else:
                    st.error("❌ Offline")

                st.markdown("---")

                # Access control
                has_access = has_premium or app_config.get("subscription_tier") == "free"

                if has_access and is_running:
                    port = app_config.get("port")
                    if st.button(f"🚀 Launch {name}", key=f"launch_{app_id}", type="primary", use_container_width=True):
                        session_id = st.session_state.get('shared_session_id', '')
                        url = f"http://localhost:{port}"
                        if session_id:
                            url += f"?session_id={session_id}"
                        st.markdown(f'<meta http-equiv="refresh" content="0; url={url}" />', unsafe_allow_html=True)
                        st.success(f"Opening {name}...")
                elif has_access and not is_running:
                    st.warning("⏳ Starting up...")
                else:
                    st.markdown("""
                    <div class="premium-lock">
                        🔒 Premium Features Locked<br>
                        <small>Upgrade to unlock full access</small>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("⬆️ Upgrade to Premium", key=f"upgrade_{app_id}", type="primary", use_container_width=True):
                        st.session_state["selected_page"] = "💳 Pricing"
                        st.rerun()

    # FUTURE APPS SECTION
    st.markdown("---")
    st.markdown("## Coming Soon to Premium Members")

    # Future apps with stepped gradient colors
    future_apps = [
        ("🎨 Collectiverse", "Universe Creation Engine", "Build infinite universes from your collections. AGI-proof your collecting.", "Q2 2026", "linear-gradient(135deg, #8B5CF6, #A78BFA)"),
        ("📝 ArXiv Paper Writer", "Scientific Reality Generator", "Transform ideas into peer-reviewed publications with AI research assistance.", "Q3 2026", "linear-gradient(135deg, #A78BFA, #C4B5FD)"),
        ("🤖 Algorithmic App Generator", "The Meta-Platform", "Apps that create apps. New tools generated based on your usage patterns.", "Q4 2026", "linear-gradient(135deg, #C4B5FD, #DDD6FE)")
    ]

    for icon_name, subtitle, description, timeline, gradient in future_apps:
        st.markdown(f"""
        <div class="coming-soon" style="background: {gradient};">
            <h3>{icon_name} - {subtitle}</h3>
            <p>{description}</p>
            <p><strong>Status:</strong> Premium early access {timeline}</p>
        </div>
        """, unsafe_allow_html=True)

    st.info("💡 **Premium members get early access to all new apps. Free users wait 6 months.**")

    # SOCIAL PROOF PLACEHOLDER (honest - no fake data)
    st.markdown("---")
    st.markdown("## What Users Say")

    st.markdown("""
    <div class="social-proof-placeholder">
        <h3>📢 Coming Soon: User Testimonials</h3>
        <p>We're collecting feedback from our early users.<br>
        Real testimonials will appear here as we grow.</p>
        <p><em>Be one of the first to share your experience!</em></p>
    </div>
    """, unsafe_allow_html=True)

    # FINAL CTA
    st.markdown("---")
    st.markdown("## Ready to Enter Your Personal Multiverse?")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Exploring Free", type="primary", use_container_width=True, key="final_cta"):
            st.info("👆 Create account in sidebar to begin")
        st.markdown("<p style='text-align: center; margin-top: 16px;'>💎 Upgrade anytime • 30-day money-back guarantee</p>", unsafe_allow_html=True)

def render_pricing_page(subscription_manager: SubscriptionManager, auth_manager: AuthManager):
    """Render the conversion-optimized pricing page."""

    st.markdown("# Choose Your Reality")
    st.markdown("## 🔥 Early Access Pricing - Lock In Your Rate Forever")

    # Guarantee
    st.markdown("""
    <div class="guarantee">
        🛡️ <strong>30-Day Money-Back Guarantee</strong> • Cancel Anytime • No Long-Term Contracts
    </div>
    """, unsafe_allow_html=True)

    # Get user info
    user = auth_manager.get_current_user() if auth_manager else None
    user_email = user.get("email") if user else None

    # Show current subscriptions if any
    if user_email and subscription_manager:
        try:
            user_subs = subscription_manager.get_user_subscriptions(user_email)
            if user_subs:
                st.success(f"✅ You have {len(user_subs)} active subscription(s)")
                with st.expander("View My Subscriptions"):
                    for sub in user_subs:
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.write(f"**{sub['type'].replace('_', ' ').title()}**")
                        with col2:
                            end_date = datetime.fromisoformat(sub['current_period_end'])
                            st.caption(f"Renews: {end_date.strftime('%Y-%m-%d')}")
                        with col3:
                            st.write(f"*{sub['status']}*")
        except Exception as e:
            logger.error(f"Error loading subscriptions: {e}")

    st.markdown("---")

    # PRICING COMPARISON
    st.markdown("## Choose Your Plan")

    col1, col2, col3 = st.columns(3)

    # FREE TIER
    with col1:
        st.markdown('<div class="pricing-card">', unsafe_allow_html=True)
        st.markdown("### Free Explorer")
        st.markdown('<div class="price-amount">$0</div>', unsafe_allow_html=True)
        st.markdown("**Forever free**")
        st.markdown("---")
        st.markdown("✅ Apps (limited features)")
        st.markdown("✅ Daily Engine basics")
        st.markdown("✅ 3 AI personas (Social)")
        st.markdown("✅ 100 sample personas (Trillions)")
        st.markdown("✅ 1 resume (AI Builder)")
        st.markdown("❌ Future apps (wait 6 months)")
        st.markdown("❌ Priority support")
        st.markdown("")
        if st.button("Stay Free", key="free_tier", use_container_width=True):
            st.info("You're on the free plan. Explore and upgrade when ready!")
        st.markdown('</div>', unsafe_allow_html=True)

    # PREMIUM TIER (HIGHLIGHTED)
    with col2:
        st.markdown('<div class="pricing-card pricing-card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="pricing-badge">⭐ BEST VALUE</div>', unsafe_allow_html=True)
        st.markdown("### Premium Architect")
        st.markdown('<div class="price-amount">$49<small>/mo</small></div>', unsafe_allow_html=True)
        st.markdown("~~$79/mo~~ **Early access pricing**")
        st.markdown("---")
        st.markdown("✅ **All apps - full access**")
        st.markdown("✅ Unlimited everything")
        st.markdown("✅ 147 AI personas (Social)")
        st.markdown("✅ 118 billion personas (Trillions)")
        st.markdown("✅ Unlimited resumes (AI Builder)")
        st.markdown("✅ **Future apps - early access**")
        st.markdown("✅ Priority email support")
        st.markdown("✅ **Rate locked forever**")
        st.markdown("")

        if user_email and subscription_manager:
            tiers = subscription_manager.list_all_tiers()
            all_access = tiers.get("all_access", {})
            price_id = all_access.get('stripe_price_id')

            if price_id:
                if st.button("🚀 UNLOCK EVERYTHING", key="premium_tier", type="primary", use_container_width=True):
                    try:
                        checkout_url = subscription_manager.create_checkout_session(
                            user_email=user_email,
                            price_id=price_id,
                            app_id=None
                        )
                        st.markdown(f'<meta http-equiv="refresh" content="0; url={checkout_url}" />', unsafe_allow_html=True)
                        st.success("Redirecting to checkout...")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.button("Coming Soon", key="premium_soon", disabled=True, use_container_width=True)
        else:
            if st.button("Login to Subscribe", key="premium_login", type="primary", use_container_width=True):
                st.info("👆 Please login in sidebar to subscribe")

        st.markdown('</div>', unsafe_allow_html=True)

    # ENTERPRISE TIER
    with col3:
        st.markdown('<div class="pricing-card">', unsafe_allow_html=True)
        st.markdown("### Enterprise")
        st.markdown('<div class="price-amount" style="font-size: 2.5rem;">Custom</div>', unsafe_allow_html=True)
        st.markdown("**Contact for pricing**")
        st.markdown("---")
        st.markdown("✅ Everything in Premium")
        st.markdown("✅ White-label multiverse")
        st.markdown("✅ Custom app generation")
        st.markdown("✅ Team accounts")
        st.markdown("✅ Dedicated support")
        st.markdown("✅ SLA guarantees")
        st.markdown("✅ Custom integrations")
        st.markdown("")
        if st.button("Contact Sales", key="enterprise", use_container_width=True):
            st.info("📧 Email: fred@xtuff.ai for enterprise inquiries")
        st.markdown('</div>', unsafe_allow_html=True)

    # VALUE PROPOSITION
    st.markdown("---")
    st.markdown("## Why Premium is a No-Brainer")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 💰 The Math

        **Buying similar tools separately:**
        - Social media + AI: $50/mo
        - Resume tools: $30/mo
        - Research databases: $40/mo
        - Productivity: $20/mo

        **Total:** $140/month

        **xtuff.ai Premium:** $49/month

        **YOU SAVE:** $91/month = **$1,092/year**
        """)

    with col2:
        st.markdown("""
        ### 🚀 What You Get

        **Available Now:**
        - Agentic Social (neurochemical control)
        - AI Resume Builder (infinite identities)
        - TrillionsOfPeople (118B personas)
        - Daily Engine (life automation)

        **Coming in 2026:**
        - Collectiverse (universe creation)
        - ArXiv Writer (scientific publishing)
        - Algorithmic apps (auto-generated tools)
        """)

    # FAQ
    st.markdown("---")
    st.markdown("## Frequently Asked Questions")

    with st.expander("❓ Why should I pay when some apps are free?"):
        st.markdown("""
        Free tier is designed to let you test the waters. Premium unlocks the real power:
        - **Unlimited usage** (no artificial limits)
        - **Full features** (AI optimization, advanced analytics)
        - **Future apps** (early access to new tools as they're built)
        - **Priority support** (faster response times)

        Think of free as a demo, premium as the full experience.
        """)

    with st.expander("❓ Can I really cancel anytime?"):
        st.markdown("""
        **Yes!** Absolutely no lock-in:
        - Cancel with one click in your account
        - No retention dark patterns
        - Keep your data even after canceling
        - 30-day money-back guarantee (no questions asked)
        """)

    with st.expander("❓ What's this 'algorithmic app generation' thing?"):
        st.markdown("""
        We're building a **meta-platform** - a platform that creates platforms.

        As you use xtuff.ai, our algorithms identify patterns and opportunities for new tools.
        Premium members get early access to these algorithmically-generated apps.

        **Example:** If we notice users struggling with a specific workflow, our system
        can generate a new micro-app to solve it. You get it first.
        """)

    with st.expander("❓ Is my data secure?"):
        st.markdown("""
        **Yes.** We take security seriously:
        - 🔒 256-bit encryption for all data
        - 🔐 Secure authentication system
        - 🛡️ Regular security audits
        - 📋 GDPR compliant
        - 🗄️ Your data stays yours (export anytime)
        """)

    with st.expander("❓ Will the price really stay $49 forever?"):
        st.markdown("""
        **Grandfathered pricing guarantee:**

        If you subscribe now at $49/mo, your rate is **locked forever**.

        Even if we raise prices to $79/mo (or higher) for new members,
        you keep paying $49/mo as long as you remain subscribed.

        This is our way of rewarding early believers.
        """)

def render_management_page():
    """Admin management page."""
    st.title("🔧 Application Management")
    st.info("Management interface - see original main.py for full implementation")

def render_monitoring_page():
    """Admin monitoring page."""
    st.title("📊 Application Monitoring")
    st.info("Monitoring interface - see original main.py for full implementation")

def render_settings_page():
    """Admin settings page."""
    st.title("⚙️ Settings")
    st.info("Settings interface - see original main.py for full implementation")

def main():
    """Main application entry point."""
    # Initialize managers
    auth_manager, subscription_manager = get_managers()

    # Auto-start apps on first launch
    if "apps_started" not in st.session_state:
        st.session_state["apps_started"] = True
        try:
            manager = ProcessManager()
            manager.initialize_processes()
            manager.start_all()
            logger.info("Auto-started all applications")
        except Exception as e:
            logger.error(f"Error auto-starting applications: {e}")

    # Render login widget
    if auth_manager:
        auth_manager.render_login_widget(location="sidebar")

    # Get user role
    user_role = auth_manager.get_user_role() if auth_manager else "anonymous"

    # Render sidebar and get selected page
    page = render_sidebar(auth_manager, user_role)

    # Override page if set in session state
    if "selected_page" in st.session_state:
        page = st.session_state["selected_page"]
        del st.session_state["selected_page"]

    # Route to appropriate page
    if page == "🏠 Home":
        render_home_page(auth_manager, subscription_manager, user_role)

    elif page == "💳 Pricing":
        render_pricing_page(subscription_manager, auth_manager)

    elif page == "🔧 Management":
        if user_role in ["admin", "superadmin"]:
            render_management_page()
        else:
            st.error("Access denied. Administrator privileges required.")

    elif page == "📊 Monitoring":
        if user_role in ["admin", "superadmin"]:
            render_monitoring_page()
        else:
            st.error("Access denied. Administrator privileges required.")

    elif page == "⚙️ Settings":
        if user_role in ["admin", "superadmin"]:
            render_settings_page()
        else:
            st.error("Access denied. Administrator privileges required.")

if __name__ == "__main__":
    main()
