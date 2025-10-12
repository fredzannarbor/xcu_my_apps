"""
Backup utilities for batch operations.
"""

import shutil
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages backups of configuration files."""

    def __init__(self, backup_base_dir: Optional[Path] = None):
        """
        Initialize the backup manager.

        Args:
            backup_base_dir: Base directory for backups
        """
        if backup_base_dir is None:
            backup_base_dir = Path("configs/imprints_archive/backups")

        self.backup_base_dir = Path(backup_base_dir)
        self.backup_base_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self,
        source_files: List[Path],
        operation_name: str = "batch_operation"
    ) -> Optional[Path]:
        """
        Create a backup of the specified files.

        Args:
            source_files: List of files to backup
            operation_name: Name of the operation (for backup naming)

        Returns:
            Path to the backup directory or None if failed
        """
        if not source_files:
            logger.warning("No files to backup")
            return None

        # Create timestamped backup directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_base_dir / f"{operation_name}_{timestamp}"

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Create backup manifest
            manifest = {
                "operation": operation_name,
                "timestamp": timestamp,
                "datetime": datetime.now().isoformat(),
                "files_backed_up": [],
                "source_directories": []
            }

            # Copy each file
            for source_file in source_files:
                if not source_file.exists():
                    logger.warning(f"Source file does not exist: {source_file}")
                    continue

                # Preserve directory structure relative to common base
                # Use the filename and parent directory name
                parent_name = source_file.parent.name
                dest_subdir = backup_dir / parent_name
                dest_subdir.mkdir(parents=True, exist_ok=True)

                dest_file = dest_subdir / source_file.name

                shutil.copy2(source_file, dest_file)

                manifest["files_backed_up"].append({
                    "source": str(source_file),
                    "backup": str(dest_file.relative_to(backup_dir)),
                    "size_bytes": source_file.stat().st_size
                })

                if str(source_file.parent) not in manifest["source_directories"]:
                    manifest["source_directories"].append(str(source_file.parent))

            # Save manifest
            manifest_path = backup_dir / "backup_manifest.json"
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)

            logger.info(
                f"Created backup of {len(source_files)} files at {backup_dir}"
            )

            return backup_dir

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def restore_backup(
        self,
        backup_dir: Path,
        destination_override: Optional[Path] = None
    ) -> bool:
        """
        Restore files from a backup.

        Args:
            backup_dir: Path to backup directory
            destination_override: Optional override for destination path

        Returns:
            True if restore was successful
        """
        if not backup_dir.exists():
            logger.error(f"Backup directory does not exist: {backup_dir}")
            return False

        manifest_path = backup_dir / "backup_manifest.json"
        if not manifest_path.exists():
            logger.error(f"Backup manifest not found: {manifest_path}")
            return False

        try:
            # Load manifest
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            restored_count = 0

            # Restore each file
            for file_info in manifest["files_backed_up"]:
                source_path = Path(file_info["source"])
                backup_path = backup_dir / file_info["backup"]

                if not backup_path.exists():
                    logger.warning(f"Backup file not found: {backup_path}")
                    continue

                # Determine destination
                if destination_override:
                    dest_path = destination_override / source_path.name
                else:
                    dest_path = source_path

                # Ensure parent directory exists
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Restore file
                shutil.copy2(backup_path, dest_path)
                restored_count += 1

            logger.info(
                f"Restored {restored_count} files from backup {backup_dir}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def list_backups(
        self,
        operation_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List available backups.

        Args:
            operation_name: Optional filter by operation name

        Returns:
            List of backup information dictionaries
        """
        backups = []

        if not self.backup_base_dir.exists():
            return backups

        for backup_dir in sorted(self.backup_base_dir.iterdir(), reverse=True):
            if not backup_dir.is_dir():
                continue

            manifest_path = backup_dir / "backup_manifest.json"
            if not manifest_path.exists():
                continue

            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)

                # Filter by operation name if specified
                if operation_name and manifest.get("operation") != operation_name:
                    continue

                backups.append({
                    "path": backup_dir,
                    "operation": manifest.get("operation", "unknown"),
                    "timestamp": manifest.get("timestamp", ""),
                    "datetime": manifest.get("datetime", ""),
                    "file_count": len(manifest.get("files_backed_up", [])),
                    "source_directories": manifest.get("source_directories", [])
                })

            except Exception as e:
                logger.warning(f"Failed to read backup manifest in {backup_dir}: {e}")

        return backups

    def delete_backup(self, backup_dir: Path) -> bool:
        """
        Delete a backup directory.

        Args:
            backup_dir: Path to backup directory

        Returns:
            True if deletion was successful
        """
        if not backup_dir.exists():
            logger.warning(f"Backup directory does not exist: {backup_dir}")
            return False

        try:
            shutil.rmtree(backup_dir)
            logger.info(f"Deleted backup: {backup_dir}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False

    def cleanup_old_backups(
        self,
        days: int = 30,
        keep_minimum: int = 5
    ) -> int:
        """
        Clean up backups older than specified days.

        Args:
            days: Number of days to keep backups
            keep_minimum: Minimum number of backups to keep

        Returns:
            Number of backups deleted
        """
        if not self.backup_base_dir.exists():
            return 0

        backups = self.list_backups()

        # Sort by datetime (newest first)
        backups.sort(key=lambda b: b.get("datetime", ""), reverse=True)

        deleted_count = 0
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for i, backup in enumerate(backups):
            # Keep minimum number of backups
            if i < keep_minimum:
                continue

            # Check age
            backup_datetime = datetime.fromisoformat(backup.get("datetime", ""))
            if backup_datetime.timestamp() < cutoff_date:
                if self.delete_backup(backup["path"]):
                    deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old backups")
        return deleted_count

    def get_backup_size(self, backup_dir: Path) -> int:
        """
        Get total size of a backup in bytes.

        Args:
            backup_dir: Path to backup directory

        Returns:
            Total size in bytes
        """
        if not backup_dir.exists():
            return 0

        total_size = 0
        for file_path in backup_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size
