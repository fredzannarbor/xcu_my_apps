# tests/test_field_mapping.py

import pytest
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass

from codexes.modules.distribution.field_mapping import (
    MappingStrategy, MappingContext, DirectMappingStrategy, 
    ComputedMappingStrategy, DefaultMappingStrategy, 
    ConditionalMappingStrategy, LLMCompletionStrategy,
    FieldMappingRegistry, create_default_lsi_registry
)
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestMappingContext:
    """Test the MappingContext dataclass."""
    
    def test_mapping_context_creation(self):
        """Test that MappingContext can be created with required fields."""
        context = MappingContext(
            field_name="test_field",
            lsi_headers=["Header1", "Header2"],
            current_row_data={"field1": "value1"}
        )
        
        assert context.field_name == "test_field"
        assert context.lsi_headers == ["Header1", "Header2"]
        assert context.current_row_data == {"field1": "value1"}
        assert context.config is None
        assert context.metadata is None
    
    def test_mapping_context_with_optional_fields(self):
        """Test MappingContext with optional fields."""
        metadata = CodexMetadata()
        config = {"key": "value"}
        
        context = MappingContext(
            field_name="test_field",
            lsi_headers=["Header1"],
            current_row_data={},
            config=config,
            metadata=metadata
        )
        
        assert context.config == config
        assert context.metadata == metadata


class TestMappingStrategy:
    """Test the abstract MappingStrategy base class."""
    
    def test_mapping_strategy_is_abstract(self):
        """Test that MappingStrategy cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MappingStrategy()
    
    def test_validate_input_default_implementation(self):
        """Test the default validate_input implementation."""
        # Create a concrete implementation for testing
        class TestStrategy(MappingStrategy):
            def map_field(self, metadata, context):
                return "test"
        
        strategy = TestStrategy()
        metadata = CodexMetadata()
        context = MappingContext("test", [], {})
        
        assert strategy.validate_input(metadata, context) is True


class TestDirectMappingStrategy:
    """Test the DirectMappingStrategy class."""
    
    def test_direct_mapping_with_value(self):
        """Test direct mapping when metadata field has a value."""
        metadata = CodexMetadata(title="Test Book")
        context = MappingContext("title", [], {})
        strategy = DirectMappingStrategy("title", "Default Title")
        
        result = strategy.map_field(metadata, context)
        assert result == "Test Book"
    
    def test_direct_mapping_with_empty_string(self):
        """Test direct mapping when metadata field is empty string."""
        metadata = CodexMetadata(title="")
        context = MappingContext("title", [], {})
        strategy = DirectMappingStrategy("title", "Default Title")
        
        result = strategy.map_field(metadata, context)
        assert result == "Default Title"
    
    def test_direct_mapping_with_none_value(self):
        """Test direct mapping when metadata field is None."""
        metadata = CodexMetadata()
        context = MappingContext("nonexistent_field", [], {})
        strategy = DirectMappingStrategy("nonexistent_field", "Default Value")
        
        result = strategy.map_field(metadata, context)
        assert result == "Default Value"
    
    def test_direct_mapping_with_numeric_value(self):
        """Test direct mapping with numeric values."""
        metadata = CodexMetadata(page_count=150)
        context = MappingContext("page_count", [], {})
        strategy = DirectMappingStrategy("page_count", "0")
        
        result = strategy.map_field(metadata, context)
        assert result == "150"
    
    def test_direct_mapping_no_default(self):
        """Test direct mapping without default value."""
        metadata = CodexMetadata(title="")
        context = MappingContext("title", [], {})
        strategy = DirectMappingStrategy("title")
        
        result = strategy.map_field(metadata, context)
        assert result == ""


class TestComputedMappingStrategy:
    """Test the ComputedMappingStrategy class."""
    
    def test_computed_mapping_success(self):
        """Test computed mapping with successful computation."""
        def compute_weight(metadata, context):
            return f"{metadata.page_count * 0.1:.2f}"
        
        metadata = CodexMetadata(page_count=100)
        context = MappingContext("weight", [], {})
        strategy = ComputedMappingStrategy(compute_weight)
        
        result = strategy.map_field(metadata, context)
        assert result == "10.00"
    
    def test_computed_mapping_with_context(self):
        """Test computed mapping that uses context."""
        def compute_with_context(metadata, context):
            return f"{metadata.title}_{context.field_name}"
        
        metadata = CodexMetadata(title="Test Book")
        context = MappingContext("computed_field", [], {})
        strategy = ComputedMappingStrategy(compute_with_context)
        
        result = strategy.map_field(metadata, context)
        assert result == "Test Book_computed_field"
    
    def test_computed_mapping_exception_handling(self):
        """Test computed mapping handles exceptions gracefully."""
        def failing_computation(metadata, context):
            raise ValueError("Computation failed")
        
        metadata = CodexMetadata()
        context = MappingContext("test_field", [], {})
        strategy = ComputedMappingStrategy(failing_computation)
        
        result = strategy.map_field(metadata, context)
        assert result == ""


class TestDefaultMappingStrategy:
    """Test the DefaultMappingStrategy class."""
    
    def test_default_mapping_returns_default(self):
        """Test that default mapping always returns the default value."""
        metadata = CodexMetadata(title="Any Title")
        context = MappingContext("any_field", [], {})
        strategy = DefaultMappingStrategy("Fixed Value")
        
        result = strategy.map_field(metadata, context)
        assert result == "Fixed Value"
    
    def test_default_mapping_empty_string(self):
        """Test default mapping with empty string."""
        metadata = CodexMetadata()
        context = MappingContext("test_field", [], {})
        strategy = DefaultMappingStrategy("")
        
        result = strategy.map_field(metadata, context)
        assert result == ""


class TestConditionalMappingStrategy:
    """Test the ConditionalMappingStrategy class."""
    
    def test_conditional_mapping_true_condition(self):
        """Test conditional mapping when condition is True."""
        def condition(metadata, context):
            return metadata.page_count > 100
        
        true_strategy = DefaultMappingStrategy("Large Book")
        false_strategy = DefaultMappingStrategy("Small Book")
        
        metadata = CodexMetadata(page_count=150)
        context = MappingContext("book_size", [], {})
        strategy = ConditionalMappingStrategy(condition, true_strategy, false_strategy)
        
        result = strategy.map_field(metadata, context)
        assert result == "Large Book"
    
    def test_conditional_mapping_false_condition(self):
        """Test conditional mapping when condition is False."""
        def condition(metadata, context):
            return metadata.page_count > 100
        
        true_strategy = DefaultMappingStrategy("Large Book")
        false_strategy = DefaultMappingStrategy("Small Book")
        
        metadata = CodexMetadata(page_count=50)
        context = MappingContext("book_size", [], {})
        strategy = ConditionalMappingStrategy(condition, true_strategy, false_strategy)
        
        result = strategy.map_field(metadata, context)
        assert result == "Small Book"
    
    def test_conditional_mapping_exception_handling(self):
        """Test conditional mapping handles exceptions in condition."""
        def failing_condition(metadata, context):
            raise ValueError("Condition failed")
        
        true_strategy = DefaultMappingStrategy("True")
        false_strategy = DefaultMappingStrategy("False")
        
        metadata = CodexMetadata()
        context = MappingContext("test_field", [], {})
        strategy = ConditionalMappingStrategy(failing_condition, true_strategy, false_strategy)
        
        result = strategy.map_field(metadata, context)
        assert result == ""


class TestLLMCompletionStrategy:
    """Test the LLMCompletionStrategy class."""
    
    def test_llm_completion_strategy_initialization(self):
        """Test LLM completion strategy can be initialized."""
        llm_caller = Mock()
        prompt_manager = Mock()
        
        strategy = LLMCompletionStrategy(
            llm_caller=llm_caller,
            prompt_manager=prompt_manager,
            prompt_key="test_prompt",
            fallback_value="fallback"
        )
        
        assert strategy.llm_caller == llm_caller
        assert strategy.prompt_manager == prompt_manager
        assert strategy.prompt_key == "test_prompt"
        assert strategy.fallback_value == "fallback"
    
    def test_llm_completion_returns_fallback(self):
        """Test LLM completion returns fallback value (placeholder implementation)."""
        llm_caller = Mock()
        prompt_manager = Mock()
        
        metadata = CodexMetadata()
        context = MappingContext("test_field", [], {})
        strategy = LLMCompletionStrategy(
            llm_caller=llm_caller,
            prompt_manager=prompt_manager,
            prompt_key="test_prompt",
            fallback_value="fallback_value"
        )
        
        result = strategy.map_field(metadata, context)
        assert result == "fallback_value"


if __name__ == "__main__":
    pytest.main([__file__])

class TestFieldMappingRegistry:
    """Test the FieldMappingRegistry class."""
    
    def test_registry_initialization(self):
        """Test that registry initializes empty."""
        registry = FieldMappingRegistry()
        
        assert len(registry.get_registered_fields()) == 0
        assert registry.get_registry_stats()["total_strategies"] == 0
    
    def test_register_strategy(self):
        """Test registering a strategy."""
        registry = FieldMappingRegistry()
        strategy = DirectMappingStrategy("title")
        
        registry.register_strategy("Title", strategy)
        
        assert registry.has_strategy("Title")
        assert registry.get_strategy("Title") == strategy
        assert "Title" in registry.get_registered_fields()
    
    def test_register_multiple_strategies(self):
        """Test registering multiple strategies."""
        registry = FieldMappingRegistry()
        strategy1 = DirectMappingStrategy("title")
        strategy2 = DefaultMappingStrategy("Author")
        
        registry.register_strategy("Title", strategy1)
        registry.register_strategy("Author", strategy2)
        
        assert len(registry.get_registered_fields()) == 2
        assert registry.get_strategy("Title") == strategy1
        assert registry.get_strategy("Author") == strategy2
    
    def test_get_nonexistent_strategy(self):
        """Test getting strategy that doesn't exist."""
        registry = FieldMappingRegistry()
        
        assert registry.get_strategy("NonExistent") is None
        assert not registry.has_strategy("NonExistent")
    
    def test_apply_mappings_with_strategies(self):
        """Test applying mappings with registered strategies."""
        registry = FieldMappingRegistry()
        registry.register_strategy("Title", DirectMappingStrategy("title"))
        registry.register_strategy("Author", DefaultMappingStrategy("Test Author"))
        
        metadata = CodexMetadata(title="Test Book")
        headers = ["Title", "Author"]
        
        results = registry.apply_mappings(metadata, headers)
        
        assert results["Title"] == "Test Book"
        assert results["Author"] == "Test Author"
    
    def test_apply_mappings_without_strategies(self):
        """Test applying mappings for fields without strategies."""
        registry = FieldMappingRegistry()
        
        metadata = CodexMetadata(title="Test Book")
        headers = ["Title", "Author"]
        
        results = registry.apply_mappings(metadata, headers)
        
        assert results["Title"] == ""
        assert results["Author"] == ""
    
    def test_apply_mappings_ordered(self):
        """Test applying mappings and getting ordered results."""
        registry = FieldMappingRegistry()
        registry.register_strategy("Title", DirectMappingStrategy("title"))
        registry.register_strategy("Author", DefaultMappingStrategy("Test Author"))
        
        metadata = CodexMetadata(title="Test Book")
        headers = ["Author", "Title"]  # Different order
        
        results = registry.apply_mappings_ordered(metadata, headers)
        
        assert results == ["Test Author", "Test Book"]
    
    def test_clear_registry(self):
        """Test clearing the registry."""
        registry = FieldMappingRegistry()
        registry.register_strategy("Title", DirectMappingStrategy("title"))
        
        assert len(registry.get_registered_fields()) == 1
        
        registry.clear_registry()
        
        assert len(registry.get_registered_fields()) == 0
        assert not registry.has_strategy("Title")
    
    def test_get_registry_stats(self):
        """Test getting registry statistics."""
        registry = FieldMappingRegistry()
        registry.register_strategy("Title", DirectMappingStrategy("title"))
        registry.register_strategy("Author", DefaultMappingStrategy("Test Author"))
        registry.register_strategy("Pages", DirectMappingStrategy("page_count"))
        
        stats = registry.get_registry_stats()
        
        assert stats["total_strategies"] == 3
        assert stats["registered_fields"] == 3
        assert stats["strategy_types"]["DirectMappingStrategy"] == 2
        assert stats["strategy_types"]["DefaultMappingStrategy"] == 1
    
    def test_field_order_preservation(self):
        """Test that field registration order is preserved."""
        registry = FieldMappingRegistry()
        
        registry.register_strategy("Third", DirectMappingStrategy("field3"))
        registry.register_strategy("First", DirectMappingStrategy("field1"))
        registry.register_strategy("Second", DirectMappingStrategy("field2"))
        
        fields = registry.get_registered_fields()
        assert fields == ["Third", "First", "Second"]
    
    def test_strategy_replacement(self):
        """Test replacing an existing strategy."""
        registry = FieldMappingRegistry()
        strategy1 = DirectMappingStrategy("title")
        strategy2 = DefaultMappingStrategy("New Title")
        
        registry.register_strategy("Title", strategy1)
        registry.register_strategy("Title", strategy2)  # Replace
        
        assert registry.get_strategy("Title") == strategy2
        assert len(registry.get_registered_fields()) == 1  # Should not duplicate


class TestDefaultLSIRegistry:
    """Test the create_default_lsi_registry function."""
    
    def test_default_registry_creation(self):
        """Test that default registry is created with expected strategies."""
        registry = create_default_lsi_registry()
        
        # Check that basic fields are registered
        assert registry.has_strategy("ISBN or SKU")
        assert registry.has_strategy("Title")
        assert registry.has_strategy("Publisher")
        assert registry.has_strategy("Contributor One")
        
        # Check that we have a reasonable number of strategies
        stats = registry.get_registry_stats()
        assert stats["total_strategies"] > 20  # Should have many default strategies
    
    def test_default_registry_basic_mapping(self):
        """Test basic mapping with default registry."""
        registry = create_default_lsi_registry()
        
        metadata = CodexMetadata(
            title="Test Book",
            isbn13="9781234567890",
            author="Test Author",
            page_count=100
        )
        
        headers = ["Title", "ISBN or SKU", "Contributor One", "Pages"]
        results = registry.apply_mappings(metadata, headers)
        
        assert results["Title"] == "Test Book"
        assert results["ISBN or SKU"] == "9781234567890"
        assert results["Contributor One"] == "Test Author"
        assert results["Pages"] == "100"
    
    def test_default_registry_computed_fields(self):
        """Test computed fields in default registry."""
        registry = create_default_lsi_registry()
        
        metadata = CodexMetadata(
            keywords="#Bibliographic Key Phrases science;technology;future",
            list_price_usd=24.99
        )
        
        headers = ["Keywords", "US Suggested List Price"]
        results = registry.apply_mappings(metadata, headers)
        
        assert results["Keywords"] == "science; technology; future"
        assert results["US Suggested List Price"] == "$24.99"


class TestComputedFunctions:
    """Test the computed strategy functions."""
    
    def test_format_keywords_computed(self):
        """Test the keywords formatting function."""
        from codexes.modules.distribution.field_mapping import _format_keywords_computed
        
        metadata = CodexMetadata(keywords="#Bibliographic Key Phrases science;technology;future")
        context = MappingContext("Keywords", [], {})
        
        result = _format_keywords_computed(metadata, context)
        assert result == "science; technology; future"
    
    def test_format_keywords_computed_empty(self):
        """Test keywords formatting with empty input."""
        from codexes.modules.distribution.field_mapping import _format_keywords_computed
        
        metadata = CodexMetadata(keywords="")
        context = MappingContext("Keywords", [], {})
        
        result = _format_keywords_computed(metadata, context)
        assert result == ""
    
    def test_format_price_computed(self):
        """Test the price formatting function."""
        from codexes.modules.distribution.field_mapping import _format_price_computed
        
        metadata = CodexMetadata(list_price_usd=19.99)
        context = MappingContext("Price", [], {})
        
        result = _format_price_computed(metadata, context)
        assert result == "$19.99"
    
    def test_format_price_computed_default(self):
        """Test price formatting with no price."""
        from codexes.modules.distribution.field_mapping import _format_price_computed
        
        metadata = CodexMetadata(list_price_usd=0)
        context = MappingContext("Price", [], {})
        
        result = _format_price_computed(metadata, context)
        assert result == "$19.99"