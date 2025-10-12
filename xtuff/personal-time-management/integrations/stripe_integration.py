#!/usr/bin/env python3
"""
Stripe Integration for Daily Engine
Handles subscription management and payments
"""

import streamlit as st
import json
from datetime import datetime
from config.settings import config

class StripeIntegration:
    def __init__(self):
        self.enabled = config.is_feature_enabled('stripe_subscription')
        self.stripe_config = config.get_feature_config('stripe_subscription')
    
    def render_subscription_ui(self):
        """Render subscription management UI"""
        if not self.enabled:
            st.info("💳 Stripe subscription is not enabled. Enable it in Settings to access premium features.")
            return False
        
        st.subheader("💳 Subscription Management")
        
        # Mock subscription status (replace with actual Stripe integration)
        subscription_status = st.session_state.get('subscription_status', 'inactive')
        
        if subscription_status == 'active':
            st.success("✅ Premium subscription active")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Plan**: Premium (${self.stripe_config.get('monthly_price', 29.99)}/month)")
                st.write("**Status**: Active")
                st.write("**Next billing**: 2025-08-28")
            with col2:
                if st.button("🚫 Cancel Subscription"):
                    st.session_state.subscription_status = 'cancelled'
                    st.rerun()
        else:
            st.warning("⚠️ Free tier - Limited features available")
            st.write(f"**Upgrade to Premium**: ${self.stripe_config.get('monthly_price', 29.99)}/month")
            
            st.write("**Premium Features:**")
            st.write("- Unlimited project tracking")
            st.write("- Advanced analytics and insights")
            st.write("- iOS notifications")
            st.write("- Automated reporting")
            st.write("- AI-powered recommendations")
            st.write("- Priority support")
            
            if st.button("🚀 Subscribe to Premium"):
                # Mock subscription activation (replace with actual Stripe checkout)
                st.session_state.subscription_status = 'active'
                st.success("🎉 Welcome to Premium! Subscription activated.")
                st.rerun()
        
        return subscription_status == 'active'
    
    def check_feature_access(self, feature: str) -> bool:
        """Check if user has access to a premium feature"""
        if not self.enabled:
            return True  # If Stripe is disabled, allow all features
        
        subscription_status = st.session_state.get('subscription_status', 'inactive')
        
        # Define premium features
        premium_features = [
            'advanced_analytics',
            'ios_notifications', 
            'automation',
            'ai_insights',
            'unlimited_projects'
        ]
        
        if feature in premium_features:
            return subscription_status == 'active'
        
        return True  # Free features
    
    def render_paywall(self, feature_name: str):
        """Render paywall for premium features"""
        st.warning(f"🔒 {feature_name} is a Premium feature")
        st.write("Upgrade to Premium to unlock this feature and many more!")
        
        if st.button(f"🚀 Upgrade for {feature_name}"):
            st.session_state.subscription_status = 'active'
            st.success("🎉 Premium activated!")
            st.rerun()

# Global stripe instance
stripe_integration = StripeIntegration()