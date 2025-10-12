#!/usr/bin/env python3
"""
Stripe Checkout Testing Script for xtuff.ai V2

This script walks you through testing the complete $49/mo Premium checkout flow.
Run this to verify Stripe integration is working correctly.

Usage:
    python test_stripe_checkout.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_step(number, text):
    print(f"{Colors.OKBLUE}{Colors.BOLD}STEP {number}:{Colors.ENDC} {text}")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def wait_for_enter(prompt="Press ENTER to continue..."):
    input(f"\n{Colors.BOLD}{prompt}{Colors.ENDC}")

def check_env_variables():
    """Check that required Stripe environment variables are set."""
    print_step(1, "Checking Environment Configuration")

    required_vars = [
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "STRIPE_PREMIUM_ALL_ACCESS_PRICE_ID"
    ]

    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()

    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask the value for security
            if "KEY" in var:
                masked = value[:10] + "..." + value[-4:]
            else:
                masked = value
            print_success(f"{var} = {masked}")
        else:
            missing.append(var)
            print_error(f"{var} is NOT SET")

    if missing:
        print_error(f"\nMissing required environment variables: {', '.join(missing)}")
        print_info("Please check your .env file and ensure all Stripe variables are set.")
        return False

    print_success("\nAll required environment variables are set!")
    return True

def check_stripe_connection():
    """Verify we can connect to Stripe API."""
    print_step(2, "Testing Stripe API Connection")

    try:
        import stripe
        from dotenv import load_dotenv
        load_dotenv()

        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

        # Try to retrieve the price
        price_id = os.getenv("STRIPE_PREMIUM_ALL_ACCESS_PRICE_ID")
        price = stripe.Price.retrieve(price_id)

        print_success(f"Connected to Stripe API successfully!")
        print_info(f"Product: {price.product}")
        print_info(f"Amount: ${price.unit_amount/100:.2f} {price.currency.upper()}")
        print_info(f"Interval: {price.recurring.interval}")
        print_info(f"Price ID: {price.id}")

        return True

    except stripe.error.StripeError as e:
        print_error(f"Stripe API Error: {e}")
        return False
    except Exception as e:
        print_error(f"Error connecting to Stripe: {e}")
        return False

def generate_test_credentials():
    """Generate unique test user credentials."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return {
        "email": f"test+stripe{timestamp}@example.com",
        "name": "Test User Premium",
        "password": "TestPassword123!"
    }

def display_manual_test_guide():
    """Display manual testing instructions."""
    print_step(3, "Manual Testing Workflow")

    creds = generate_test_credentials()

    print("\n" + Colors.BOLD + "🎯 TEST USER CREDENTIALS:" + Colors.ENDC)
    print(f"  Email:    {Colors.OKGREEN}{creds['email']}{Colors.ENDC}")
    print(f"  Name:     {Colors.OKGREEN}{creds['name']}{Colors.ENDC}")
    print(f"  Password: {Colors.OKGREEN}{creds['password']}{Colors.ENDC}")

    print("\n" + Colors.BOLD + "📋 TESTING CHECKLIST:" + Colors.ENDC)

    steps = [
        ("Navigate to Application", "Open http://localhost:8500 in your browser"),
        ("Create Test Account", f"Sign up with email: {creds['email']}"),
        ("Explore Free Features", "Browse the 4 featured apps and note free tier limits"),
        ("Hit Paywalls", "Verify '🔒 Unlock with Premium' messages appear"),
        ("View Pricing Page", "Click '💎 Go Premium' or navigate to Pricing"),
        ("Review Premium Tier", "Confirm $49/mo pricing and all features listed"),
        ("Start Checkout", "Click '🚀 UNLOCK EVERYTHING' button"),
        ("Complete Payment", "Use test card: 4242 4242 4242 4242, exp: 12/30, CVC: 123"),
        ("Verify Redirect", "Confirm redirect back to app with session_id in URL"),
        ("Check Premium Status", "Sidebar should show '💎 Premium Member'"),
        ("Test App Access", "All 4 apps should be unlocked (no more paywalls)"),
        ("View Subscription", "Pricing page should show active subscription"),
        ("Verify in Stripe", "Check Stripe dashboard for new subscription"),
    ]

    for i, (title, description) in enumerate(steps, 1):
        print(f"\n  {Colors.BOLD}{i:2d}. {title}{Colors.ENDC}")
        print(f"      {description}")

    print("\n" + Colors.BOLD + "💳 STRIPE TEST CARDS:" + Colors.ENDC)
    print(f"  Success:             {Colors.OKGREEN}4242 4242 4242 4242{Colors.ENDC}")
    print(f"  Card Declined:       {Colors.FAIL}4000 0000 0000 0002{Colors.ENDC}")
    print(f"  Insufficient Funds:  {Colors.WARNING}4000 0000 0000 9995{Colors.ENDC}")

    print("\n" + Colors.BOLD + "🔗 USEFUL LINKS:" + Colors.ENDC)
    print(f"  App:              {Colors.OKCYAN}http://localhost:8500{Colors.ENDC}")
    print(f"  Stripe Dashboard: {Colors.OKCYAN}https://dashboard.stripe.com/test/dashboard{Colors.ENDC}")
    print(f"  Stripe Logs:      {Colors.OKCYAN}https://dashboard.stripe.com/test/logs{Colors.ENDC}")
    print(f"  Test Cards:       {Colors.OKCYAN}https://stripe.com/docs/testing{Colors.ENDC}")

def check_app_running():
    """Check if the Streamlit app is running."""
    print_step(4, "Checking Application Status")

    import requests

    try:
        response = requests.get("http://localhost:8500", timeout=5)
        if response.status_code == 200:
            print_success("Application is running at http://localhost:8500")
            return True
        else:
            print_warning(f"Application returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to http://localhost:8500")
        print_info("Start the app with: uv run streamlit run main.py --server.port=8500")
        return False
    except Exception as e:
        print_error(f"Error checking app status: {e}")
        return False

def run_integration_test():
    """Run automated integration tests if possible."""
    print_step(5, "Running Automated Checks")

    try:
        from subscription_manager import get_subscription_manager

        print_info("Testing subscription manager initialization...")
        manager = get_subscription_manager()

        # Test tier information
        tiers = manager.list_all_tiers()
        all_access = tiers.get("all_access", {})

        if all_access.get("stripe_price_id"):
            print_success(f"All-access tier configured with price ID: {all_access['stripe_price_id']}")
        else:
            print_error("All-access tier price ID not configured!")
            return False

        # Test price calculation
        if all_access.get("price"):
            print_success(f"All-access price calculated: ${all_access['price']:.2f}/mo")
        else:
            print_warning("All-access price not calculated (fallback: $49.00)")

        print_success("Subscription manager tests passed!")
        return True

    except Exception as e:
        print_error(f"Integration test failed: {e}")
        return False

def main():
    """Main test orchestration."""
    print_header("🧪 STRIPE CHECKOUT TESTING SUITE")
    print_header("xtuff.ai V2 Revenue - $49/mo Premium")

    print(f"{Colors.BOLD}This script will guide you through testing the Stripe checkout flow.{Colors.ENDC}")
    print(f"Make sure the Streamlit app is running before proceeding.\n")

    wait_for_enter("Press ENTER to start testing...")

    # Run checks
    all_passed = True

    # Check 1: Environment variables
    if not check_env_variables():
        all_passed = False
        print_error("\nEnvironment check failed. Please fix configuration before continuing.")
        sys.exit(1)

    wait_for_enter()

    # Check 2: Stripe connection
    if not check_stripe_connection():
        all_passed = False
        print_error("\nStripe connection failed. Please check your API keys.")
        sys.exit(1)

    wait_for_enter()

    # Check 3: App status
    app_running = check_app_running()
    if not app_running:
        print_warning("\nApp is not running. Start it before manual testing.")

    wait_for_enter()

    # Check 4: Integration tests
    if not run_integration_test():
        print_warning("\nSome integration tests failed, but you can still proceed with manual testing.")

    wait_for_enter()

    # Display manual test guide
    display_manual_test_guide()

    # Final summary
    print_header("✅ PRE-FLIGHT CHECKS COMPLETE")

    if all_passed and app_running:
        print_success("All automated checks passed!")
        print_success("You're ready to test the Stripe checkout flow.")
        print_info("\nFollow the manual testing checklist above.")
        print_info("Open http://localhost:8500 in your browser to begin.")
    else:
        print_warning("Some checks failed, but you can still attempt manual testing.")

    print("\n" + Colors.BOLD + "📖 Full Testing Guide:" + Colors.ENDC)
    print("   See STRIPE_TESTING_GUIDE.md for detailed instructions.\n")

    print(f"{Colors.BOLD}Happy Testing! 🚀{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Testing interrupted by user.{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}Unexpected error: {e}{Colors.ENDC}")
        sys.exit(1)
