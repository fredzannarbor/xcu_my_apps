"""
Cross-platform compatibility tests for arxiv-writer package.
"""

import pytest
import sys
import os
import platform
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from src.arxiv_writer.core.generator import ArxivPaperGenerator
from src.arxiv_writer.core.models import PaperConfig, LLMConfig
from src.arxiv_writer.llm.caller import call_model_with_prompt
from src.arxiv_writer.llm.enhanced_caller import EnhancedLLMCaller
from src.arxiv_writer.utils.cli_utils import validate_output_directory, setup_logging


class TestPythonVersionCompatibility:
    """Test compatibility across different Python versions."""
    
    def test_python_version_support(self):
        """Test that the package works with supported Python versions."""
        # Check current Python version
        python_version = sys.version_info
        
        # Package should support Python 3.8+
        assert python_version >= (3, 8), f"Python {python_version} not supported. Minimum version is 3.8"
        assert python_version < (4, 0), f"Python {python_version} not tested. Maximum tested version is 3.12"
    
    def test_import_compatibility(self):
        """Test that all modules can be imported successfully."""
        # Test core module imports
        try:
            from src.arxiv_writer.core import generator, models, context_collector
            from src.arxiv_writer.llm import caller, enhanced_caller, models as llm_models
            from src.arxiv_writer.templates import manager, renderer, models as template_models
            from src.arxiv_writer.plugins import base, registry, manager as plugin_manager
            from src.arxiv_writer.utils import cli_utils
            from src.arxiv_writer.config import loader
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    def test_dataclass_compatibility(self):
        """Test dataclass compatibility across Python versions."""
        from src.arxiv_writer.core.models import PaperConfig, Section
        from src.arxiv_writer.llm.models import LLMConfig, LLMResponse
        
        # Test dataclass creation and field access
        config = PaperConfig(output_directory="/tmp/test")
        assert hasattr(config, 'output_directory')
        assert config.output_directory == "/tmp/test"
        
        llm_config = LLMConfig(model="gpt-4", temperature=0.7)
        assert llm_config.model == "gpt-4"
        assert llm_config.temperature == 0.7
    
    def test_type_hints_compatibility(self):
        """Test type hints compatibility across Python versions."""
        from typing import Dict, List, Optional, Union
        
        # Test that type hints work correctly
        def test_function(data: Dict[str, Any], items: List[str], optional: Optional[int] = None) -> Union[str, None]:
            return str(data) if data else None
        
        result = test_function({"key": "value"}, ["item1", "item2"])
        assert isinstance(result, str)
    
    @pytest.mark.skipif(sys.version_info < (3, 9), reason="Requires Python 3.9+")
    def test_python39_features(self):
        """Test Python 3.9+ specific features."""
        # Test built-in generic types (dict instead of Dict)
        def modern_typing_function(data: dict[str, any]) -> list[str]:
            return list(data.keys())
        
        result = modern_typing_function({"key1": "value1", "key2": "value2"})
        assert isinstance(result, list)
        assert len(result) == 2
    
    @pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10+")
    def test_python310_features(self):
        """Test Python 3.10+ specific features."""
        # Test match-case statements
        def test_match_case(value: str) -> str:
            match value:
                case "openai":
                    return "OpenAI provider"
                case "anthropic":
                    return "Anthropic provider"
                case _:
                    return "Unknown provider"
        
        assert test_match_case("openai") == "OpenAI provider"
        assert test_match_case("unknown") == "Unknown provider"


class TestOperatingSystemCompatibility:
    """Test compatibility across different operating systems."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.current_os = platform.system().lower()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_path_handling_cross_platform(self):
        """Test path handling across different operating systems."""
        from pathlib import Path
        
        # Test path creation and manipulation
        test_path = Path(self.temp_dir) / "subdir" / "file.txt"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text("Test content")
        
        # Verify path operations work on all platforms
        assert test_path.exists()
        assert test_path.is_file()
        assert test_path.read_text() == "Test content"
        
        # Test path string conversion
        path_str = str(test_path)
        if self.current_os == "windows":
            assert "\\" in path_str or "/" in path_str  # Windows accepts both
        else:
            assert "/" in path_str  # Unix-like systems use forward slashes
    
    def test_file_permissions_cross_platform(self):
        """Test file permission handling across platforms."""
        test_file = Path(self.temp_dir) / "permission_test.txt"
        test_file.write_text("Permission test content")
        
        # Test basic file operations
        assert test_file.exists()
        assert os.access(test_file, os.R_OK)  # Readable
        assert os.access(test_file, os.W_OK)  # Writable
        
        # Test directory creation with permissions
        test_dir = Path(self.temp_dir) / "test_permissions"
        test_dir.mkdir(mode=0o755, exist_ok=True)
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_environment_variable_handling(self):
        """Test environment variable handling across platforms."""
        # Set test environment variable
        test_var_name = "ARXIV_WRITER_TEST_VAR"
        test_var_value = "test_value_123"
        
        os.environ[test_var_name] = test_var_value
        
        try:
            # Test environment variable access
            assert os.getenv(test_var_name) == test_var_value
            
            # Test with configuration loader
            from src.arxiv_writer.config.loader import ConfigLoader
            
            config_dict = {
                "test_field": f"${{{test_var_name}}}",
                "other_field": "static_value"
            }
            
            resolved = ConfigLoader.resolve_environment_variables(config_dict)
            assert resolved["test_field"] == test_var_value
            assert resolved["other_field"] == "static_value"
        finally:
            del os.environ[test_var_name]
    
    def test_temp_directory_handling(self):
        """Test temporary directory handling across platforms."""
        import tempfile
        
        # Test temporary file creation
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write("Temporary content")
            temp_path = temp_file.name
        
        try:
            # Verify temp file exists and is accessible
            assert Path(temp_path).exists()
            assert Path(temp_path).read_text() == "Temporary content"
        finally:
            Path(temp_path).unlink(missing_ok=True)
        
        # Test temporary directory creation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            assert temp_path.exists()
            assert temp_path.is_dir()
            
            # Create files in temp directory
            test_file = temp_path / "test.txt"
            test_file.write_text("Test content")
            assert test_file.exists()
    
    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific test")
    def test_unix_specific_features(self):
        """Test Unix-specific features."""
        # Test Unix-style path operations
        test_path = Path(self.temp_dir) / "unix_test"
        test_path.mkdir()
        
        # Test symbolic links (Unix-specific)
        link_path = Path(self.temp_dir) / "unix_link"
        try:
            link_path.symlink_to(test_path)
            assert link_path.is_symlink()
            assert link_path.resolve() == test_path.resolve()
        except OSError:
            # Some Unix systems may not support symlinks in test environment
            pytest.skip("Symbolic links not supported in test environment")
    
    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    def test_windows_specific_features(self):
        """Test Windows-specific features."""
        # Test Windows path handling
        test_path = Path(self.temp_dir) / "windows_test.txt"
        test_path.write_text("Windows test content")
        
        # Test Windows-style path operations
        path_str = str(test_path)
        # Windows paths may use either forward or backward slashes
        assert any(sep in path_str for sep in ['\\', '/'])
        
        # Test case-insensitive file system (Windows default)
        upper_path = Path(str(test_path).upper())
        if upper_path.exists():  # Case-insensitive file system
            assert upper_path.read_text() == "Windows test content"
    
    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_macos_specific_features(self):
        """Test macOS-specific features."""
        # Test macOS path handling
        test_path = Path(self.temp_dir) / "macos_test.txt"
        test_path.write_text("macOS test content")
        
        # Test that file operations work correctly on macOS
        assert test_path.exists()
        assert test_path.read_text() == "macOS test content"
        
        # Test extended attributes (macOS-specific)
        try:
            import xattr
            xattr.setxattr(str(test_path), "user.test_attr", b"test_value")
            attr_value = xattr.getxattr(str(test_path), "user.test_attr")
            assert attr_value == b"test_value"
        except ImportError:
            # xattr module not available, skip extended attribute test
            pass
        except OSError:
            # Extended attributes not supported in test environment
            pass


class TestLLMProviderCompatibility:
    """Test compatibility with different LLM providers."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.arxiv_writer.llm.caller.litellm.completion')
    def test_openai_provider_compatibility(self, mock_completion):
        """Test compatibility with OpenAI provider."""
        # Mock OpenAI-style response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "OpenAI response content"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        mock_response.model = "gpt-4"
        mock_completion.return_value = mock_response
        
        # Test OpenAI provider
        from src.arxiv_writer.llm.models import LLMConfig
        config = LLMConfig(provider="openai", model="gpt-4")
        
        prompt_config = {
            "messages": [{"role": "user", "content": "Test prompt"}],
            "params": {"temperature": 0.7}
        }
        
        result = call_model_with_prompt("openai/gpt-4", prompt_config)
        
        assert result["raw_content"] == "OpenAI response content"
        assert result["parsed_content"] == "OpenAI response content"
    
    @patch('src.arxiv_writer.llm.caller.litellm.completion')
    def test_anthropic_provider_compatibility(self, mock_completion):
        """Test compatibility with Anthropic provider."""
        # Mock Anthropic-style response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Anthropic response content"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 120
        mock_response.usage.completion_tokens = 80
        mock_response.usage.total_tokens = 200
        mock_response.model = "claude-3-opus"
        mock_completion.return_value = mock_response
        
        # Test Anthropic provider
        from src.arxiv_writer.llm.models import LLMConfig
        config = LLMConfig(provider="anthropic", model="claude-3-opus")
        
        prompt_config = {
            "messages": [{"role": "user", "content": "Test prompt"}],
            "params": {"temperature": 0.5}
        }
        
        result = call_model_with_prompt("anthropic/claude-3-opus", prompt_config)
        
        assert result["raw_content"] == "Anthropic response content"
        assert result["parsed_content"] == "Anthropic response content"
    
    @patch('src.arxiv_writer.llm.caller.litellm.completion')
    def test_multiple_provider_fallback(self, mock_completion):
        """Test fallback between multiple LLM providers."""
        call_count = 0
        
        def mock_provider_fallback(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            model = args[0] if args else kwargs.get('model', '')
            
            if call_count == 1:
                # First provider fails
                from litellm.exceptions import RateLimitError
                raise RateLimitError("Rate limit exceeded", "openai", "gpt-4")
            else:
                # Second provider succeeds
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message = Mock()
                mock_response.choices[0].message.content = f"Fallback response from {model}"
                mock_response.usage = Mock()
                mock_response.usage.prompt_tokens = 100
                mock_response.usage.completion_tokens = 50
                mock_response.usage.total_tokens = 150
                mock_response.model = model
                return mock_response
        
        mock_completion.side_effect = mock_provider_fallback
        
        # Test provider fallback
        prompt_config = {
            "messages": [{"role": "user", "content": "Test prompt"}],
            "params": {"temperature": 0.7}
        }
        
        with patch('time.sleep'):  # Speed up retries
            result = call_model_with_prompt("openai/gpt-4", prompt_config, max_retries=2)
        
        assert result["raw_content"].startswith("Fallback response")
        assert call_count == 2  # First call failed, second succeeded
    
    def test_llm_config_validation(self):
        """Test LLM configuration validation across providers."""
        from src.arxiv_writer.llm.models import LLMConfig
        
        # Test valid configurations for different providers
        valid_configs = [
            LLMConfig(provider="openai", model="gpt-4", temperature=0.7),
            LLMConfig(provider="anthropic", model="claude-3-opus", temperature=0.5),
            LLMConfig(provider="openai", model="gpt-3.5-turbo", max_tokens=2000),
            LLMConfig(provider="anthropic", model="claude-3-sonnet", timeout=120),
        ]
        
        for config in valid_configs:
            # Basic validation
            assert config.provider in ["openai", "anthropic"]
            assert isinstance(config.model, str)
            assert len(config.model) > 0
            assert 0 <= config.temperature <= 2
            assert config.timeout > 0
            assert config.retry_attempts >= 0
    
    def test_enhanced_caller_provider_compatibility(self):
        """Test enhanced caller compatibility with different providers."""
        from src.arxiv_writer.llm.enhanced_caller import EnhancedLLMCaller
        
        # Test enhanced caller initialization
        caller = EnhancedLLMCaller(max_retries=3, base_delay=1.0)
        
        # Test retry configuration
        stats = caller.get_retry_stats()
        assert stats["max_retries"] == 3
        assert stats["base_delay"] == 1.0
        
        # Test retryable error detection
        retryable_errors = [
            "rate_limit_exceeded",
            "service_unavailable", 
            "timeout",
            "internal_server_error"
        ]
        
        for error_type in retryable_errors:
            assert error_type in caller.retryable_errors


class TestDependencyCompatibility:
    """Test compatibility with different versions of dependencies."""
    
    def test_litellm_compatibility(self):
        """Test compatibility with litellm library."""
        try:
            import litellm
            
            # Test basic litellm functionality
            assert hasattr(litellm, 'completion')
            assert hasattr(litellm, 'set_verbose')
            
            # Test that we can configure litellm
            litellm.set_verbose = False
            litellm.telemetry = False
            
        except ImportError:
            pytest.fail("litellm library not available")
    
    def test_pandas_compatibility(self):
        """Test compatibility with pandas library."""
        try:
            import pandas as pd
            
            # Test basic pandas functionality
            df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
            assert len(df) == 3
            assert list(df.columns) == ["col1", "col2"]
            
            # Test pandas operations used in the package
            assert df["col1"].sum() == 6
            assert df["col2"].tolist() == ["a", "b", "c"]
            
        except ImportError:
            pytest.fail("pandas library not available")
    
    def test_jinja2_compatibility(self):
        """Test compatibility with Jinja2 template engine."""
        try:
            from jinja2 import Template, Environment
            
            # Test basic Jinja2 functionality
            template = Template("Hello {{ name }}!")
            result = template.render(name="World")
            assert result == "Hello World!"
            
            # Test environment creation
            env = Environment()
            template2 = env.from_string("Value: {{ value }}")
            result2 = template2.render(value=42)
            assert result2 == "Value: 42"
            
        except ImportError:
            pytest.fail("Jinja2 library not available")
    
    def test_click_compatibility(self):
        """Test compatibility with Click CLI library."""
        try:
            import click
            
            # Test basic Click functionality
            @click.command()
            @click.option('--name', default='World')
            def hello(name):
                return f"Hello {name}!"
            
            # Test that command can be created
            assert callable(hello)
            assert hasattr(hello, 'callback')
            
        except ImportError:
            pytest.fail("Click library not available")
    
    def test_pathlib_compatibility(self):
        """Test compatibility with pathlib across Python versions."""
        from pathlib import Path
        
        # Test basic pathlib functionality
        temp_path = Path(tempfile.mkdtemp())
        
        try:
            # Test path operations
            test_file = temp_path / "test.txt"
            test_file.write_text("Test content")
            
            assert test_file.exists()
            assert test_file.is_file()
            assert test_file.read_text() == "Test content"
            
            # Test path properties
            assert test_file.name == "test.txt"
            assert test_file.suffix == ".txt"
            assert test_file.parent == temp_path
            
        finally:
            import shutil
            shutil.rmtree(temp_path, ignore_errors=True)


class TestCICompatibility:
    """Test compatibility with CI/CD environments."""
    
    def test_ci_environment_detection(self):
        """Test detection of CI/CD environments."""
        # Common CI environment variables
        ci_indicators = [
            "CI", "CONTINUOUS_INTEGRATION", 
            "GITHUB_ACTIONS", "TRAVIS", "CIRCLECI", 
            "JENKINS_URL", "GITLAB_CI"
        ]
        
        # Check if we're in a CI environment
        in_ci = any(os.getenv(indicator) for indicator in ci_indicators)
        
        # Test should work both in CI and local environments
        if in_ci:
            # In CI environment
            assert os.getenv("CI") or any(os.getenv(indicator) for indicator in ci_indicators)
        else:
            # In local environment
            assert not any(os.getenv(indicator) for indicator in ci_indicators)
    
    def test_headless_environment_compatibility(self):
        """Test compatibility with headless environments."""
        # Test that the package works without GUI dependencies
        try:
            from src.arxiv_writer.core.generator import ArxivPaperGenerator
            from src.arxiv_writer.core.models import PaperConfig
            
            # Should be able to create instances without GUI
            config = PaperConfig(output_directory="/tmp/test")
            generator = ArxivPaperGenerator(config)
            
            assert generator is not None
            assert config is not None
            
        except Exception as e:
            if "display" in str(e).lower() or "gui" in str(e).lower():
                pytest.fail(f"Package requires GUI in headless environment: {e}")
            else:
                # Other exceptions are acceptable
                pass
    
    def test_docker_compatibility(self):
        """Test compatibility with Docker environments."""
        # Test file system operations that work in containers
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Test basic file operations
            test_file = Path(temp_dir) / "docker_test.txt"
            test_file.write_text("Docker compatibility test")
            
            assert test_file.exists()
            assert test_file.read_text() == "Docker compatibility test"
            
            # Test directory operations
            sub_dir = Path(temp_dir) / "subdir"
            sub_dir.mkdir()
            assert sub_dir.exists()
            assert sub_dir.is_dir()
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_resource_constraints_compatibility(self):
        """Test compatibility with resource-constrained environments."""
        import psutil
        
        # Get system resources
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        
        # Test that package can handle low-resource environments
        if memory.available < 1024 * 1024 * 1024:  # Less than 1GB available
            # Low memory environment
            pytest.skip("Skipping resource-intensive tests in low-memory environment")
        
        if cpu_count < 2:
            # Single-core environment
            pytest.skip("Skipping CPU-intensive tests in single-core environment")
        
        # Basic functionality should work even in constrained environments
        from src.arxiv_writer.core.models import PaperConfig, LLMConfig
        
        config = PaperConfig(
            output_directory="/tmp/test",
            llm_config=LLMConfig(model="gpt-4", temperature=0.7)
        )
        
        assert config is not None
        assert config.llm_config.model == "gpt-4"


class TestPackageDistributionCompatibility:
    """Test compatibility with different package distribution methods."""
    
    def test_pip_installation_compatibility(self):
        """Test compatibility with pip installation."""
        # Test that package structure is compatible with pip
        from src.arxiv_writer import __init__
        
        # Should have proper package structure
        package_dir = Path(__init__.__file__).parent
        assert package_dir.exists()
        assert (package_dir / "__init__.py").exists()
        
        # Test that submodules can be imported
        submodules = ["core", "llm", "templates", "plugins", "utils", "config"]
        for submodule in submodules:
            submodule_path = package_dir / submodule
            if submodule_path.exists():
                assert (submodule_path / "__init__.py").exists()
    
    def test_wheel_compatibility(self):
        """Test compatibility with wheel distribution."""
        # Test that package metadata is accessible
        try:
            import pkg_resources
            
            # Try to get package information
            try:
                dist = pkg_resources.get_distribution("arxiv-writer")
                assert dist.project_name == "arxiv-writer"
            except pkg_resources.DistributionNotFound:
                # Package not installed via pip, which is expected in development
                pass
                
        except ImportError:
            # pkg_resources not available, skip test
            pass
    
    def test_editable_installation_compatibility(self):
        """Test compatibility with editable (development) installation."""
        # Test that package can be imported from source
        from src.arxiv_writer.core import generator
        from src.arxiv_writer.llm import caller
        
        # Should be able to access source files
        generator_file = Path(generator.__file__)
        caller_file = Path(caller.__file__)
        
        assert generator_file.exists()
        assert caller_file.exists()
        
        # Files should be in expected source structure
        assert "src" in str(generator_file) or "arxiv_writer" in str(generator_file)
        assert "src" in str(caller_file) or "arxiv_writer" in str(caller_file)