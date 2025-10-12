
#!/usr/bin/env python3
"""
Script to assemble JSON document from .kiro/specs directories
organized by ascending date of last modification.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import argparse


def get_directory_modification_time(directory_path):
    """
    Get the last modification time of a directory based on the most recently
    modified file within it.
    """
    latest_time = os.path.getmtime(directory_path)
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_time = os.path.getmtime(file_path)
                if file_time > latest_time:
                    latest_time = file_time
            except OSError:
                # Skip files that can't be accessed
                continue
    
    return latest_time


def read_spec_directory(directory_path):
    """
    Read and analyze a spec directory to extract tasks, design, and requirements.
    """
    spec_data = {
        "tasks": [],
        "design": [],
        "requirements": []
    }
    
    directory_name = directory_path.name
    
    # Walk through all files in the directory
    for file_path in directory_path.rglob('*'):
        if file_path.is_file() and not file_path.name.startswith('.'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if content:
                    file_info = {
                        "file": str(file_path.relative_to(directory_path)),
                        "content": content[:500],  # Truncate long content
                        "full_content": content,
                        "size": len(content),
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    }
                    
                    # Categorize based on file name or content patterns
                    file_name_lower = file_path.name.lower()
                    content_lower = content.lower()
                    
                    if any(keyword in file_name_lower for keyword in ['task', 'todo', 'action', 'step']):
                        spec_data["tasks"].append(file_info)
                    elif any(keyword in file_name_lower for keyword in ['design', 'architecture', 'spec', 'plan']):
                        spec_data["design"].append(file_info)
                    elif any(keyword in file_name_lower for keyword in ['requirement', 'req', 'criteria', 'must']):
                        spec_data["requirements"].append(file_info)
                    elif any(keyword in content_lower[:200] for keyword in ['todo', 'task', 'action item', '- [ ]']):
                        spec_data["tasks"].append(file_info)
                    elif any(keyword in content_lower[:200] for keyword in ['design', 'architecture', 'specification']):
                        spec_data["design"].append(file_info)
                    elif any(keyword in content_lower[:200] for keyword in ['requirement', 'must', 'shall', 'should']):
                        spec_data["requirements"].append(file_info)
                    else:
                        # Default to design if unclear
                        spec_data["design"].append(file_info)
                        
            except (UnicodeDecodeError, PermissionError, OSError) as e:
                # Skip files that can't be read
                print(f"Warning: Could not read {file_path}: {e}")
                continue
    
    return spec_data


def assemble_specs_json(specs_dir=".kiro/specs", output_file=None, verbose=False):
    """
    Main function to assemble the specs JSON document.
    """
    specs_path = Path(specs_dir)
    
    if not specs_path.exists():
        raise FileNotFoundError(f"Specs directory not found: {specs_dir}")
    
    # Get all spec directories and sort by modification time
    spec_directories = []
    
    for item in specs_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            mod_time = get_directory_modification_time(item)
            spec_directories.append((mod_time, item))
    
    # Sort by modification time (ascending - earliest first)
    spec_directories.sort(key=lambda x: x[0])
    
    # Assemble the final JSON document
    final_document = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_specs": len(spec_directories),
            "source_directory": str(specs_path.absolute()),
            "processing_order": "ascending_modification_time"
        },
        "tasks": [],
        "design": [],
        "requirements": []
    }
    
    # Process each directory in chronological order
    for mod_time, directory in spec_directories:
        if verbose:
            print(f"Processing: {directory.name} (modified: {datetime.fromtimestamp(mod_time).isoformat()})")
        
        spec_data = read_spec_directory(directory)
        
        # Add directory metadata to each entry
        dir_metadata = {
            "spec_directory": directory.name,
            "directory_modified": datetime.fromtimestamp(mod_time).isoformat()
        }
        
        # Merge the data, adding directory context
        for task in spec_data["tasks"]:
            task.update(dir_metadata)
            final_document["tasks"].append(task)
        
        for design in spec_data["design"]:
            design.update(dir_metadata)
            final_document["design"].append(design)
        
        for requirement in spec_data["requirements"]:
            requirement.update(dir_metadata)
            final_document["requirements"].append(requirement)
    
    # Summary statistics
    final_document["metadata"]["summary"] = {
        "total_tasks": len(final_document["tasks"]),
        "total_design_items": len(final_document["design"]),
        "total_requirements": len(final_document["requirements"]),
        "directories_processed": [d.name for _, d in spec_directories]
    }
    
    if verbose:
        print(f"\nSummary:")
        print(f"- Processed {len(spec_directories)} spec directories")
        print(f"- Found {len(final_document['tasks'])} tasks")
        print(f"- Found {len(final_document['design'])} design items")  
        print(f"- Found {len(final_document['requirements'])} requirements")
    
    # Write output
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_document, f, indent=2, ensure_ascii=False)
        if verbose:
            print(f"\nOutput written to: {output_file}")
    else:
        print(json.dumps(final_document, indent=2, ensure_ascii=False))
    
    return final_document


def main():
    parser = argparse.ArgumentParser(description="Assemble JSON document from .kiro/specs directories")
    parser.add_argument("--specs-dir", default=".kiro/specs", help="Path to specs directory")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        assemble_specs_json(
            specs_dir=args.specs_dir,
            output_file=args.output,
            verbose=args.verbose
        )
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
