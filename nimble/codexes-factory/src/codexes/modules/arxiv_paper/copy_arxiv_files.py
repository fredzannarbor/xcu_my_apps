#!/usr/bin/env python3
"""
Script to copy all needed files from codexes-factory to arxiv-writer package location.
This script identifies and copies the core arxiv paper generation functionality.
"""

import os
import shutil
from pathlib import Path
import json

def copy_arxiv_files():
    """Copy all necessary files for arxiv-writer package."""
    
    # Source and destination paths
    source_root = Path.cwd()  # Current codexes-factory directory
    dest_root = Path("/Users/fred/xcu_my_apps/nimble/arxiv-writer")
    
    print(f"Copying files from {source_root} to {dest_root}")
    
    # Create destination directory if it doesn't exist
    dest_root.mkdir(parents=True, exist_ok=True)
    
    # Files and directories to copy
    copy_map = {
        # Core arxiv paper module
        "src/codexes/modules/arxiv_paper/": "src/arxiv_writer/core/",
        
        # Core LLM functionality
        "src/codexes/core/llm_caller.py": "src/arxiv_writer/llm/caller.py",
        "src/codexes/core/enhanced_llm_caller.py": "src/arxiv_writer/llm/enhanced_caller.py",
        
        # Prompt templates
        "prompts/arxiv_paper_prompts.json": "templates/default_prompts.json",
        
        # Configuration files (examples)
        "configs/llm_monitoring_config.json": "examples/configs/llm_monitoring_config.json",
        "configs/llm_prompt_config.json": "examples/configs/llm_prompt_config.json",
        
        # Example imprint configuration
        "configs/imprints/xynapse_traces.json": "examples/configs/imprints/xynapse_traces.json",
        
        # Requirements and dependencies info
        "requirements.txt": "requirements_reference.txt",
        "pyproject.toml": "pyproject_reference.toml",
    }
    
    # Copy files and directories
    for src_path, dest_path in copy_map.items():
        src_full = source_root / src_path
        dest_full = dest_root / dest_path
        
        if not src_full.exists():
            print(f"⚠️  Source not found: {src_full}")
            continue
            
        # Create destination directory
        dest_full.parent.mkdir(parents=True, exist_ok=True)
        
        if src_full.is_dir():
            print(f"📁 Copying directory: {src_path} -> {dest_path}")
            if dest_full.exists():
                shutil.rmtree(dest_full)
            shutil.copytree(src_full, dest_full)
        else:
            print(f"📄 Copying file: {src_path} -> {dest_path}")
            shutil.copy2(src_full, dest_full)
    
    # Copy additional utility files that might be needed
    utility_files = [
        "generate_paper_sections_7_1.py",
        "generate_paper_sections_7_2.py", 
        "generate_paper_sections_7_3.py",
        "generate_paper_sections_7_4.py",
        "test_arxiv_submission.py",
        "recreate_article.py",
        "final_check.py"
    ]
    
    examples_dir = dest_root / "examples" / "scripts"
    examples_dir.mkdir(parents=True, exist_ok=True)
    
    for util_file in utility_files:
        src_file = source_root / util_file
        if src_file.exists():
            dest_file = examples_dir / util_file
            print(f"📄 Copying utility: {util_file} -> examples/scripts/{util_file}")
            shutil.copy2(src_file, dest_file)
    
    print("✅ File copying completed!")
    return dest_root

if __name__ == "__main__":
    copy_arxiv_files()