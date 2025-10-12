#!/usr/bin/env python3
"""
Command Line Content Transformation Tool

Transform CodexObject files from one type to another using the existing transformation engine.

Usage:
    python transform_content.py input.json --target synopsis --output output.json
    python transform_content.py input.json --target outline --approach planning --parameter expand
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project paths
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

try:
    from src.codexes.modules.ideation.core.transformation import ContentTransformer
    from src.codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType, DevelopmentStage
    TRANSFORMATION_ENGINE_AVAILABLE = True
except ImportError:
    print("Warning: Advanced transformation engine not available, using basic transformation")
    TRANSFORMATION_ENGINE_AVAILABLE = False
    from src.codexes.ui.core.simple_codex_object import SimpleCodexObject as CodexObject, CodexObjectType


def load_codex_object(file_path: str) -> CodexObject:
    """Load a CodexObject from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both simple and ideation CodexObject formats
        if TRANSFORMATION_ENGINE_AVAILABLE:
            # Create ideation CodexObject
            obj = CodexObject(
                title=data.get('title', 'Untitled'),
                content=data.get('content', ''),
                genre=data.get('genre', ''),
                target_audience=data.get('target_audience', ''),
                object_type=CodexObjectType(data.get('object_type', 'idea')),
                development_stage=DevelopmentStage.DEVELOPMENT
            )
        else:
            # Create simple CodexObject
            obj = CodexObject(
                title=data.get('title', 'Untitled'),
                content=data.get('content', ''),
                object_type=CodexObjectType(data.get('object_type', 'idea')),
                word_count=data.get('word_count', len(data.get('content', '').split())),
                genre=data.get('genre', ''),
                target_audience=data.get('target_audience', '')
            )
        
        return obj
        
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{file_path}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading CodexObject: {e}")
        sys.exit(1)


def save_codex_object(obj: CodexObject, file_path: str):
    """Save a CodexObject to a JSON file."""
    try:
        # Convert to dictionary
        if TRANSFORMATION_ENGINE_AVAILABLE:
            data = {
                'uuid': obj.uuid,
                'title': obj.title,
                'content': obj.content,
                'object_type': obj.object_type.value,
                'word_count': obj.word_count,
                'genre': obj.genre,
                'target_audience': obj.target_audience,
                'development_stage': obj.development_stage.value,
                'created_timestamp': obj.created_timestamp,
                'modified_timestamp': datetime.now().isoformat()
            }
        else:
            data = {
                'uuid': obj.uuid,
                'title': obj.title,
                'content': obj.content,
                'object_type': obj.object_type.value,
                'word_count': obj.word_count,
                'genre': getattr(obj, 'genre', ''),
                'target_audience': getattr(obj, 'target_audience', ''),
                'created_timestamp': obj.created_timestamp,
                'modified_timestamp': datetime.now().isoformat()
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved transformed object to: {file_path}")
        
    except Exception as e:
        print(f"Error saving CodexObject: {e}")
        sys.exit(1)


def transform_with_engine(source_obj: CodexObject, target_type: CodexObjectType) -> CodexObject:
    """Transform using the advanced transformation engine."""
    try:
        transformer = ContentTransformer()
        result = transformer.transform_content(source_obj, target_type)
        
        if result.success:
            print(f"✅ Transformation successful (confidence: {result.confidence_score:.1%})")
            print(f"📝 Notes: {result.transformation_notes}")
            return result.transformed_object
        else:
            print(f"⚠️ Advanced transformation failed: {result.error_message}")
            print("🔄 Falling back to basic transformation...")
            return transform_basic(source_obj, target_type)
            
    except Exception as e:
        print(f"⚠️ Transformation engine error: {e}")
        print("🔄 Falling back to basic transformation...")
        return transform_basic(source_obj, target_type)


def transform_basic(source_obj: CodexObject, target_type: CodexObjectType) -> CodexObject:
    """Basic transformation (type change only)."""
    try:
        # Create new object with changed type
        transformed_obj = CodexObject(
            title=source_obj.title,
            content=source_obj.content,
            object_type=target_type,
            word_count=source_obj.word_count,
            genre=getattr(source_obj, 'genre', ''),
            target_audience=getattr(source_obj, 'target_audience', '')
        )
        
        print(f"✅ Basic transformation complete (type changed to {target_type.value})")
        return transformed_obj
        
    except Exception as e:
        print(f"❌ Basic transformation error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Transform CodexObject files from one type to another",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transform an idea to a synopsis
  python transform_content.py idea.json --target synopsis --output synopsis.json
  
  # Transform with specific approach and parameter
  python transform_content.py synopsis.json --target outline --approach planning --parameter expand
  
  # Transform and save to default output file
  python transform_content.py draft.json --target manuscript

Available content types:
  idea, logline, summary, synopsis, treatment, outline, draft, manuscript, book_idea, idea_with_fields

Available approaches:
  planning (top-down structured), gardening (bottom-up organic)

Available parameters:
  expand (add detail), condense (summarize), restructure (change format), enhance (improve)
        """
    )
    
    parser.add_argument('input', help='Input JSON file containing CodexObject')
    parser.add_argument('--target', '-t', required=True, 
                       choices=['idea', 'logline', 'summary', 'synopsis', 'treatment', 
                               'outline', 'draft', 'manuscript', 'book_idea', 'idea_with_fields'],
                       help='Target content type')
    parser.add_argument('--output', '-o', help='Output JSON file (default: input_transformed.json)')
    parser.add_argument('--approach', choices=['planning', 'gardening'], 
                       default='planning', help='Transformation approach (default: planning)')
    parser.add_argument('--parameter', choices=['expand', 'condense', 'restructure', 'enhance'],
                       default='expand', help='Transformation parameter (default: expand)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Set default output file if not provided
    if not args.output:
        input_path = Path(args.input)
        args.output = input_path.stem + '_transformed.json'
    
    if args.verbose:
        print(f"🔄 Transforming: {args.input} → {args.output}")
        print(f"📋 Target type: {args.target}")
        print(f"🎯 Approach: {args.approach}")
        print(f"⚙️  Parameter: {args.parameter}")
        print(f"🔧 Engine available: {TRANSFORMATION_ENGINE_AVAILABLE}")
        print()
    
    # Load source object
    print(f"📖 Loading source object from: {args.input}")
    source_obj = load_codex_object(args.input)
    
    print(f"📄 Source: {source_obj.title} ({source_obj.object_type.value}) - {source_obj.word_count} words")
    
    # Convert target type
    target_type = CodexObjectType(args.target)
    
    # Check if transformation is needed
    if source_obj.object_type == target_type:
        print(f"⚠️  Source is already {target_type.value}, no transformation needed")
        if args.verbose:
            print("Copying to output file anyway...")
        save_codex_object(source_obj, args.output)
        return
    
    # Perform transformation
    print(f"🔄 Transforming {source_obj.object_type.value} → {target_type.value}...")
    
    if TRANSFORMATION_ENGINE_AVAILABLE:
        transformed_obj = transform_with_engine(source_obj, target_type)
    else:
        transformed_obj = transform_basic(source_obj, target_type)
    
    # Save result
    save_codex_object(transformed_obj, args.output)
    
    print(f"🎉 Transformation complete!")
    print(f"📊 Result: {transformed_obj.title} ({transformed_obj.object_type.value}) - {transformed_obj.word_count} words")
    
    if args.verbose:
        print(f"\n📝 Content preview:")
        preview = transformed_obj.content[:200] + "..." if len(transformed_obj.content) > 200 else transformed_obj.content
        print(f'"{preview}"')


if __name__ == "__main__":
    main()