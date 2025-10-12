#!/usr/bin/env python3
"""
Module Documentation Generator
Traverses directories, inspects modules, and generates 4 documents for each using Claude Code agents.
"""

import os
import sys
from pathlib import Path
import json
from typing import List, Dict, Any
import importlib.util
import ast

def find_python_modules(root_dir: str, exclude_patterns: List[str] = None) -> List[Dict[str, Any]]:
    """Find all Python modules in directory tree."""
    if exclude_patterns is None:
        exclude_patterns = ['__pycache__', '.git', '.venv', 'node_modules', 'test_', '_test.py']

    modules = []
    root_path = Path(root_dir)

    for py_file in root_path.rglob("*.py"):
        # Skip excluded patterns
        if any(pattern in str(py_file) for pattern in exclude_patterns):
            continue

        # Skip __init__.py files (optional)
        if py_file.name == '__init__.py':
            continue

        module_info = analyze_module_structure(py_file)
        if module_info:
            modules.append(module_info)

    return modules

def analyze_module_structure(file_path: Path) -> Dict[str, Any]:
    """Analyze a Python module's structure using AST."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source)

        module_info = {
            'path': str(file_path),
            'relative_path': str(file_path.relative_to(Path.cwd())),
            'name': file_path.stem,
            'classes': [],
            'functions': [],
            'imports': [],
            'docstring': ast.get_docstring(tree),
            'line_count': len(source.splitlines())
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                module_info['classes'].append({
                    'name': node.name,
                    'line': node.lineno,
                    'docstring': ast.get_docstring(node)
                })
            elif isinstance(node, ast.FunctionDef):
                module_info['functions'].append({
                    'name': node.name,
                    'line': node.lineno,
                    'docstring': ast.get_docstring(node),
                    'is_method': False  # Would need more analysis for this
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_info['imports'].append(alias.name)
                else:
                    module_info['imports'].append(node.module)

        return module_info

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return None

def generate_documentation_for_module(module_info: Dict[str, Any]) -> Dict[str, str]:
    """Generate 4 types of documentation for a module using Claude Code tools."""

    module_path = module_info['relative_path']
    module_name = module_info['name']

    # This would be called from within Claude Code environment
    # where you have access to the Task tool

    documentation_tasks = {
        'api_reference': f"""
Generate comprehensive API reference documentation for the Python module at {module_path}.
Include:
- Module overview and purpose
- All classes with methods and attributes
- All functions with parameters and return types
- Usage examples for main functionality
- Type hints where available

Format as markdown with clear sections.
""",

        'developer_guide': f"""
Create a developer guide for the module at {module_path}.
Include:
- Architecture overview
- Key design patterns used
- How this module fits into the larger system
- Common development tasks and workflows
- Testing approach
- Known limitations or gotchas

Format as markdown suitable for developers working on this code.
""",

        'user_tutorial': f"""
Write a user-friendly tutorial for the module at {module_path}.
Include:
- What problems this module solves
- Step-by-step usage examples
- Common use cases with code samples
- Troubleshooting guide
- Best practices for usage

Format as markdown aimed at end users, not developers.
""",

        'integration_guide': f"""
Create an integration guide for the module at {module_path}.
Include:
- How to integrate with other modules/systems
- Dependencies and requirements
- Configuration options
- Common integration patterns
- Migration guide (if applicable)
- Performance considerations

Format as markdown for system integrators.
"""
    }

    return documentation_tasks

def main():
    """Main documentation generation workflow."""

    # Configuration
    ROOT_DIR = "src/"  # Adjust as needed
    OUTPUT_DIR = "docs/modules/"

    print("🔍 Scanning for Python modules...")
    modules = find_python_modules(ROOT_DIR)
    print(f"Found {len(modules)} modules to document")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate module inventory
    with open(f"{OUTPUT_DIR}/module_inventory.json", 'w') as f:
        json.dump(modules, f, indent=2)

    print("📝 Module inventory saved to module_inventory.json")

    # This is where you'd use the Task tool in Claude Code environment
    print("📚 To generate documentation, run this script within Claude Code environment")
    print("    where you have access to the Task tool for calling documentation agents")

    # Example of how you'd structure the Task tool calls:
    for module in modules[:3]:  # Limit for demo
        module_name = module['name']
        print(f"\n🔄 Would generate docs for: {module_name}")

        tasks = generate_documentation_for_module(module)
        for doc_type, prompt in tasks.items():
            print(f"  📄 {doc_type}: {len(prompt)} chars")

if __name__ == "__main__":
    main()