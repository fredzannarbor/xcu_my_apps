"""
Code Example Extraction and Documentation Tools for ArXiv Paper Generation

This module provides tools to automatically extract code examples, generate
technical architecture diagrams, and create configuration documentation
from the Codexes Factory codebase.
"""

import ast
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeExample:
    """Represents an extracted code example."""
    file_path: str
    class_name: Optional[str]
    function_name: Optional[str]
    code_snippet: str
    docstring: Optional[str]
    line_start: int
    line_end: int
    complexity_score: int
    dependencies: List[str]


@dataclass
class ArchitectureComponent:
    """Represents a component in the system architecture."""
    name: str
    module_path: str
    component_type: str  # 'class', 'function', 'module'
    dependencies: List[str]
    description: str
    interfaces: List[str]


class CodeExtractor:
    """Extracts code examples and documentation from the codebase."""
    
    def __init__(self, base_path: str = "src/codexes"):
        self.base_path = Path(base_path)
        self.extracted_examples: List[CodeExample] = []
        self.architecture_components: List[ArchitectureComponent] = []
        
    def extract_key_classes(self, target_modules: Optional[List[str]] = None) -> List[CodeExample]:
        """
        Extract key classes and methods from specified modules.
        
        Args:
            target_modules: List of module paths to analyze. If None, analyzes all modules.
            
        Returns:
            List of extracted code examples
        """
        if target_modules is None:
            target_modules = [
                "core/llm_caller.py",
                "core/enhanced_llm_caller.py", 
                "modules/distribution/multi_level_config.py",
                "modules/distribution/field_mapping_registry.py",
                "modules/metadata/codex_metadata.py",
                "modules/prepress/latex_generator.py",
                "modules/covers/cover_generator.py"
            ]
            
        examples = []
        
        for module_path in target_modules:
            full_path = self.base_path / module_path
            if full_path.exists():
                examples.extend(self._extract_from_file(full_path))
                
        self.extracted_examples = examples
        return examples
    
    def _extract_from_file(self, file_path: Path) -> List[CodeExample]:
        """Extract code examples from a single Python file."""
        examples = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    example = self._extract_class_example(node, content, str(file_path))
                    if example:
                        examples.append(example)
                        
                elif isinstance(node, ast.FunctionDef) and not self._is_method(node, tree):
                    example = self._extract_function_example(node, content, str(file_path))
                    if example:
                        examples.append(example)
                        
        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {e}")
            
        return examples
    
    def _extract_class_example(self, node: ast.ClassDef, content: str, file_path: str) -> Optional[CodeExample]:
        """Extract a class definition as a code example."""
        lines = content.split('\n')
        
        # Get class definition with key methods
        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 20
        
        # Find key methods to include
        key_methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name in ['__init__', '__call__', 'process', 'generate', 'validate']:
                    key_methods.append(item)
                    
        # Build code snippet
        snippet_lines = []
        snippet_lines.extend(lines[start_line:min(start_line + 5, len(lines))])  # Class header
        
        for method in key_methods[:2]:  # Include up to 2 key methods
            method_start = method.lineno - 1
            method_end = min(method_start + 10, len(lines))  # Limit method length
            snippet_lines.append("    # ...")
            snippet_lines.extend(lines[method_start:method_end])
            
        code_snippet = '\n'.join(snippet_lines)
        
        return CodeExample(
            file_path=file_path,
            class_name=node.name,
            function_name=None,
            code_snippet=code_snippet,
            docstring=ast.get_docstring(node),
            line_start=start_line + 1,
            line_end=end_line,
            complexity_score=self._calculate_complexity(node),
            dependencies=self._extract_dependencies(content)
        )
    
    def _extract_function_example(self, node: ast.FunctionDef, content: str, file_path: str) -> Optional[CodeExample]:
        """Extract a function definition as a code example."""
        lines = content.split('\n')
        start_line = node.lineno - 1
        end_line = min(node.end_lineno if hasattr(node, 'end_lineno') else start_line + 15, len(lines))
        
        code_snippet = '\n'.join(lines[start_line:end_line])
        
        return CodeExample(
            file_path=file_path,
            class_name=None,
            function_name=node.name,
            code_snippet=code_snippet,
            docstring=ast.get_docstring(node),
            line_start=start_line + 1,
            line_end=end_line,
            complexity_score=self._calculate_complexity(node),
            dependencies=self._extract_dependencies(content)
        )
    
    def _is_method(self, node: ast.FunctionDef, tree: ast.AST) -> bool:
        """Check if a function is a method of a class."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                if node in parent.body:
                    return True
        return False
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate a simple complexity score for a code node."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                complexity += 1
        return complexity
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract import dependencies from file content."""
        dependencies = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                dependencies.append(line)
                
        return dependencies[:5]  # Limit to first 5 imports
    
    def generate_architecture_diagram_data(self) -> Dict[str, Any]:
        """
        Generate data structure for creating architecture diagrams.
        
        Returns:
            Dictionary containing nodes and edges for diagram generation
        """
        nodes = []
        edges = []
        
        # Core modules
        core_modules = [
            {"id": "llm_caller", "label": "LLM Caller", "type": "core", "description": "Handles AI model interactions"},
            {"id": "config_system", "label": "Multi-Level Config", "type": "core", "description": "Hierarchical configuration management"},
            {"id": "metadata", "label": "Metadata System", "type": "core", "description": "Book metadata management"},
            {"id": "prepress", "label": "Prepress Pipeline", "type": "module", "description": "LaTeX and PDF generation"},
            {"id": "distribution", "label": "Distribution", "type": "module", "description": "LSI CSV and distribution formats"},
            {"id": "covers", "label": "Cover Generation", "type": "module", "description": "Automated cover creation"},
            {"id": "ideation", "label": "Ideation System", "type": "module", "description": "AI-assisted content ideation"}
        ]
        
        nodes.extend(core_modules)
        
        # Define relationships
        relationships = [
            ("config_system", "metadata", "configures"),
            ("config_system", "prepress", "configures"),
            ("config_system", "distribution", "configures"),
            ("config_system", "covers", "configures"),
            ("llm_caller", "metadata", "enhances"),
            ("llm_caller", "ideation", "powers"),
            ("llm_caller", "covers", "generates"),
            ("metadata", "prepress", "provides_data"),
            ("metadata", "distribution", "provides_data"),
            ("metadata", "covers", "provides_data"),
            ("prepress", "distribution", "outputs_to")
        ]
        
        for source, target, relationship in relationships:
            edges.append({
                "source": source,
                "target": target,
                "label": relationship,
                "type": "dependency"
            })
            
        return {
            "nodes": nodes,
            "edges": edges,
            "layout": "hierarchical",
            "title": "Codexes Factory Architecture - Xynapse Traces Imprint"
        }
    
    def generate_mermaid_diagram(self) -> str:
        """Generate a Mermaid diagram representation of the architecture."""
        diagram_data = self.generate_architecture_diagram_data()
        
        mermaid = ["graph TD"]
        
        # Add nodes
        for node in diagram_data["nodes"]:
            node_id = node["id"]
            label = node["label"]
            node_type = node["type"]
            
            if node_type == "core":
                mermaid.append(f'    {node_id}["{label}"]:::core')
            else:
                mermaid.append(f'    {node_id}["{label}"]:::module')
        
        # Add edges
        for edge in diagram_data["edges"]:
            source = edge["source"]
            target = edge["target"]
            label = edge["label"]
            mermaid.append(f'    {source} -->|{label}| {target}')
        
        # Add styling
        mermaid.extend([
            "",
            "    classDef core fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
            "    classDef module fill:#f3e5f5,stroke:#4a148c,stroke-width:2px"
        ])
        
        return '\n'.join(mermaid)
    
    def extract_configuration_examples(self, config_path: str = "configs/imprints/xynapse_traces.json") -> Dict[str, Any]:
        """
        Extract and format configuration examples for documentation.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dictionary with formatted configuration examples
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            examples = {
                "basic_imprint_config": {
                    "imprint": config_data.get("imprint"),
                    "publisher": config_data.get("publisher"),
                    "contact_email": config_data.get("contact_email")
                },
                "branding_config": config_data.get("branding", {}),
                "publishing_focus": config_data.get("publishing_focus", {}),
                "default_book_settings": config_data.get("default_book_settings", {}),
                "pricing_defaults": config_data.get("pricing_defaults", {}),
                "distribution_settings": config_data.get("distribution_settings", {}),
                "workflow_settings": config_data.get("workflow_settings", {}),
                "fixes_configuration": config_data.get("fixes_configuration", {})
            }
            
            return examples
            
        except Exception as e:
            logger.error(f"Error extracting configuration examples: {e}")
            return {}
    
    def generate_code_documentation(self) -> Dict[str, Any]:
        """
        Generate comprehensive code documentation for the paper.
        
        Returns:
            Dictionary containing formatted code documentation
        """
        if not self.extracted_examples:
            self.extract_key_classes()
            
        documentation = {
            "architecture_overview": self.generate_architecture_diagram_data(),
            "mermaid_diagram": self.generate_mermaid_diagram(),
            "key_classes": [],
            "configuration_examples": self.extract_configuration_examples(),
            "code_statistics": self._generate_code_statistics()
        }
        
        # Format key classes for documentation
        for example in self.extracted_examples:
            if example.class_name:  # Focus on classes for the paper
                class_doc = {
                    "name": example.class_name,
                    "file_path": example.file_path,
                    "description": example.docstring or f"Core class: {example.class_name}",
                    "code_snippet": self._format_code_snippet(example.code_snippet),
                    "complexity": example.complexity_score,
                    "key_dependencies": example.dependencies[:3]
                }
                documentation["key_classes"].append(class_doc)
        
        return documentation
    
    def _format_code_snippet(self, code: str) -> str:
        """Format code snippet for academic paper inclusion."""
        lines = code.split('\n')
        
        # Remove excessive whitespace and limit length
        formatted_lines = []
        for line in lines[:15]:  # Limit to 15 lines
            if line.strip():  # Skip empty lines
                formatted_lines.append(line)
                
        return '\n'.join(formatted_lines)
    
    def _generate_code_statistics(self) -> Dict[str, Any]:
        """Generate statistics about the codebase for the paper."""
        stats = {
            "total_files_analyzed": 0,
            "total_classes_extracted": 0,
            "total_functions_extracted": 0,
            "average_complexity": 0,
            "key_modules": []
        }
        
        if self.extracted_examples:
            stats["total_files_analyzed"] = len(set(ex.file_path for ex in self.extracted_examples))
            stats["total_classes_extracted"] = len([ex for ex in self.extracted_examples if ex.class_name])
            stats["total_functions_extracted"] = len([ex for ex in self.extracted_examples if ex.function_name])
            
            complexities = [ex.complexity_score for ex in self.extracted_examples]
            stats["average_complexity"] = sum(complexities) / len(complexities) if complexities else 0
            
            # Identify key modules
            module_counts = {}
            for example in self.extracted_examples:
                module = example.file_path.split('/')[-2] if '/' in example.file_path else 'core'
                module_counts[module] = module_counts.get(module, 0) + 1
                
            stats["key_modules"] = sorted(module_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return stats


def main():
    """Main function for testing the code extractor."""
    extractor = CodeExtractor()
    
    # Extract code examples
    examples = extractor.extract_key_classes()
    print(f"Extracted {len(examples)} code examples")
    
    # Generate documentation
    documentation = extractor.generate_code_documentation()
    
    # Save to output directory
    output_dir = Path("output/arxiv_paper/code_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "code_documentation.json", 'w') as f:
        json.dump(documentation, f, indent=2)
    
    with open(output_dir / "architecture_diagram.mmd", 'w') as f:
        f.write(documentation["mermaid_diagram"])
    
    print(f"Documentation saved to {output_dir}")


if __name__ == "__main__":
    main()