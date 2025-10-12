"""
Quick test script for batch operations module.

This script verifies that all batch operations modules can be imported
and basic functionality works.
"""

import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from codexes.modules.batch_operations import (
            BatchOperationResult,
            ConfigDiff,
            ValidationError,
            IdeationBatchResult,
            BatchRevisionResult,
            complete_and_validate_configs,
            revise_configs_batch,
            create_ideation_tournaments,
            render_path_selector,
            get_predefined_paths,
            get_configs_from_paths,
            render_config_selector,
            BatchConfigLoader,
            BatchValidator,
            BackupManager,
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_path_utilities():
    """Test path utility functions."""
    print("\nTesting path utilities...")

    try:
        from codexes.modules.batch_operations import get_predefined_paths

        paths = get_predefined_paths()
        print(f"✅ Found {len(paths)} predefined paths:")
        for name, path in paths.items():
            exists = "✓" if path.exists() else "✗"
            print(f"   {exists} {name} -> {path}")

        return True
    except Exception as e:
        print(f"❌ Path utilities test failed: {e}")
        return False


def test_config_loader():
    """Test configuration loader."""
    print("\nTesting config loader...")

    try:
        from codexes.modules.batch_operations import BatchConfigLoader
        from pathlib import Path

        loader = BatchConfigLoader()

        # Try to load template
        template_path = Path("configs/imprints/imprint_template.json")
        if template_path.exists():
            template = loader.load_template(template_path)
            if template:
                print(f"✅ Loaded template successfully")
                print(f"   Template has {len(template)} top-level fields")
            else:
                print("⚠️ Template loaded but returned None")
        else:
            print(f"⚠️ Template not found at {template_path}")

        return True
    except Exception as e:
        print(f"❌ Config loader test failed: {e}")
        return False


def test_validator():
    """Test validation utilities."""
    print("\nTesting validator...")

    try:
        from codexes.modules.batch_operations import BatchValidator
        from pathlib import Path

        template_path = Path("configs/imprints/imprint_template.json")
        if template_path.exists():
            validator = BatchValidator(template_path)

            if validator.template_schema:
                print(f"✅ Validator initialized with template")
                print(f"   Template schema has {len(validator.template_schema)} fields")
            else:
                print("⚠️ Validator created but no schema loaded")
        else:
            print(f"⚠️ Template not found, creating validator without schema")
            validator = BatchValidator()
            print("✅ Validator created without schema")

        return True
    except Exception as e:
        print(f"❌ Validator test failed: {e}")
        return False


def test_backup_manager():
    """Test backup manager."""
    print("\nTesting backup manager...")

    try:
        from codexes.modules.batch_operations import BackupManager
        from pathlib import Path

        manager = BackupManager()
        print(f"✅ Backup manager initialized")
        print(f"   Backup directory: {manager.backup_base_dir}")

        if manager.backup_base_dir.exists():
            print(f"   ✓ Backup directory exists")
        else:
            print(f"   Directory will be created on first backup")

        # List existing backups
        backups = manager.list_backups()
        print(f"   Found {len(backups)} existing backups")

        return True
    except Exception as e:
        print(f"❌ Backup manager test failed: {e}")
        return False


def test_models():
    """Test data models."""
    print("\nTesting data models...")

    try:
        from codexes.modules.batch_operations import (
            BatchOperationResult,
            ConfigDiff,
            ValidationError,
            ValidationSeverity
        )

        # Create test result
        result = BatchOperationResult(operation_type="test")
        result.configs_processed = 5
        result.configs_fixed = 3

        # Add test error
        error = ValidationError(
            field="test_field",
            message="Test error",
            severity=ValidationSeverity.WARNING,
            config_name="test_config"
        )
        result.add_error(error)

        # Create test diff
        diff = ConfigDiff(
            field="test.field",
            old_value="old",
            new_value="new",
            config_name="test_config"
        )

        # Convert to dict
        result_dict = result.to_dict()
        diff_dict = diff.to_dict()

        print(f"✅ Models working correctly")
        print(f"   Result has {result.configs_processed} configs processed")
        print(f"   Result dict has {len(result_dict)} keys")

        return True
    except Exception as e:
        print(f"❌ Models test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Batch Operations Module Test Suite")
    print("="*60)

    tests = [
        ("Imports", test_imports),
        ("Path Utilities", test_path_utilities),
        ("Config Loader", test_config_loader),
        ("Validator", test_validator),
        ("Backup Manager", test_backup_manager),
        ("Data Models", test_models),
    ]

    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))

    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Batch operations module is ready to use.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review the errors above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
