#!/usr/bin/env python3
"""
Batch Content Transformation CLI Tool

Command line interface for batch transformation of CodexObjects with history tracking,
quality assessment, and rollback capabilities.

Usage:
    # Single file transformation
    python batch_transform_cli.py single input.json --target synopsis --output output.json
    
    # Batch transformation from directory
    python batch_transform_cli.py batch data/ --target outline --output-dir results/
    
    # Batch transformation with quality assessment
    python batch_transform_cli.py batch *.json --target synopsis --quality --parallel
    
    # History and rollback operations
    python batch_transform_cli.py history --list
    python batch_transform_cli.py rollback --snapshot snapshot_id
"""

import argparse
import json
import sys
import glob
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project paths
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

try:
    from src.codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType, DevelopmentStage
    from src.codexes.modules.ideation.core.transformation import ContentTransformer
    IDEATION_ENGINE_AVAILABLE = True
except ImportError:
    print("Warning: Ideation engine not available, using basic transformation")
    IDEATION_ENGINE_AVAILABLE = False
    # Fallback to simple objects
    from src.codexes.ui.core.simple_codex_object import SimpleCodexObject as CodexObject, CodexObjectType


class BatchTransformationCLI:
    """Command line interface for batch content transformation."""
    
    def __init__(self):
        self.history_file = Path("transformation_history.json")
        self.snapshots_dir = Path("transformation_snapshots")
        self.snapshots_dir.mkdir(exist_ok=True)
        
        # Transformation options
        self.available_types = [
            'idea', 'logline', 'summary', 'synopsis', 'treatment', 
            'outline', 'detailed_outline', 'draft', 'manuscript', 'series'
        ]
        
        self.approaches = {
            'planning': 'Top-down structured approach',
            'gardening': 'Bottom-up organic approach'
        }
        
        self.parameters = {
            'expand': 'Add detail and depth',
            'condense': 'Summarize and focus',
            'restructure': 'Change format/structure',
            'enhance': 'Improve existing content'
        }
    
    def load_codex_object(self, file_path: str) -> Optional[CodexObject]:
        """Load a CodexObject from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both simple and ideation CodexObject formats
            if IDEATION_ENGINE_AVAILABLE:
                obj = CodexObject(
                    title=data.get('title', 'Untitled'),
                    content=data.get('content', ''),
                    genre=data.get('genre', ''),
                    target_audience=data.get('target_audience', ''),
                    object_type=CodexObjectType(data.get('object_type', 'idea')),
                    development_stage=DevelopmentStage.DEVELOPMENT
                )
            else:
                obj = CodexObject(
                    title=data.get('title', 'Untitled'),
                    content=data.get('content', ''),
                    object_type=CodexObjectType(data.get('object_type', 'idea')),
                    word_count=data.get('word_count', len(data.get('content', '').split())),
                    genre=data.get('genre', ''),
                    target_audience=data.get('target_audience', '')
                )
            
            return obj
            
        except Exception as e:
            print(f"❌ Error loading {file_path}: {e}")
            return None
    
    def save_codex_object(self, obj: CodexObject, file_path: str) -> bool:
        """Save a CodexObject to a JSON file."""
        try:
            # Convert to dictionary
            if IDEATION_ENGINE_AVAILABLE:
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
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving {file_path}: {e}")
            return False
    
    def transform_single_object(self, source_obj: CodexObject, target_type: CodexObjectType,
                              approach: str = 'planning', parameter: str = 'expand') -> Optional[CodexObject]:
        """Transform a single CodexObject."""
        try:
            if IDEATION_ENGINE_AVAILABLE:
                # Use advanced transformation engine
                transformer = ContentTransformer()
                result = transformer.transform_content(source_obj, target_type)
                
                if result.success:
                    return result.transformed_object
                else:
                    print(f"⚠️ Advanced transformation failed: {result.error_message}")
                    return self._basic_transform(source_obj, target_type)
            else:
                # Use basic transformation
                return self._basic_transform(source_obj, target_type)
                
        except Exception as e:
            print(f"❌ Transformation error: {e}")
            return None
    
    def _basic_transform(self, source_obj: CodexObject, target_type: CodexObjectType) -> CodexObject:
        """Basic transformation (type change only)."""
        if IDEATION_ENGINE_AVAILABLE:
            transformed_obj = CodexObject(
                title=source_obj.title,
                content=source_obj.content,
                object_type=target_type,
                genre=source_obj.genre,
                target_audience=source_obj.target_audience,
                development_stage=DevelopmentStage.DEVELOPMENT
            )
        else:
            transformed_obj = CodexObject(
                title=source_obj.title,
                content=source_obj.content,
                object_type=target_type,
                word_count=source_obj.word_count,
                genre=getattr(source_obj, 'genre', ''),
                target_audience=getattr(source_obj, 'target_audience', '')
            )
        
        return transformed_obj
    
    def assess_transformation_quality(self, source_obj: CodexObject, transformed_obj: CodexObject) -> Dict[str, float]:
        """Assess the quality of a transformation."""
        quality_metrics = {}
        
        try:
            # Content length comparison
            source_words = source_obj.word_count
            transformed_words = transformed_obj.word_count
            
            if source_words > 0:
                length_ratio = transformed_words / source_words
                quality_metrics['length_ratio'] = length_ratio
                
                # Score based on expected length change
                if 0.8 <= length_ratio <= 2.0:
                    quality_metrics['length_score'] = 0.9
                elif 0.5 <= length_ratio <= 3.0:
                    quality_metrics['length_score'] = 0.7
                else:
                    quality_metrics['length_score'] = 0.4
            else:
                quality_metrics['length_score'] = 0.5
            
            # Content preservation (simple heuristic)
            source_words_set = set(source_obj.content.lower().split())
            transformed_words_set = set(transformed_obj.content.lower().split())
            
            if source_words_set:
                overlap_ratio = len(source_words_set.intersection(transformed_words_set)) / len(source_words_set)
                quality_metrics['content_preservation'] = overlap_ratio
                
                if overlap_ratio >= 0.3:
                    quality_metrics['preservation_score'] = 0.9
                elif overlap_ratio >= 0.1:
                    quality_metrics['preservation_score'] = 0.7
                else:
                    quality_metrics['preservation_score'] = 0.4
            else:
                quality_metrics['preservation_score'] = 0.5
            
            # Type appropriateness
            type_score = self._assess_type_appropriateness(transformed_obj)
            quality_metrics['type_appropriateness'] = type_score
            
            # Overall quality score
            overall_score = (
                quality_metrics.get('length_score', 0.5) * 0.3 +
                quality_metrics.get('preservation_score', 0.5) * 0.4 +
                quality_metrics.get('type_appropriateness', 0.5) * 0.3
            )
            quality_metrics['overall_score'] = overall_score
            
        except Exception as e:
            print(f"⚠️ Quality assessment error: {e}")
            quality_metrics = {'overall_score': 0.5, 'error': str(e)}
        
        return quality_metrics
    
    def _assess_type_appropriateness(self, obj: CodexObject) -> float:
        """Assess if content is appropriate for its assigned type."""
        word_count = obj.word_count
        
        # Simple heuristics based on content type expectations
        if obj.object_type == CodexObjectType.IDEA:
            return 0.9 if 10 <= word_count <= 200 else 0.6
        elif obj.object_type == CodexObjectType.LOGLINE:
            return 0.9 if 10 <= word_count <= 50 else 0.6
        elif obj.object_type == CodexObjectType.SYNOPSIS:
            return 0.9 if 100 <= word_count <= 1000 else 0.6
        elif obj.object_type == CodexObjectType.OUTLINE:
            return 0.9 if 200 <= word_count <= 2000 else 0.6
        elif obj.object_type == CodexObjectType.DRAFT:
            return 0.9 if word_count >= 500 else 0.6
        elif obj.object_type == CodexObjectType.MANUSCRIPT:
            return 0.9 if word_count >= 1000 else 0.6
        else:
            return 0.7
    
    def create_snapshot(self, objects: List[CodexObject], description: str = "") -> str:
        """Create a rollback snapshot of objects."""
        snapshot_id = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        snapshot_data = {
            'id': snapshot_id,
            'timestamp': datetime.now().isoformat(),
            'description': description,
            'objects': []
        }
        
        for obj in objects:
            obj_data = {
                'uuid': obj.uuid,
                'title': obj.title,
                'content': obj.content,
                'object_type': obj.object_type.value,
                'word_count': obj.word_count,
                'genre': getattr(obj, 'genre', ''),
                'target_audience': getattr(obj, 'target_audience', '')
            }
            snapshot_data['objects'].append(obj_data)
        
        # Save snapshot
        snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
        
        return snapshot_id
    
    def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Load a snapshot by ID."""
        try:
            snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading snapshot {snapshot_id}: {e}")
            return None
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all available snapshots."""
        snapshots = []
        
        for snapshot_file in self.snapshots_dir.glob("*.json"):
            try:
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    snapshot_data = json.load(f)
                    snapshots.append(snapshot_data)
            except Exception as e:
                print(f"⚠️ Error reading snapshot {snapshot_file}: {e}")
        
        # Sort by timestamp
        snapshots.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return snapshots
    
    def save_history_entry(self, entry: Dict[str, Any]):
        """Save a transformation history entry."""
        try:
            # Load existing history
            history = []
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # Add new entry
            history.append(entry)
            
            # Keep only last 1000 entries
            if len(history) > 1000:
                history = history[-1000:]
            
            # Save updated history
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ Error saving history: {e}")
    
    def load_history(self) -> List[Dict[str, Any]]:
        """Load transformation history."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"❌ Error loading history: {e}")
            return []
    
    def cmd_single_transform(self, args):
        """Handle single file transformation command."""
        print(f"🔄 Single Transformation: {args.input} → {args.target}")
        
        # Load source object
        source_obj = self.load_codex_object(args.input)
        if not source_obj:
            return 1
        
        print(f"📄 Source: {source_obj.title} ({source_obj.object_type.value}) - {source_obj.word_count} words")
        
        # Check if transformation needed
        target_type = CodexObjectType(args.target)
        if source_obj.object_type == target_type:
            print(f"⚠️ Source is already {target_type.value}, no transformation needed")
            return 0
        
        # Create snapshot if requested
        snapshot_id = None
        if args.snapshot:
            snapshot_id = self.create_snapshot([source_obj], f"Before transforming {args.input}")
            print(f"📸 Created snapshot: {snapshot_id}")
        
        # Transform
        print(f"🔄 Transforming {source_obj.object_type.value} → {target_type.value}...")
        transformed_obj = self.transform_single_object(source_obj, target_type, args.approach, args.parameter)
        
        if not transformed_obj:
            print("❌ Transformation failed")
            return 1
        
        # Assess quality if requested
        quality_score = None
        if args.quality:
            quality_score = self.assess_transformation_quality(source_obj, transformed_obj)
            print(f"📊 Quality Score: {quality_score['overall_score']:.1%}")
            
            if args.verbose:
                print("📈 Quality Details:")
                for metric, value in quality_score.items():
                    if metric != 'overall_score' and isinstance(value, (int, float)):
                        print(f"  • {metric.replace('_', ' ').title()}: {value:.2f}")
        
        # Save result
        output_path = args.output or f"{Path(args.input).stem}_transformed.json"
        if self.save_codex_object(transformed_obj, output_path):
            print(f"✅ Saved to: {output_path}")
        else:
            return 1
        
        # Save history entry
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'single',
            'source_file': args.input,
            'output_file': output_path,
            'source_type': source_obj.object_type.value,
            'target_type': target_type.value,
            'source_title': source_obj.title,
            'result_title': transformed_obj.title,
            'approach': args.approach,
            'parameter': args.parameter,
            'success': True,
            'snapshot_id': snapshot_id,
            'quality_score': quality_score.get('overall_score') if quality_score else None
        }
        self.save_history_entry(history_entry)
        
        print(f"🎉 Transformation complete!")
        return 0
    
    def cmd_batch_transform(self, args):
        """Handle batch transformation command."""
        print(f"📦 Batch Transformation: {args.input_pattern} → {args.target}")
        
        # Collect input files
        input_files = []
        if os.path.isdir(args.input_pattern):
            # Directory - find all JSON files
            input_files = list(Path(args.input_pattern).glob("*.json"))
        else:
            # Pattern - use glob
            input_files = [Path(f) for f in glob.glob(args.input_pattern)]
        
        if not input_files:
            print(f"❌ No files found matching: {args.input_pattern}")
            return 1
        
        print(f"📚 Found {len(input_files)} files to process")
        
        # Load all objects
        source_objects = []
        for file_path in input_files:
            obj = self.load_codex_object(str(file_path))
            if obj:
                source_objects.append((obj, file_path))
        
        if not source_objects:
            print("❌ No valid objects loaded")
            return 1
        
        print(f"✅ Loaded {len(source_objects)} objects")
        
        # Create snapshot if requested
        snapshot_id = None
        if args.snapshot:
            objects_only = [obj for obj, _ in source_objects]
            snapshot_id = self.create_snapshot(objects_only, f"Before batch transform to {args.target}")
            print(f"📸 Created snapshot: {snapshot_id}")
        
        # Setup output directory
        output_dir = Path(args.output_dir) if args.output_dir else Path("batch_output")
        output_dir.mkdir(exist_ok=True)
        
        # Transform objects
        target_type = CodexObjectType(args.target)
        results = []
        
        if args.parallel and len(source_objects) > 1:
            results = self._batch_transform_parallel(source_objects, target_type, args, output_dir)
        else:
            results = self._batch_transform_sequential(source_objects, target_type, args, output_dir)
        
        # Generate summary
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print(f"\n🎉 Batch Transformation Complete!")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {(successful/len(results)*100):.1f}%")
        
        if args.quality:
            quality_scores = [r['quality_score'] for r in results if r.get('quality_score')]
            if quality_scores:
                avg_quality = sum(quality_scores) / len(quality_scores)
                print(f"📈 Average Quality: {avg_quality:.1%}")
        
        # Save batch history entry
        batch_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'batch',
            'input_pattern': args.input_pattern,
            'target_type': args.target,
            'total_files': len(source_objects),
            'successful': successful,
            'failed': failed,
            'approach': args.approach,
            'parameter': args.parameter,
            'parallel': args.parallel,
            'quality_enabled': args.quality,
            'snapshot_id': snapshot_id,
            'output_dir': str(output_dir),
            'results': results
        }
        self.save_history_entry(batch_entry)
        
        return 0 if failed == 0 else 1
    
    def _batch_transform_sequential(self, source_objects, target_type, args, output_dir):
        """Process batch transformation sequentially."""
        results = []
        total = len(source_objects)
        
        for i, (source_obj, input_path) in enumerate(source_objects):
            print(f"🔄 Processing {i+1}/{total}: {source_obj.title}")
            
            # Transform
            transformed_obj = self.transform_single_object(source_obj, target_type, args.approach, args.parameter)
            
            if transformed_obj:
                # Assess quality if requested
                quality_score = None
                if args.quality:
                    quality_metrics = self.assess_transformation_quality(source_obj, transformed_obj)
                    quality_score = quality_metrics['overall_score']
                
                # Save result
                output_path = output_dir / f"{input_path.stem}_to_{target_type.value}.json"
                success = self.save_codex_object(transformed_obj, str(output_path))
                
                result = {
                    'index': i,
                    'input_file': str(input_path),
                    'output_file': str(output_path),
                    'source_title': source_obj.title,
                    'source_type': source_obj.object_type.value,
                    'target_type': target_type.value,
                    'success': success,
                    'quality_score': quality_score
                }
                
                if success:
                    print(f"  ✅ Saved to: {output_path}")
                else:
                    print(f"  ❌ Failed to save")
            else:
                result = {
                    'index': i,
                    'input_file': str(input_path),
                    'source_title': source_obj.title,
                    'source_type': source_obj.object_type.value,
                    'target_type': target_type.value,
                    'success': False,
                    'error': 'Transformation failed'
                }
                print(f"  ❌ Transformation failed")
            
            results.append(result)
        
        return results
    
    def _batch_transform_parallel(self, source_objects, target_type, args, output_dir):
        """Process batch transformation in parallel."""
        results = []
        total = len(source_objects)
        completed = 0
        
        max_workers = min(4, len(source_objects))
        print(f"🚀 Using {max_workers} parallel workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_data = {
                executor.submit(self._transform_single_task, source_obj, target_type, args, output_dir, input_path, i): 
                (i, source_obj, input_path) for i, (source_obj, input_path) in enumerate(source_objects)
            }
            
            # Process completed tasks
            for future in as_completed(future_to_data):
                i, source_obj, input_path = future_to_data[future]
                completed += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    status = "✅" if result['success'] else "❌"
                    print(f"{status} Completed {completed}/{total}: {source_obj.title}")
                    
                except Exception as e:
                    result = {
                        'index': i,
                        'input_file': str(input_path),
                        'source_title': source_obj.title,
                        'source_type': source_obj.object_type.value,
                        'target_type': target_type.value,
                        'success': False,
                        'error': str(e)
                    }
                    results.append(result)
                    print(f"❌ Error {completed}/{total}: {source_obj.title} - {e}")
        
        # Sort results by index to maintain order
        results.sort(key=lambda x: x['index'])
        return results
    
    def _transform_single_task(self, source_obj, target_type, args, output_dir, input_path, index):
        """Single transformation task for parallel processing."""
        # Transform
        transformed_obj = self.transform_single_object(source_obj, target_type, args.approach, args.parameter)
        
        if not transformed_obj:
            return {
                'index': index,
                'input_file': str(input_path),
                'source_title': source_obj.title,
                'source_type': source_obj.object_type.value,
                'target_type': target_type.value,
                'success': False,
                'error': 'Transformation failed'
            }
        
        # Assess quality if requested
        quality_score = None
        if args.quality:
            quality_metrics = self.assess_transformation_quality(source_obj, transformed_obj)
            quality_score = quality_metrics['overall_score']
        
        # Save result
        output_path = output_dir / f"{input_path.stem}_to_{target_type.value}.json"
        success = self.save_codex_object(transformed_obj, str(output_path))
        
        return {
            'index': index,
            'input_file': str(input_path),
            'output_file': str(output_path) if success else None,
            'source_title': source_obj.title,
            'source_type': source_obj.object_type.value,
            'target_type': target_type.value,
            'success': success,
            'quality_score': quality_score
        }
    
    def cmd_history(self, args):
        """Handle history command."""
        if args.list:
            history = self.load_history()
            
            if not history:
                print("📝 No transformation history found")
                return 0
            
            print(f"📚 Transformation History ({len(history)} entries)")
            print("=" * 80)
            
            # Show recent entries (last 20)
            recent_entries = history[-20:] if len(history) > 20 else history
            
            for entry in reversed(recent_entries):
                timestamp = entry.get('timestamp', 'Unknown')
                entry_type = entry.get('type', 'unknown')
                
                if entry_type == 'single':
                    print(f"🎯 {timestamp}")
                    print(f"   Single: {entry.get('source_type')} → {entry.get('target_type')}")
                    print(f"   File: {entry.get('source_file')} → {entry.get('output_file')}")
                    if entry.get('quality_score'):
                        print(f"   Quality: {entry['quality_score']:.1%}")
                
                elif entry_type == 'batch':
                    print(f"📦 {timestamp}")
                    print(f"   Batch: {entry.get('total_files')} files → {entry.get('target_type')}")
                    print(f"   Success: {entry.get('successful')}/{entry.get('total_files')}")
                    if entry.get('quality_enabled'):
                        avg_quality = sum(r.get('quality_score', 0) for r in entry.get('results', []) if r.get('quality_score')) / max(1, len([r for r in entry.get('results', []) if r.get('quality_score')]))
                        print(f"   Avg Quality: {avg_quality:.1%}")
                
                print()
            
            if len(history) > 20:
                print(f"... and {len(history) - 20} more entries")
        
        elif args.export:
            history = self.load_history()
            export_file = args.export
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Exported {len(history)} history entries to: {export_file}")
        
        return 0
    
    def cmd_rollback(self, args):
        """Handle rollback command."""
        if args.list_snapshots:
            snapshots = self.list_snapshots()
            
            if not snapshots:
                print("📸 No snapshots found")
                return 0
            
            print(f"📸 Available Snapshots ({len(snapshots)})")
            print("=" * 80)
            
            for snapshot in snapshots:
                timestamp = datetime.fromisoformat(snapshot['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                print(f"📸 {snapshot['id']}")
                print(f"   Created: {timestamp}")
                print(f"   Objects: {len(snapshot['objects'])}")
                if snapshot.get('description'):
                    print(f"   Description: {snapshot['description']}")
                print()
        
        elif args.snapshot:
            snapshot_data = self.load_snapshot(args.snapshot)
            
            if not snapshot_data:
                print(f"❌ Snapshot not found: {args.snapshot}")
                return 1
            
            # Restore objects
            output_dir = Path(args.output_dir) if args.output_dir else Path("restored_objects")
            output_dir.mkdir(exist_ok=True)
            
            restored_count = 0
            
            for obj_data in snapshot_data['objects']:
                try:
                    # Recreate CodexObject
                    if IDEATION_ENGINE_AVAILABLE:
                        obj = CodexObject(
                            title=obj_data['title'],
                            content=obj_data['content'],
                            object_type=CodexObjectType(obj_data['object_type']),
                            genre=obj_data.get('genre', ''),
                            target_audience=obj_data.get('target_audience', ''),
                            development_stage=DevelopmentStage.DEVELOPMENT
                        )
                    else:
                        obj = CodexObject(
                            title=obj_data['title'],
                            content=obj_data['content'],
                            object_type=CodexObjectType(obj_data['object_type']),
                            word_count=obj_data['word_count'],
                            genre=obj_data.get('genre', ''),
                            target_audience=obj_data.get('target_audience', '')
                        )
                    
                    # Save restored object
                    output_path = output_dir / f"restored_{obj_data['uuid']}.json"
                    if self.save_codex_object(obj, str(output_path)):
                        restored_count += 1
                        print(f"✅ Restored: {obj.title} → {output_path}")
                    
                except Exception as e:
                    print(f"❌ Error restoring object {obj_data.get('title', 'Unknown')}: {e}")
            
            print(f"\n🎉 Restored {restored_count}/{len(snapshot_data['objects'])} objects to: {output_dir}")
        
        return 0


def main():
    cli = BatchTransformationCLI()
    
    parser = argparse.ArgumentParser(
        description="Batch Content Transformation CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file transformation
  python batch_transform_cli.py single input.json --target synopsis --output output.json
  
  # Batch transformation from directory
  python batch_transform_cli.py batch data/ --target outline --output-dir results/
  
  # Batch with quality assessment and parallel processing
  python batch_transform_cli.py batch "*.json" --target synopsis --quality --parallel
  
  # Create snapshot before transformation
  python batch_transform_cli.py single input.json --target outline --snapshot
  
  # List transformation history
  python batch_transform_cli.py history --list
  
  # List available snapshots
  python batch_transform_cli.py rollback --list-snapshots
  
  # Restore from snapshot
  python batch_transform_cli.py rollback --snapshot snapshot_id --output-dir restored/

Available content types:
  idea, logline, summary, synopsis, treatment, outline, detailed_outline, draft, manuscript, series
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Single transformation command
    single_parser = subparsers.add_parser('single', help='Transform a single file')
    single_parser.add_argument('input', help='Input JSON file')
    single_parser.add_argument('--target', '-t', required=True, choices=cli.available_types,
                              help='Target content type')
    single_parser.add_argument('--output', '-o', help='Output file (default: input_transformed.json)')
    single_parser.add_argument('--approach', choices=['planning', 'gardening'], default='planning',
                              help='Transformation approach')
    single_parser.add_argument('--parameter', choices=['expand', 'condense', 'restructure', 'enhance'],
                              default='expand', help='Transformation parameter')
    single_parser.add_argument('--quality', action='store_true', help='Assess transformation quality')
    single_parser.add_argument('--snapshot', action='store_true', help='Create rollback snapshot')
    single_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Batch transformation command
    batch_parser = subparsers.add_parser('batch', help='Transform multiple files')
    batch_parser.add_argument('input_pattern', help='Input pattern (directory or glob pattern)')
    batch_parser.add_argument('--target', '-t', required=True, choices=cli.available_types,
                             help='Target content type')
    batch_parser.add_argument('--output-dir', '-o', help='Output directory (default: batch_output)')
    batch_parser.add_argument('--approach', choices=['planning', 'gardening'], default='planning',
                             help='Transformation approach')
    batch_parser.add_argument('--parameter', choices=['expand', 'condense', 'restructure', 'enhance'],
                             default='expand', help='Transformation parameter')
    batch_parser.add_argument('--quality', action='store_true', help='Assess transformation quality')
    batch_parser.add_argument('--parallel', action='store_true', help='Use parallel processing')
    batch_parser.add_argument('--snapshot', action='store_true', help='Create rollback snapshot')
    batch_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # History command
    history_parser = subparsers.add_parser('history', help='View transformation history')
    history_parser.add_argument('--list', action='store_true', help='List recent transformations')
    history_parser.add_argument('--export', help='Export history to JSON file')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback and snapshot operations')
    rollback_parser.add_argument('--list-snapshots', action='store_true', help='List available snapshots')
    rollback_parser.add_argument('--snapshot', help='Restore from snapshot ID')
    rollback_parser.add_argument('--output-dir', help='Output directory for restored objects')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    if args.command == 'single':
        return cli.cmd_single_transform(args)
    elif args.command == 'batch':
        return cli.cmd_batch_transform(args)
    elif args.command == 'history':
        return cli.cmd_history(args)
    elif args.command == 'rollback':
        return cli.cmd_rollback(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())