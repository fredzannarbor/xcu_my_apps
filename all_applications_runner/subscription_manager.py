#!/usr/bin/env python3
"""
Subscription Manager for Unified App Runner

Handles Stripe integration for subscription management and payment processing.
"""

import os
import logging
import stripe
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SubscriptionManager:
    """Manages user subscriptions and Stripe integration."""

    # Base price tier definitions per app
    # Individual app pricing: $9 for basic, $19 for premium
    # All-access bundle: 70% of total premium price for all apps
    PRICE_TIERS = {
        "free": {
            "name": "Free",
            "price": 0,
            "description": "Free access to selected apps"
        },
        "basic": {
            "name": "Basic",
            "price": 9.00,
            "description": "$9/month per app - Basic access",
            "stripe_price_id": os.getenv("STRIPE_PRICE_ID")
        },
        "premium": {
            "name": "Premium",
            "price": 19.00,
            "description": "$19/month per app - Premium features",
            "stripe_price_id": os.getenv("STRIPE_PRICE_ID_2")
        },
        "all_access": {
            "name": "All Access Bundle",
            "price": None,  # Calculated dynamically as 70% of total premium
            "description": "Unlimited access to all apps",
            "discount_percentage": 30,  # 30% off total premium price
            "stripe_price_id": os.getenv("STRIPE_PREMIUM_ALL_ACCESS_PRICE_ID")
        }
    }

    def __init__(self, apps_config_path: str = "apps_config.json"):
        """Initialize the subscription manager with Stripe credentials."""
        self.stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")
        self.stripe_publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        self.apps_config_path = Path(apps_config_path)

        if not self.stripe_secret_key:
            logger.warning("Stripe secret key not found in environment variables")
            raise ValueError("STRIPE_SECRET_KEY not configured")

        stripe.api_key = self.stripe_secret_key

        # Calculate all-access price based on apps config
        self._calculate_all_access_price()

        logger.info("Subscription manager initialized with Stripe integration")

    def _calculate_all_access_price(self):
        """Calculate all-access bundle price as 70% of total premium apps."""
        try:
            import json
            with open(self.apps_config_path, 'r') as f:
                config = json.load(f)

            # Count premium-eligible apps (non-free tier apps)
            premium_app_count = 0
            for org_id, org_config in config.get("organizations", {}).items():
                for app_id, app_config in org_config.get("apps", {}).items():
                    tier = app_config.get("subscription_tier", "free")
                    if tier in ["basic", "premium"]:
                        premium_app_count += 1

            # Calculate: Total premium price * 0.70
            total_premium_price = premium_app_count * self.PRICE_TIERS["premium"]["price"]
            all_access_price = total_premium_price * 0.70

            # Update the all-access tier price
            self.PRICE_TIERS["all_access"]["price"] = round(all_access_price, 2)
            self.PRICE_TIERS["all_access"]["description"] = (
                f"Unlimited access to all apps - Save 30%! "
                f"({premium_app_count} apps × $19 = ${total_premium_price:.0f}, "
                f"you pay ${all_access_price:.0f})"
            )

            logger.info(f"Calculated all-access price: ${all_access_price:.2f} for {premium_app_count} apps")

        except Exception as e:
            logger.warning(f"Could not calculate all-access price: {e}")
            # Default fallback
            self.PRICE_TIERS["all_access"]["price"] = 49.00
            self.PRICE_TIERS["all_access"]["description"] = "Unlimited access to all apps - Save 30%!"

    def check_user_subscription(self, user_email: str, app_id: str) -> bool:
        """
        Check if a user has an active subscription for a specific app.

        Args:
            user_email: Email address of the user
            app_id: Application identifier

        Returns:
            bool: True if user has access, False otherwise
        """
        try:
            # Search for customer by email
            customers = stripe.Customer.list(email=user_email, limit=1)

            if not customers.data:
                logger.info(f"No customer found for email: {user_email}")
                return False

            customer = customers.data[0]

            # Get active subscriptions
            subscriptions = stripe.Subscription.list(
                customer=customer.id,
                status='active',
                limit=10
            )

            if not subscriptions.data:
                logger.info(f"No active subscriptions for user: {user_email}")
                return False

            # Check if any subscription includes the app
            for subscription in subscriptions.data:
                metadata = subscription.metadata

                # Check if subscription is all-access or includes specific app
                if metadata.get('type') == 'all_access':
                    return True

                if metadata.get('app_id') == app_id:
                    return True

            logger.info(f"User {user_email} does not have subscription for app: {app_id}")
            return False

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error checking subscription: {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            return False

    def create_checkout_session(
        self,
        user_email: str,
        price_id: str,
        app_id: Optional[str] = None,
        success_url: str = "http://localhost:8500?session_id={CHECKOUT_SESSION_ID}",
        cancel_url: str = "http://localhost:8500"
    ) -> str:
        """
        Create a Stripe Checkout session for subscription purchase.

        Args:
            user_email: Email address of the user
            price_id: Stripe price ID
            app_id: Optional app identifier for single-app subscriptions
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment

        Returns:
            str: Checkout session URL
        """
        try:
            # Create or retrieve customer
            customers = stripe.Customer.list(email=user_email, limit=1)

            if customers.data:
                customer = customers.data[0]
                logger.info(f"Using existing customer: {customer.id}")
            else:
                customer = stripe.Customer.create(email=user_email)
                logger.info(f"Created new customer: {customer.id}")

            # Prepare metadata
            metadata = {
                "user_email": user_email,
                "created_at": datetime.now().isoformat()
            }

            if app_id:
                metadata["app_id"] = app_id
                metadata["type"] = "single_app"
            else:
                metadata["type"] = "all_access"

            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
                subscription_data={
                    'metadata': metadata
                }
            )

            logger.info(f"Created checkout session for {user_email}: {checkout_session.id}")
            return checkout_session.url

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            raise

    def get_user_subscriptions(self, user_email: str) -> List[Dict[str, Any]]:
        """
        Get all active subscriptions for a user.

        Args:
            user_email: Email address of the user

        Returns:
            List of subscription dictionaries with app details
        """
        try:
            # Search for customer by email
            customers = stripe.Customer.list(email=user_email, limit=1)

            if not customers.data:
                logger.info(f"No customer found for email: {user_email}")
                return []

            customer = customers.data[0]

            # Get active subscriptions
            subscriptions = stripe.Subscription.list(
                customer=customer.id,
                status='active',
                limit=100
            )

            user_subs = []

            for subscription in subscriptions.data:
                metadata = subscription.metadata

                sub_info = {
                    "subscription_id": subscription.id,
                    "status": subscription.status,
                    "created": datetime.fromtimestamp(subscription.created).isoformat(),
                    "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
                    "type": metadata.get('type', 'unknown'),
                    "app_id": metadata.get('app_id'),
                    "price_id": subscription.items.data[0].price.id if subscription.items.data else None
                }

                user_subs.append(sub_info)

            logger.info(f"Found {len(user_subs)} active subscriptions for {user_email}")
            return user_subs

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting subscriptions: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting subscriptions: {e}")
            return []

    def cancel_subscription(self, subscription_id: str) -> bool:
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            logger.info(f"Cancelled subscription: {subscription_id}")
            return subscription.status == 'canceled'

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {e}")
            return False
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            return False

    def get_app_access_list(self, user_email: str) -> List[str]:
        """
        Get list of app IDs the user has access to.

        Args:
            user_email: Email address of the user

        Returns:
            List of app IDs user can access
        """
        subscriptions = self.get_user_subscriptions(user_email)
        app_ids = []

        for sub in subscriptions:
            if sub['type'] == 'all_access':
                # Return special marker for all-access
                return ['*']  # Wildcard for all apps

            app_id = sub.get('app_id')
            if app_id and app_id not in app_ids:
                app_ids.append(app_id)

        return app_ids

    def get_tier_info(self, tier_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a pricing tier.

        Args:
            tier_name: Name of the tier (free, basic, premium, all_access)

        Returns:
            Dictionary with tier information or None
        """
        return self.PRICE_TIERS.get(tier_name)

    def list_all_tiers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available pricing tiers.

        Returns:
            Dictionary of all pricing tiers
        """
        return self.PRICE_TIERS


def get_subscription_manager() -> SubscriptionManager:
    """Get a configured SubscriptionManager instance."""
    try:
        return SubscriptionManager()
    except ValueError as e:
        logger.error(f"Failed to initialize subscription manager: {e}")
        raise


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        manager = get_subscription_manager()

        # Display available tiers
        print("\nAvailable Pricing Tiers:")
        print("=" * 60)
        for tier_name, tier_info in manager.list_all_tiers().items():
            print(f"\n{tier_info['name']} (${tier_info['price']}/month)")
            print(f"  {tier_info['description']}")
            if tier_info.get('discount_percentage'):
                print(f"  Discount: {tier_info['discount_percentage']}%")

        print("\n" + "=" * 60)
        print("Subscription manager initialized successfully")

    except Exception as e:
        print(f"Error: {e}")
