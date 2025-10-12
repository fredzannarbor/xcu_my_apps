#!/usr/bin/env python3
"""
Test script to verify timeout configuration works
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from codexes.modules.crawlers import ZyteCrawler
except ModuleNotFoundError:
    from src.codexes.modules.crawlers import ZyteCrawler

def test_timeout_configuration():
    """Test that the timeout parameter is properly configured."""
    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("❌ ZYTE_API_KEY environment variable not set!")
        return

    print("🔍 Testing timeout configuration...")

    # Test with different timeouts
    timeouts = [30, 60, 120]

    for timeout in timeouts:
        print(f"\n📄 Testing timeout: {timeout} seconds")

        try:
            crawler = ZyteCrawler(api_key, timeout=timeout)
            print(f"   ✅ ZyteCrawler initialized with timeout: {crawler.timeout}s")

            if crawler.timeout == timeout:
                print(f"   ✅ Timeout correctly set to {timeout}s")
            else:
                print(f"   ❌ Timeout mismatch: expected {timeout}, got {crawler.timeout}")

        except Exception as e:
            print(f"   💥 Error: {e}")

    print(f"\n🎯 Timeout configuration test completed!")

if __name__ == "__main__":
    test_timeout_configuration()