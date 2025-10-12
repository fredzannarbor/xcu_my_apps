#!/usr/bin/env python3
"""
Test script to verify authentication integration with central auth system.
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, '/Users/fred/xcu_my_apps')
sys.path.insert(0, '/Users/fred/xcu_my_apps/all_applications_runner')

import yaml
from yaml.loader import SafeLoader

def test_config():
    """Test that the config file has the correct test accounts."""
    config_path = Path('/Users/fred/xcu_my_apps/all_applications_runner/resources/yaml/config.yaml')

    with open(config_path, 'r') as file:
        config = yaml.load(file, Loader=SafeLoader)

    usernames = config['credentials']['usernames']

    print("=" * 80)
    print("TEST USER ACCOUNTS IN CONFIG")
    print("=" * 80)
    print()

    test_accounts = {
        'admin': {
            'expected_role': 'admin',
            'expected_tier': 'premium',
            'expected_password': 'hotdogtoy (plain text)'
        },
        'johndoe': {
            'expected_role': 'user',
            'expected_tier': 'free',
            'expected_password': 'footballfoot (hashed)'
        },
        'basicbob': {
            'expected_role': 'user',
            'expected_tier': 'basic',
            'expected_password': 'basicbob (hashed)'
        },
        'priscilla': {
            'expected_role': 'user',
            'expected_tier': 'premium',
            'expected_password': 'premiumprice (hashed)'
        },
        'xtraxtuff': {
            'expected_role': 'user',
            'expected_tier': 'basic',
            'expected_password': 'xtraonly (hashed)',
            'expected_access': ['xtuff_ai']
        }
    }

    for username, expected in test_accounts.items():
        if username in usernames:
            user = usernames[username]
            print(f"✅ {username}:")
            print(f"   Name: {user.get('name')}")
            print(f"   Email: {user.get('email')}")
            print(f"   Role: {user.get('role')} (expected: {expected['expected_role']})")
            print(f"   Tier: {user.get('subscription_tier')} (expected: {expected['expected_tier']})")
            if 'expected_access' in expected:
                print(f"   App Access: {user.get('app_access')} (expected: {expected['expected_access']})")
            print(f"   Password: {'hashed' if user.get('password', '').startswith('$2b$') else 'plain'}")
            print()

            # Verify expectations
            if user.get('role') != expected['expected_role']:
                print(f"   ⚠️  WARNING: Role mismatch!")
            if user.get('subscription_tier') != expected['expected_tier']:
                print(f"   ⚠️  WARNING: Tier mismatch!")
        else:
            print(f"❌ {username}: NOT FOUND IN CONFIG")
            print()

    print("=" * 80)
    print("SUBSCRIPTION FEATURES FROM apps_config.json")
    print("=" * 80)
    print()

    import json
    apps_config_path = Path('/Users/fred/xcu_my_apps/all_applications_runner/apps_config.json')
    with open(apps_config_path, 'r') as f:
        apps_config = json.load(f)

    ai_resume = apps_config['organizations']['xtuff_ai']['apps']['ai_resume_builder']
    features = ai_resume.get('subscription_features', {})

    print("AI Resume Builder Features by Tier:")
    print()
    for tier, feature_list in features.items():
        print(f"{tier.upper()}:")
        for feature in feature_list:
            print(f"  - {feature}")
        print()

if __name__ == "__main__":
    try:
        test_config()
        print("\n✅ Configuration test completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
