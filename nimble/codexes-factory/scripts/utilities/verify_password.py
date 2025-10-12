#!/usr/bin/env python3
"""
Script to verify admin password for Streamlit authentication
"""

import bcrypt

# The hashed password from config.yaml for admin user
admin_hash = "$2b$12$rR6JaAzVByA0V/lBSFjxCeEk7Lau73jJmGtHiQlwCV1sfvXn3HW9a"

# Test passwords
test_passwords = ["hotdogtoy", "admin", "password", "123456"]

print("Testing passwords for admin user...")
print("=" * 50)

for password in test_passwords:
    if bcrypt.checkpw(password.encode('utf-8'), admin_hash.encode('utf-8')):
        print(f"✅ MATCH: Password is '{password}'")
    else:
        print(f"❌ No match: '{password}'")

print("=" * 50)