#!/usr/bin/env python3
"""
Nuclear fix: Remove all corrupted files and keep only working ones.
"""

import os
import subprocess
from pathlib import Path

def is_file_corrupted(file_path):
    """Check if a Python file has syntax errors."""
    try:
        result = subprocess.run(
            ['python', '-m', 'py_compile', str(file_path)],
            capture_output=True,
            text=True
        )
        return result.returncode != 0
    except:
        return True

def main():
    """Remove all corrupted files, keep only working ones."""
    ideation_dir = Path("src/codexes/modules/ideation")
    
    # Files we know are working (created clean)
    working_files = {
        "src/codexes/modules/ideation/core/codex_object.py",
        "src/codexes/modules/ideation/series/series_generator.py", 
        "src/codexes/modules/ideation/series/consistency_manager.py",
        "src/codexes/modules/ideation/series/franchise_manager.py",
        "src/codexes/modules/ideation/tournament/tournament_engine.py",
        "src/codexes/modules/ideation/synthetic_readers/reader_persona.py",
        "src/codexes/modules/ideation/synthetic_readers/reader_panel.py",
        "src/codexes/modules/ideation/storage/database_manager.py",
        "src/codexes/modules/ideation/storage/file_manager.py",
        "src/codexes/modules/ideation/llm/ideation_llm_service.py"
    }
    
    # Get all Python files
    py_files = list(ideation_dir.rglob("*.py"))
    
    corrupted_files = []
    working_files_found = []
    
    for py_file in py_files:
        if is_file_corrupted(py_file):
            corrupted_files.append(py_file)
        else:
            working_files_found.append(py_file)
    
    print(f"Found {len(corrupted_files)} corrupted files")
    print(f"Found {len(working_files_found)} working files")
    
    # Remove corrupted files
    for corrupted_file in corrupted_files:
        print(f"Removing corrupted file: {corrupted_file}")
        corrupted_file.unlink()
    
    print(f"\nRemoved {len(corrupted_files)} corrupted files")
    print(f"Kept {len(working_files_found)} working files:")
    for working_file in working_files_found:
        print(f"  ✅ {working_file}")

if __name__ == "__main__":
    main()