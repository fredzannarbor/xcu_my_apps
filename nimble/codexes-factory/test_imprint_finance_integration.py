#!/usr/bin/env python3
"""
Test script for the Imprint-Finance Integration

This script tests the integration between the imprints module and the
Leo Bloom financial reporting system.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all required modules can be imported."""
    print("🧪 Testing module imports...")

    try:
        from codexes.modules.finance.leo_bloom.integrations.imprint_finance_integration import ImprintFinanceIntegration
        print("✅ ImprintFinanceIntegration import successful")
    except Exception as e:
        print(f"❌ ImprintFinanceIntegration import failed: {e}")
        return False

    try:
        from codexes.modules.imprints.models.imprint_configuration import ImprintConfiguration
        print("✅ ImprintConfiguration import successful")
    except Exception as e:
        print(f"❌ ImprintConfiguration import failed: {e}")
        return False

    try:
        from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
        print("✅ FinancialReportingObjects import successful")
    except Exception as e:
        print(f"❌ FinancialReportingObjects import failed: {e}")
        return False

    return True


def test_integration_basic():
    """Test basic integration functionality."""
    print("\n🧪 Testing basic integration functionality...")

    try:
        from codexes.modules.finance.leo_bloom.integrations.imprint_finance_integration import ImprintFinanceIntegration

        # Initialize integration
        integration = ImprintFinanceIntegration()
        print("✅ Integration initialization successful")

        # Load imprint configurations
        integration.load_imprint_configurations()
        available_imprints = integration.get_available_imprints()
        print(f"✅ Loaded {len(available_imprints)} imprint configurations")

        if available_imprints:
            print(f"📋 Available imprints: {available_imprints[:5]}...")  # Show first 5

            # Test validation
            validation_result = integration.validate_integration()
            print(f"✅ Integration validation: {validation_result['integration_status']}")

            if validation_result['issues']:
                print(f"⚠️ Validation issues found: {len(validation_result['issues'])}")
                for issue in validation_result['issues'][:3]:  # Show first 3 issues
                    print(f"   • {issue}")

            return True
        else:
            print("⚠️ No imprint configurations found")
            return False

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


def test_sample_analysis():
    """Test sample financial analysis for an imprint."""
    print("\n🧪 Testing sample financial analysis...")

    try:
        from codexes.modules.finance.leo_bloom.integrations.imprint_finance_integration import ImprintFinanceIntegration

        integration = ImprintFinanceIntegration()
        integration.load_imprint_configurations()

        available_imprints = integration.get_available_imprints()
        if not available_imprints:
            print("⚠️ No imprints available for testing")
            return False

        # Test with first available imprint
        test_imprint = available_imprints[0]
        print(f"🎯 Testing with imprint: {test_imprint}")

        # Generate summary
        summary = integration.generate_imprint_financial_summary(test_imprint)
        print(f"✅ Generated summary for {test_imprint}")
        print(f"   • Records: {summary.get('records_count', 0)}")
        print(f"   • Revenue: ${summary.get('financial_metrics', {}).get('total_revenue', 0):,.2f}")

        if 'error' in summary:
            print(f"⚠️ Summary contains error: {summary['error']}")
        else:
            print("✅ Summary generated successfully")

        return True

    except Exception as e:
        print(f"❌ Sample analysis test failed: {e}")
        return False


def test_dashboard_import():
    """Test that the dashboard UI can be imported."""
    print("\n🧪 Testing dashboard import...")

    try:
        from codexes.modules.finance.leo_bloom.ui.ImprintFinancialDashboard import ImprintFinancialDashboard
        print("✅ ImprintFinancialDashboard import successful")

        # Try to initialize dashboard
        dashboard = ImprintFinancialDashboard()
        print("✅ Dashboard initialization successful")
        return True

    except Exception as e:
        print(f"❌ Dashboard import failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("🚀 Starting Imprint-Finance Integration Tests\n")

    tests = [
        ("Module Imports", test_imports),
        ("Basic Integration", test_integration_basic),
        ("Sample Analysis", test_sample_analysis),
        ("Dashboard Import", test_dashboard_import)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)

        if test_func():
            passed += 1
            print(f"\n✅ {test_name} PASSED")
        else:
            print(f"\n❌ {test_name} FAILED")

    print(f"\n{'='*60}")
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print('='*60)

    if passed == total:
        print("🎉 All tests passed! Integration is ready to use.")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)