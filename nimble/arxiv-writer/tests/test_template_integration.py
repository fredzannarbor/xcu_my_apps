"""
Integration tests for template management system.
"""

import tempfile
import json
from pathlib import Path

from src.arxiv_writer.templates import TemplateManager, PromptTemplate, LatexTemplate


def test_end_to_end_template_workflow():
    """Test complete template workflow from loading to rendering."""
    
    # Create a temporary template file
    template_data = {
        "paper_sections": {
            "abstract": {
                "system_prompt": "You are an expert academic writer.",
                "user_prompt": "Write an abstract for a research paper about {topic} with {word_count} words. This study will explore the topic in detail.",
                "context_variables": ["topic", "word_count"],
                "validation_criteria": {
                    "word_count_range": [10, 50],
                    "must_include_terms": ["research", "study"]
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(template_data, f)
        temp_path = f.name
    
    try:
        # Initialize template manager and load templates
        manager = TemplateManager({'prompts_file': temp_path})
        
        # Verify template was loaded
        assert "abstract" in manager.prompt_templates
        template = manager.get_prompt_template("abstract")
        assert template is not None
        assert template.name == "abstract"
        assert "topic" in template.context_variables
        assert "word_count" in template.context_variables
        
        # Test template validation
        validation_result = manager.validate_template("abstract")
        assert validation_result.is_valid
        
        # Test template rendering
        context = {
            "topic": "artificial intelligence",
            "word_count": "200"
        }
        
        rendered = manager.render_template("abstract", context)
        assert rendered.template_name == "abstract"
        assert "artificial intelligence" in rendered.user_prompt
        assert "200" in rendered.user_prompt
        
        # Test LaTeX template
        latex_template = LatexTemplate(
            name="article",
            content="\\documentclass{article}\n\\title{title}\n\\author{author}\n\\begin{document}\n\\maketitle\n{content}\n\\end{document}",
            template_type="latex"
        )
        
        manager.add_custom_template(latex_template)
        
        latex_context = {
            "title": "My Research Paper",
            "author": "John Doe",
            "content": "This is the paper content."
        }
        
        latex_rendered = manager.render_template("article", latex_context)
        assert "\\title{My Research Paper}" in latex_rendered
        assert "\\author{John Doe}" in latex_rendered
        assert "This is the paper content." in latex_rendered
        
        # Test template info
        info = manager.get_template_info("abstract")
        assert info['name'] == "abstract"
        assert info['type'] == "PromptTemplate"
        assert "topic" in info['context_variables']
        
        # Test listing templates
        templates = manager.list_templates()
        assert "abstract" in templates
        assert "article" in templates
        
    finally:
        Path(temp_path).unlink()


def test_template_error_handling():
    """Test error handling in template system."""
    
    manager = TemplateManager({})
    
    # Test rendering non-existent template
    try:
        manager.render_template("nonexistent", {})
        assert False, "Should have raised TemplateError"
    except Exception as e:
        assert "not found" in str(e)
    
    # Test rendering with missing context
    template = PromptTemplate(
        name="test",
        system_prompt="System",
        user_prompt="User {missing_var}",
        context_variables=["missing_var"]
    )
    
    manager.add_custom_template(template)
    
    try:
        manager.render_template("test", {})
        assert False, "Should have raised TemplateError"
    except Exception as e:
        assert "Missing required context variables" in str(e)


if __name__ == "__main__":
    test_end_to_end_template_workflow()
    test_template_error_handling()
    print("All integration tests passed!")