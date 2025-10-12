"""
File system management for ideation system.
Handles organization and storage of ideation artifacts in the file system.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import uuid

from ..core.codex_object import CodexObject, CodexObjectType

logger = logging.getLogger(__name__)


class FileManager:
    """
    Manages file system operations for ideation artifacts.
    Provides organized storage and retrieval of files related to ideation workflows.
    """
    
    def __init__(self, base_path: str):
        """
        Initialize file manager with base storage path.
        
        Args:
            base_path: Base directory for ideation file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create directory structure
        self._initialize_directory_structure()
        
        logger.info(f"FileManager initialized with base path: {self.base_path}")
    
    def _initialize_directory_structure(self):
        """Initialize the standard directory structure for ideation files."""
        directories = [
            "objects/ideas",
            "objects/loglines", 
            "objects/summaries",
            "objects/synopses",
            "objects/treatments",
            "objects/outlines",
            "objects/detailed_outlines",
            "objects/drafts",
            "objects/manuscripts",
            "objects/series",
            "tournaments",
            "series",
            "synthetic_readers/panels",
            "synthetic_readers/evaluations",
            "batch_jobs",
            "exports/tournaments",
            "exports/evaluations",
            "exports/analytics",
            "backups",
            "temp"
        ]
        
        for directory in directories:
            dir_path = self.base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_object_directory(self, object_type: CodexObjectType) -> Path:
        """Get the directory path for a specific object type."""
        type_mapping = {
            CodexObjectType.IDEA: "ideas",
            CodexObjectType.LOGLINE: "loglines",
            CodexObjectType.SUMMARY: "summaries",
            CodexObjectType.SYNOPSIS: "synopses",
            CodexObjectType.TREATMENT: "treatments",
            CodexObjectType.OUTLINE: "outlines",
            CodexObjectType.DETAILED_OUTLINE: "detailed_outlines",
            CodexObjectType.DRAFT: "drafts",
            CodexObjectType.MANUSCRIPT: "manuscripts",
            CodexObjectType.SERIES: "series",
            CodexObjectType.UNKNOWN: "unknown"
        }
        
        subdir = type_mapping.get(object_type, "unknown")
        return self.base_path / "objects" / subdir
    
    def save_codex_object_file(self, obj: CodexObject) -> str:
        """
        Save a CodexObject to a JSON file.
        
        Args:
            obj: CodexObject to save
            
        Returns:
            Path to saved file
        """
        try:
            # Determine save directory
            save_dir = self.get_object_directory(obj.object_type)
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename
            filename = f"{obj.shortuuid}_{obj.object_type.value}.json"
            file_path = save_dir / filename
            
            # Save object
            obj.save_to_file(str(file_path))
            
            logger.info(f"Saved CodexObject file: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving CodexObject file for {obj.shortuuid}: {e}")
            raise
    
    def load_codex_object_file(self, file_path: str) -> Optional[CodexObject]:
        """
        Load a CodexObject from a JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Loaded CodexObject or None if failed
        """
        try:
            return CodexObject.load_from_file(file_path)
        except Exception as e:
            logger.error(f"Error loading CodexObject from {file_path}: {e}")
            return None
    
    def find_object_files(self, 
                         object_type: Optional[CodexObjectType] = None,
                         pattern: str = "*.json") -> List[Path]:
        """
        Find CodexObject files matching criteria.
        
        Args:
            object_type: Filter by object type
            pattern: File pattern to match
            
        Returns:
            List of matching file paths
        """
        try:
            if object_type:
                search_dir = self.get_object_directory(object_type)
                return list(search_dir.glob(pattern))
            else:
                # Search all object directories
                all_files = []
                objects_dir = self.base_path / "objects"
                for subdir in objects_dir.iterdir():
                    if subdir.is_dir():
                        all_files.extend(subdir.glob(pattern))
                return all_files
                
        except Exception as e:
            logger.error(f"Error finding object files: {e}")
            return []
    
    def delete_codex_object_file(self, obj: CodexObject) -> bool:
        """
        Delete the file for a CodexObject.
        
        Args:
            obj: CodexObject whose file should be deleted
            
        Returns:
            True if successful, False otherwise
        """
        try:
            save_dir = self.get_object_directory(obj.object_type)
            filename = f"{obj.shortuuid}_{obj.object_type.value}.json"
            file_path = save_dir / filename
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted CodexObject file: {file_path}")
                return True
            else:
                logger.warning(f"CodexObject file not found: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting CodexObject file for {obj.shortuuid}: {e}")
            return False
    
    def save_tournament_data(self, tournament_uuid: str, tournament_data: Dict[str, Any]) -> str:
        """
        Save tournament data to file system.
        
        Args:
            tournament_uuid: Tournament UUID
            tournament_data: Tournament data dictionary
            
        Returns:
            Path to saved directory
        """
        try:
            tournament_dir = self.base_path / "tournaments" / tournament_uuid
            tournament_dir.mkdir(parents=True, exist_ok=True)
            
            # Save main tournament data
            tournament_file = tournament_dir / "tournament.json"
            with open(tournament_file, 'w', encoding='utf-8') as f:
                json.dump(tournament_data, f, indent=2, ensure_ascii=False)
            
            # Save bracket data if available
            if 'bracket' in tournament_data:
                bracket_file = tournament_dir / "bracket.json"
                with open(bracket_file, 'w', encoding='utf-8') as f:
                    json.dump(tournament_data['bracket'], f, indent=2, ensure_ascii=False)
            
            # Save results if available
            if 'results' in tournament_data:
                results_file = tournament_dir / "results.json"
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump(tournament_data['results'], f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved tournament data: {tournament_dir}")
            return str(tournament_dir)
            
        except Exception as e:
            logger.error(f"Error saving tournament data for {tournament_uuid}: {e}")
            raise
    
    def load_tournament_data(self, tournament_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Load tournament data from file system.
        
        Args:
            tournament_uuid: Tournament UUID
            
        Returns:
            Tournament data dictionary or None if not found
        """
        try:
            tournament_dir = self.base_path / "tournaments" / tournament_uuid
            tournament_file = tournament_dir / "tournament.json"
            
            if not tournament_file.exists():
                return None
            
            with open(tournament_file, 'r', encoding='utf-8') as f:
                tournament_data = json.load(f)
            
            # Load additional files if they exist
            bracket_file = tournament_dir / "bracket.json"
            if bracket_file.exists():
                with open(bracket_file, 'r', encoding='utf-8') as f:
                    tournament_data['bracket'] = json.load(f)
            
            results_file = tournament_dir / "results.json"
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    tournament_data['results'] = json.load(f)
            
            return tournament_data
            
        except Exception as e:
            logger.error(f"Error loading tournament data for {tournament_uuid}: {e}")
            return None
    
    def save_series_data(self, series_uuid: str, series_data: Dict[str, Any]) -> str:
        """
        Save series data to file system.
        
        Args:
            series_uuid: Series UUID
            series_data: Series data dictionary
            
        Returns:
            Path to saved directory
        """
        try:
            series_dir = self.base_path / "series" / series_uuid
            series_dir.mkdir(parents=True, exist_ok=True)
            
            # Save main series data
            series_file = series_dir / "series.json"
            with open(series_file, 'w', encoding='utf-8') as f:
                json.dump(series_data, f, indent=2, ensure_ascii=False)
            
            # Create subdirectories for series artifacts
            (series_dir / "consistency_reports").mkdir(exist_ok=True)
            (series_dir / "book_outlines").mkdir(exist_ok=True)
            
            logger.info(f"Saved series data: {series_dir}")
            return str(series_dir)
            
        except Exception as e:
            logger.error(f"Error saving series data for {series_uuid}: {e}")
            raise
    
    def save_reader_panel_data(self, panel_uuid: str, panel_data: Dict[str, Any]) -> str:
        """
        Save synthetic reader panel data.
        
        Args:
            panel_uuid: Panel UUID
            panel_data: Panel data dictionary
            
        Returns:
            Path to saved file
        """
        try:
            panels_dir = self.base_path / "synthetic_readers" / "panels"
            panels_dir.mkdir(parents=True, exist_ok=True)
            
            panel_file = panels_dir / f"{panel_uuid}.json"
            with open(panel_file, 'w', encoding='utf-8') as f:
                json.dump(panel_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved reader panel data: {panel_file}")
            return str(panel_file)
            
        except Exception as e:
            logger.error(f"Error saving reader panel data for {panel_uuid}: {e}")
            raise
    
    def save_batch_job_data(self, job_uuid: str, job_data: Dict[str, Any]) -> str:
        """
        Save batch job data and create working directory.
        
        Args:
            job_uuid: Job UUID
            job_data: Job data dictionary
            
        Returns:
            Path to job directory
        """
        try:
            job_dir = self.base_path / "batch_jobs" / job_uuid
            job_dir.mkdir(parents=True, exist_ok=True)
            
            # Save job configuration
            config_file = job_dir / "config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(job_data, f, indent=2, ensure_ascii=False)
            
            # Create subdirectories
            (job_dir / "results").mkdir(exist_ok=True)
            (job_dir / "logs").mkdir(exist_ok=True)
            
            logger.info(f"Saved batch job data: {job_dir}")
            return str(job_dir)
            
        except Exception as e:
            logger.error(f"Error saving batch job data for {job_uuid}: {e}")
            raise
    
    def export_to_csv(self, data: List[Dict[str, Any]], filename: str, 
                     export_type: str = "general") -> str:
        """
        Export data to CSV file.
        
        Args:
            data: List of dictionaries to export
            filename: Output filename
            export_type: Type of export (tournaments, evaluations, analytics)
            
        Returns:
            Path to exported file
        """
        try:
            import csv
            
            export_dir = self.base_path / "exports" / export_type
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Add timestamp to filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"{timestamp}_{filename}"
            csv_path = export_dir / csv_filename
            
            if not data:
                logger.warning("No data to export")
                return str(csv_path)
            
            # Write CSV
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Exported {len(data)} records to {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
    
    def export_to_json(self, data: Any, filename: str, 
                      export_type: str = "general") -> str:
        """
        Export data to JSON file.
        
        Args:
            data: Data to export
            filename: Output filename
            export_type: Type of export
            
        Returns:
            Path to exported file
        """
        try:
            export_dir = self.base_path / "exports" / export_type
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Add timestamp to filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"{timestamp}_{filename}"
            json_path = export_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported data to {json_path}")
            return str(json_path)
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            raise
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a backup of all ideation data.
        
        Args:
            backup_name: Optional backup name, defaults to timestamp
            
        Returns:
            Path to backup directory
        """
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_dir = self.base_path / "backups" / backup_name
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy all data directories
            data_dirs = ["objects", "tournaments", "series", "synthetic_readers", "batch_jobs"]
            
            for data_dir in data_dirs:
                source_dir = self.base_path / data_dir
                if source_dir.exists():
                    dest_dir = backup_dir / data_dir
                    shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
            
            # Create backup manifest
            manifest = {
                "backup_name": backup_name,
                "created_timestamp": datetime.now().isoformat(),
                "directories_backed_up": data_dirs,
                "backup_size_mb": self._get_directory_size(backup_dir) / (1024 * 1024)
            }
            
            manifest_file = backup_dir / "backup_manifest.json"
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created backup: {backup_dir}")
            return str(backup_dir)
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise
    
    def _get_directory_size(self, directory: Path) -> int:
        """Get total size of directory in bytes."""
        total_size = 0
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified age.
        
        Args:
            max_age_hours: Maximum age of temp files to keep
            
        Returns:
            Number of files cleaned up
        """
        try:
            temp_dir = self.base_path / "temp"
            if not temp_dir.exists():
                return 0
            
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            cleaned_count = 0
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} temporary files")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about file system storage usage."""
        try:
            stats = {
                "base_path": str(self.base_path),
                "total_size_mb": self._get_directory_size(self.base_path) / (1024 * 1024),
                "directory_stats": {}
            }
            
            # Get stats for each major directory
            major_dirs = ["objects", "tournaments", "series", "synthetic_readers", 
                         "batch_jobs", "exports", "backups"]
            
            for dir_name in major_dirs:
                dir_path = self.base_path / dir_name
                if dir_path.exists():
                    file_count = len(list(dir_path.rglob('*')))
                    size_mb = self._get_directory_size(dir_path) / (1024 * 1024)
                    stats["directory_stats"][dir_name] = {
                        "file_count": file_count,
                        "size_mb": round(size_mb, 2)
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}


class IdeationFileManager:
    """
    High-level file manager interface for ideation system.
    Provides convenient methods for common file operations.
    """
    
    def __init__(self, base_path: str):
        """Initialize with base storage path."""
        self.file_manager = FileManager(base_path)
        logger.info("IdeationFileManager initialized")
    
    def save_object(self, obj: CodexObject) -> str:
        """Save a CodexObject to the file system."""
        return self.file_manager.save_codex_object_file(obj)
    
    def load_object(self, file_path: str) -> Optional[CodexObject]:
        """Load a CodexObject from the file system."""
        return self.file_manager.load_codex_object_file(file_path)
    
    def find_objects(self, object_type: Optional[CodexObjectType] = None) -> List[CodexObject]:
        """Find and load CodexObjects from the file system."""
        file_paths = self.file_manager.find_object_files(object_type)
        objects = []
        
        for file_path in file_paths:
            obj = self.load_object(str(file_path))
            if obj:
                objects.append(obj)
        
        return objects
    
    def delete_object(self, obj: CodexObject) -> bool:
        """Delete a CodexObject from the file system."""
        return self.file_manager.delete_codex_object_file(obj)
    
    def export_objects_csv(self, objects: List[CodexObject], filename: str) -> str:
        """Export CodexObjects to CSV format."""
        data = []
        for obj in objects:
            data.append({
                "uuid": obj.uuid,
                "shortuuid": obj.shortuuid,
                "type": obj.object_type.value,
                "stage": obj.development_stage.value,
                "title": obj.title,
                "genre": obj.genre,
                "word_count": obj.word_count,
                "confidence_score": obj.confidence_score,
                "created": obj.created_timestamp,
                "modified": obj.last_modified,
                "status": obj.status
            })
        
        return self.file_manager.export_to_csv(data, filename, "objects")
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create a backup of all ideation files."""
        return self.file_manager.create_backup(backup_name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get file system statistics."""
        return self.file_manager.get_storage_stats()