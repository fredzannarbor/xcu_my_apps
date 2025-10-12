"""
Integration tests for complete paper generation workflow.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.arxiv_writer.core.generator import ArxivPaperGenerator
from src.arxiv_writer.core.models import PaperConfig, LLMConfig, TemplateConfig
from src.arxiv_writer.core.context_collector import ContextCollector
from src.arxiv_writer.core.section_generator import SectionGenerator
from src.arxiv_writer.templates.manager import TemplateManager
from src.arxiv_writer.llm.caller import call_model_with_prompt


class TestPaperGenerationIntegration:
    """Integration tests for complete paper generation workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = PaperConfig(
            output_directory=self.temp_dir,
            llm_config=LLMConfig(
                provider="openai",
                model="gpt-4",
                temperature=0.7
            ),
            template_config=TemplateConfig(
                template_file="default.json"
            )
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.arxiv_writer.llm.caller.litellm.completion')
    def test_end_to_end_paper_generation_with_mock_llm(self, mock_completion):
        """Test complete paper generation workflow with mocked LLM calls."""
        # Mock LLM responses for different sections
        mock_responses = {
            "abstract": "This paper presents a comprehensive analysis of machine learning techniques...",
            "introduction": "Machine learning has revolutionized many fields...",
            "methodology": "Our approach consists of three main components...",
            "results": "The experimental results demonstrate significant improvements...",
            "conclusion": "In conclusion, our method achieves state-of-the-art performance..."
        }
        
        def mock_llm_response(*args, **kwargs):
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            
            # Determine which section based on the prompt content
            messages = kwargs.get('messages', args[1] if len(args) > 1 else [])
            prompt_content = str(messages).lower()
            
            if 'abstract' in prompt_content:
                content = mock_responses["abstract"]
            elif 'introduction' in prompt_content:
                content = mock_responses["introduction"]
            elif 'methodology' in prompt_content or 'method' in prompt_content:
                content = mock_responses["methodology"]
            elif 'result' in prompt_content:
                content = mock_responses["results"]
            elif 'conclusion' in prompt_content:
                content = mock_responses["conclusion"]
            else:
                content = "Generated content for section"
            
            mock_response.choices[0].message.content = content
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 200
            mock_response.usage.total_tokens = 300
            return mock_response
        
        mock_completion.side_effect = mock_llm_response
        
        # Create test context data
        context_data = {
            "title": "Advanced Machine Learning Techniques",
            "authors": ["John Doe", "Jane Smith"],
            "abstract": "Initial abstract content",
            "keywords": ["machine learning", "neural networks", "deep learning"],
            "sections": {
                "introduction": "Brief introduction",
                "methodology": "Method overview",
                "results": "Results summary",
                "conclusion": "Conclusion summary"
            }
        }
        
        # Initialize generator
        generator = ArxivPaperGenerator(self.config)
        
        # Generate paper
        result = generator.generate_paper(
            context_data=context_data,
            output_dir=self.temp_dir
        )
        
        # Verify results
        assert result.success is True
        assert len(result.sections) > 0
        assert result.complete_paper is not None
        assert len(result.complete_paper) > 0
        
        # Verify that LLM was called multiple times (once per section)
        assert mock_completion.call_count >= len(context_data["sections"])
        
        # Verify output files were created
        assert len(result.output_files) > 0
        for file_path in result.output_files:
            assert Path(file_path).exists()
    
    @patch('src.arxiv_writer.llm.caller.litellm.completion')
    def test_paper_generation_with_real_llm_structure(self, mock_completion):
        """Test paper generation with realistic LLM response structure."""
        # Create more realistic LLM responses
        def realistic_llm_response(*args, **kwargs):
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].finish_reason = "stop"
            
            # Generate realistic content based on section
            messages = kwargs.get('messages', args[1] if len(args) > 1 else [])
            prompt_content = str(messages).lower()
            
            if 'abstract' in prompt_content:
                content = """
                This paper introduces a novel approach to machine learning that combines 
                deep neural networks with reinforcement learning techniques. Our method 
                achieves state-of-the-art performance on several benchmark datasets, 
                demonstrating improvements of up to 15% over existing approaches.
                """
            elif 'introduction' in prompt_content:
                content = """
                \\section{Introduction}
                
                Machine learning has become increasingly important in recent years, with 
                applications spanning from computer vision to natural language processing. 
                However, existing approaches face several limitations...
                
                The main contributions of this work are:
                \\begin{itemize}
                \\item A novel architecture combining CNNs and RNNs
                \\item Comprehensive evaluation on multiple datasets
                \\item Open-source implementation for reproducibility
                \\end{itemize}
                """
            else:
                content = f"Generated content for section with LaTeX formatting."
            
            mock_response.choices[0].message.content = content.strip()
            
            # Add realistic usage statistics
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = len(str(messages)) // 4  # Rough estimate
            mock_response.usage.completion_tokens = len(content) // 4
            mock_response.usage.total_tokens = mock_response.usage.prompt_tokens + mock_response.usage.completion_tokens
            
            return mock_response
        
        mock_completion.side_effect = realistic_llm_response
        
        # Create comprehensive context data
        context_data = {
            "title": "Novel Deep Learning Architecture for Multi-Modal Learning",
            "authors": [
                {"name": "Dr. Alice Johnson", "affiliation": "MIT", "email": "alice@mit.edu"},
                {"name": "Prof. Bob Wilson", "affiliation": "Stanford", "email": "bob@stanford.edu"}
            ],
            "abstract": "This work presents a groundbreaking approach...",
            "keywords": ["deep learning", "multi-modal", "neural networks", "computer vision"],
            "sections": {
                "introduction": {"order": 1, "required": True},
                "related_work": {"order": 2, "required": True},
                "methodology": {"order": 3, "required": True},
                "experiments": {"order": 4, "required": True},
                "results": {"order": 5, "required": True},
                "discussion": {"order": 6, "required": False},
                "conclusion": {"order": 7, "required": True}
            },
            "references": [
                {
                    "title": "Attention Is All You Need",
                    "authors": ["Vaswani et al."],
                    "venue": "NIPS",
                    "year": 2017
                },
                {
                    "title": "Deep Residual Learning for Image Recognition",
                    "authors": ["He et al."],
                    "venue": "CVPR",
                    "year": 2016
                }
            ],
            "datasets": ["ImageNet", "COCO", "CIFAR-10"],
            "metrics": ["Accuracy", "F1-Score", "BLEU"]
        }
        
        # Generate paper with comprehensive configuration
        generator = ArxivPaperGenerator(self.config)
        result = generator.generate_paper(
            context_data=context_data,
            output_dir=self.temp_dir,
            compile_pdf=False  # Skip PDF compilation for faster testing
        )
        
        # Comprehensive verification
        assert result.success is True
        assert len(result.sections) >= 5  # At least the required sections
        
        # Verify section content quality
        for section_name, section in result.sections.items():
            assert section.content is not None
            assert len(section.content.strip()) > 0
            assert section.word_count > 0
            assert section.model_used is not None
        
        # Verify complete paper assembly
        assert result.complete_paper is not None
        assert len(result.complete_paper) > 1000  # Reasonable length
        
        # Verify generation summary
        assert result.generation_summary is not None
        assert result.generation_summary.total_sections > 0
        assert result.generation_summary.total_words > 0
        assert result.generation_summary.generation_time > 0
    
    def test_paper_generation_error_handling(self):
        """Test paper generation error handling and recovery."""
        # Test with invalid context data
        invalid_context = {
            "title": "",  # Empty title
            "authors": [],  # No authors
            "sections": {}  # No sections
        }
        
        generator = ArxivPaperGenerator(self.config)
        
        with pytest.raises(Exception):  # Should raise validation error
            generator.generate_paper(
                context_data=invalid_context,
                output_dir=self.temp_dir
            )
    
    @patch('src.arxiv_writer.llm.caller.litellm.completion')
    def test_paper_generation_with_llm_failures(self, mock_completion):
        """Test paper generation resilience to LLM failures."""
        call_count = 0
        
        def failing_llm_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            # Fail first few calls, then succeed
            if call_count <= 2:
                from litellm.exceptions import RateLimitError
                raise RateLimitError("Rate limit exceeded", "test_provider", "test_model")
            
            # Successful response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "Generated content after retry"
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 50
            mock_response.usage.completion_tokens = 100
            mock_response.usage.total_tokens = 150
            return mock_response
        
        mock_completion.side_effect = failing_llm_response
        
        context_data = {
            "title": "Test Paper",
            "authors": ["Test Author"],
            "sections": {"introduction": "Test intro"}
        }
        
        generator = ArxivPaperGenerator(self.config)
        
        with patch('time.sleep'):  # Speed up retries
            result = generator.generate_paper(
                context_data=context_data,
                output_dir=self.temp_dir
            )
        
        # Should eventually succeed despite initial failures
        assert result.success is True
        assert call_count > 2  # Verify retries occurred
    
    def test_paper_generation_performance_tracking(self):
        """Test performance tracking during paper generation."""
        with patch('src.arxiv_writer.llm.caller.litellm.completion') as mock_completion:
            # Mock fast LLM response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "Fast generated content"
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 25
            mock_response.usage.completion_tokens = 50
            mock_response.usage.total_tokens = 75
            mock_completion.return_value = mock_response
            
            context_data = {
                "title": "Performance Test Paper",
                "authors": ["Test Author"],
                "sections": {
                    "introduction": "Intro",
                    "methodology": "Methods",
                    "results": "Results"
                }
            }
            
            generator = ArxivPaperGenerator(self.config)
            
            import time
            start_time = time.time()
            result = generator.generate_paper(
                context_data=context_data,
                output_dir=self.temp_dir
            )
            end_time = time.time()
            
            # Verify performance tracking
            assert result.generation_summary.generation_time > 0
            assert result.generation_summary.generation_time <= (end_time - start_time) + 1  # Allow some margin
            
            # Verify token usage tracking
            assert result.generation_summary.total_tokens > 0
            assert result.generation_summary.llm_calls > 0


class TestPluginSystemIntegration:
    """Integration tests for plugin system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_custom_section_plugin_integration(self):
        """Test integration with custom section plugins."""
        from src.arxiv_writer.plugins.base import SectionPlugin
        from src.arxiv_writer.plugins.registry import PluginRegistry
        
        # Create a custom section plugin
        class CustomIntroductionPlugin(SectionPlugin):
            def __init__(self, config):
                super().__init__(config)
                self.name = "custom_introduction"
            
            def generate_section(self, context):
                return {
                    "content": f"Custom introduction for: {context.get('title', 'Unknown')}",
                    "word_count": 50,
                    "metadata": {"plugin": "custom_introduction"}
                }
            
            def validate_section(self, section):
                return {"valid": True, "errors": [], "warnings": []}
        
        # Register the plugin
        registry = PluginRegistry()
        plugin = CustomIntroductionPlugin({})
        registry.register_plugin("custom_introduction", plugin)
        
        # Test plugin integration
        context = {"title": "Test Paper with Custom Plugin"}
        result = plugin.generate_section(context)
        
        assert result["content"] == "Custom introduction for: Test Paper with Custom Plugin"
        assert result["word_count"] == 50
        assert result["metadata"]["plugin"] == "custom_introduction"
    
    def test_formatter_plugin_integration(self):
        """Test integration with custom formatter plugins."""
        from src.arxiv_writer.plugins.base import FormatterPlugin
        
        class MarkdownFormatterPlugin(FormatterPlugin):
            def __init__(self, config):
                super().__init__(config)
                self.name = "markdown_formatter"
            
            def format_paper(self, sections):
                formatted = "# Paper\n\n"
                for section_name, section in sections.items():
                    formatted += f"## {section_name.title()}\n\n"
                    formatted += f"{section.content}\n\n"
                return formatted
            
            def get_supported_formats(self):
                return ["markdown", "md"]
        
        # Test formatter plugin
        plugin = MarkdownFormatterPlugin({})
        
        # Mock sections
        from src.arxiv_writer.core.models import Section
        sections = {
            "introduction": Section(
                name="introduction",
                content="This is the introduction section.",
                word_count=6,
                generated_at=None,
                model_used="test-model",
                validation_status=None,
                metadata={}
            ),
            "conclusion": Section(
                name="conclusion",
                content="This is the conclusion section.",
                word_count=6,
                generated_at=None,
                model_used="test-model",
                validation_status=None,
                metadata={}
            )
        }
        
        formatted = plugin.format_paper(sections)
        
        assert "# Paper" in formatted
        assert "## Introduction" in formatted
        assert "## Conclusion" in formatted
        assert "This is the introduction section." in formatted
        assert "This is the conclusion section." in formatted
    
    def test_plugin_discovery_and_loading(self):
        """Test plugin discovery and loading mechanism."""
        from src.arxiv_writer.plugins.manager import PluginManager
        
        # Create a temporary plugin file
        plugin_code = '''
from src.arxiv_writer.plugins.base import SectionPlugin

class TestDiscoveryPlugin(SectionPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "test_discovery"
    
    def generate_section(self, context):
        return {"content": "Discovered plugin content", "word_count": 3}
'''
        
        plugin_file = Path(self.temp_dir) / "test_plugin.py"
        plugin_file.write_text(plugin_code)
        
        # Test plugin discovery
        manager = PluginManager()
        
        # Mock the plugin discovery to include our test plugin
        with patch.object(manager, 'discover_plugins') as mock_discover:
            mock_discover.return_value = [str(plugin_file)]
            
            discovered_plugins = manager.discover_plugins()
            assert str(plugin_file) in discovered_plugins


class TestCodexesFactoryCompatibility:
    """Integration tests for Codexes Factory compatibility."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_codexes_factory_config_migration(self):
        """Test migration from Codexes Factory configuration format."""
        from src.arxiv_writer.core.codexes_factory_adapter import CodexesFactoryAdapter
        
        # Create a mock Codexes Factory configuration
        codexes_config = {
            "llm_config": {
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "${OPENAI_API_KEY}",
                "temperature": 0.7,
                "max_tokens": 4000
            },
            "output_settings": {
                "directory": "/tmp/codexes_output",
                "format": "latex"
            },
            "paper_structure": {
                "sections": ["abstract", "introduction", "methodology", "results", "conclusion"],
                "include_bibliography": True,
                "citation_style": "ieee"
            }
        }
        
        # Test configuration migration
        adapter = CodexesFactoryAdapter()
        arxiv_config = adapter.migrate_config(codexes_config)
        
        # Verify migration
        assert arxiv_config.llm_config.provider == "openai"
        assert arxiv_config.llm_config.model == "gpt-4"
        assert arxiv_config.llm_config.temperature == 0.7
        assert arxiv_config.output_directory == "/tmp/codexes_output"
    
    @patch('src.arxiv_writer.llm.caller.litellm.completion')
    def test_codexes_factory_workflow_compatibility(self, mock_completion):
        """Test compatibility with Codexes Factory workflow."""
        from src.arxiv_writer.core.codexes_factory_adapter import CodexesFactoryAdapter
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Compatible generated content"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 200
        mock_response.usage.total_tokens = 300
        mock_completion.return_value = mock_response
        
        # Create Codexes Factory style input
        codexes_input = {
            "project_name": "test_project",
            "analysis_data": {
                "summary": "Project analysis summary",
                "key_findings": ["Finding 1", "Finding 2"],
                "metrics": {"accuracy": 0.95, "precision": 0.92}
            },
            "configuration": {
                "output_format": "arxiv",
                "include_code_examples": True,
                "citation_style": "acm"
            }
        }
        
        # Test compatibility workflow
        adapter = CodexesFactoryAdapter()
        result = adapter.generate_arxiv_paper(codexes_input, self.temp_dir)
        
        # Verify compatibility
        assert result["success"] is True
        assert "output_files" in result
        assert len(result["output_files"]) > 0
    
    def test_xynapse_traces_compatibility(self):
        """Test compatibility with xynapse traces configuration."""
        from src.arxiv_writer.core.codexes_factory_adapter import CodexesFactoryAdapter
        
        # Mock xynapse traces configuration
        xynapse_config = {
            "imprint_config": {
                "name": "test_imprint",
                "version": "1.0",
                "analysis_type": "comprehensive"
            },
            "trace_data": {
                "execution_traces": ["trace1", "trace2"],
                "performance_metrics": {"latency": 100, "throughput": 1000},
                "error_analysis": {"total_errors": 5, "error_types": ["timeout", "memory"]}
            },
            "output_preferences": {
                "format": "academic_paper",
                "sections": ["abstract", "introduction", "analysis", "results", "conclusion"],
                "include_appendix": True
            }
        }
        
        # Test xynapse compatibility
        adapter = CodexesFactoryAdapter()
        converted_context = adapter.convert_xynapse_traces(xynapse_config)
        
        # Verify conversion
        assert "title" in converted_context
        assert "sections" in converted_context
        assert "analysis_data" in converted_context
        assert converted_context["analysis_data"]["performance_metrics"]["latency"] == 100


class TestPerformanceIntegration:
    """Integration tests for performance and large context processing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.arxiv_writer.llm.caller.litellm.completion')
    def test_large_context_processing(self, mock_completion):
        """Test processing of large context data."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Processed large context successfully"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 5000
        mock_response.usage.completion_tokens = 1000
        mock_response.usage.total_tokens = 6000
        mock_completion.return_value = mock_response
        
        # Create large context data
        large_context = {
            "title": "Large Scale Analysis of Machine Learning Systems",
            "authors": [f"Author {i}" for i in range(20)],  # Many authors
            "abstract": "A" * 1000,  # Large abstract
            "keywords": [f"keyword_{i}" for i in range(100)],  # Many keywords
            "sections": {
                f"section_{i}": f"Content for section {i} " * 100  # Large sections
                for i in range(10)
            },
            "references": [
                {
                    "title": f"Reference {i}",
                    "authors": [f"Ref Author {j}" for j in range(5)],
                    "abstract": "Reference abstract " * 50,
                    "year": 2020 + (i % 4)
                }
                for i in range(200)  # Many references
            ],
            "datasets": [f"Dataset_{i}" for i in range(50)],
            "code_examples": [
                {
                    "language": "python",
                    "code": "def example_function():\n    " + "pass\n    " * 20,
                    "description": "Example code " * 10
                }
                for i in range(20)
            ]
        }
        
        # Test large context processing
        config = PaperConfig(
            output_directory=self.temp_dir,
            llm_config=LLMConfig(model="gpt-4", max_tokens=8000)
        )
        
        generator = ArxivPaperGenerator(config)
        
        import time
        start_time = time.time()
        result = generator.generate_paper(
            context_data=large_context,
            output_dir=self.temp_dir
        )
        processing_time = time.time() - start_time
        
        # Verify large context handling
        assert result.success is True
        assert processing_time < 60  # Should complete within reasonable time
        assert result.generation_summary.total_tokens > 1000  # Significant token usage
        
        # Verify that context was properly chunked/processed
        assert len(result.sections) > 0
        for section in result.sections.values():
            assert len(section.content) > 0
    
    @patch('src.arxiv_writer.llm.caller.litellm.completion')
    def test_concurrent_section_generation(self, mock_completion):
        """Test concurrent generation of multiple sections."""
        import threading
        import time
        
        call_times = []
        
        def timed_llm_response(*args, **kwargs):
            call_times.append(time.time())
            time.sleep(0.1)  # Simulate processing time
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = f"Section content generated at {time.time()}"
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 200
            mock_response.usage.total_tokens = 300
            return mock_response
        
        mock_completion.side_effect = timed_llm_response
        
        context_data = {
            "title": "Concurrent Processing Test",
            "authors": ["Test Author"],
            "sections": {
                f"section_{i}": f"Content for section {i}"
                for i in range(5)
            }
        }
        
        config = PaperConfig(
            output_directory=self.temp_dir,
            llm_config=LLMConfig(model="gpt-4")
        )
        
        generator = ArxivPaperGenerator(config)
        
        start_time = time.time()
        result = generator.generate_paper(
            context_data=context_data,
            output_dir=self.temp_dir
        )
        total_time = time.time() - start_time
        
        # Verify concurrent processing benefits
        assert result.success is True
        assert len(call_times) == len(context_data["sections"])
        
        # If truly concurrent, total time should be less than sum of individual times
        expected_sequential_time = len(context_data["sections"]) * 0.1
        assert total_time < expected_sequential_time * 1.5  # Allow some overhead
    
    def test_memory_usage_optimization(self):
        """Test memory usage optimization for large papers."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create memory-intensive context
        memory_intensive_context = {
            "title": "Memory Usage Test",
            "large_data": {
                "matrix": [[i * j for j in range(1000)] for i in range(1000)],  # Large matrix
                "text_data": ["Large text content " * 1000 for _ in range(100)],  # Large text arrays
                "nested_structure": {
                    f"level_{i}": {
                        f"sublevel_{j}": [f"data_{k}" for k in range(100)]
                        for j in range(50)
                    }
                    for i in range(10)
                }
            }
        }
        
        # Process the context
        from src.arxiv_writer.core.context_collector import ContextCollector
        collector = ContextCollector({})
        
        # This should not cause excessive memory usage
        processed_context = collector.prepare_context(memory_intensive_context)
        
        # Check memory usage after processing
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 500MB for this test)
        assert memory_increase < 500, f"Memory usage increased by {memory_increase}MB"
        
        # Verify that processing was successful
        assert processed_context is not None
        assert "title" in processed_context