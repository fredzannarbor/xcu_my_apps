"""
Database migration utilities for ideation system.
Handles database schema updates and data migrations.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages database schema migrations for the ideation system.
    Ensures database schema stays up-to-date with code changes.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize migration manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.migrations = self._get_migrations()
        logger.info(f"MigrationManager initialized for {self.db_path}")
    
    def _get_migrations(self) -> List[Dict[str, Any]]:
        """Get list of available migrations in order."""
        return [
            {
                "version": "001_initial_schema",
                "description": "Create initial ideation database schema",
                "sql": self._get_initial_schema_sql()
            },
            {
                "version": "002_add_indexes",
                "description": "Add performance indexes",
                "sql": self._get_indexes_sql()
            }
        ]
    
    def _get_initial_schema_sql(self) -> str:
        """Get the initial database schema SQL."""
        return """
        -- Migration tracking table
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            description TEXT,
            applied_at TEXT NOT NULL
        );
        
        -- Core content objects
        CREATE TABLE IF NOT EXISTS codex_objects (
            uuid TEXT PRIMARY KEY,
            shortuuid TEXT NOT NULL,
            object_type TEXT NOT NULL,
            development_stage TEXT NOT NULL,
            title TEXT,
            content TEXT,
            logline TEXT,
            description TEXT,
            genre TEXT,
            target_audience TEXT,
            confidence_score REAL DEFAULT 0.0,
            word_count INTEGER DEFAULT 0,
            parent_uuid TEXT,
            series_uuid TEXT,
            source_elements TEXT, -- JSON array
            derived_from TEXT, -- JSON array
            created_timestamp TEXT NOT NULL,
            last_modified TEXT NOT NULL,
            processing_history TEXT, -- JSON array
            llm_responses TEXT, -- JSON object
            generation_metadata TEXT, -- JSON object
            tournament_performance TEXT, -- JSON object
            reader_feedback TEXT, -- JSON array
            evaluation_scores TEXT, -- JSON object
            status TEXT DEFAULT 'created',
            tags TEXT, -- JSON array
            notes TEXT,
            FOREIGN KEY (parent_uuid) REFERENCES codex_objects(uuid),
            FOREIGN KEY (series_uuid) REFERENCES series(uuid)
        );
        
        -- Tournament management
        CREATE TABLE IF NOT EXISTS tournaments (
            uuid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            tournament_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'created',
            config_json TEXT,
            created_timestamp TEXT NOT NULL,
            started_timestamp TEXT,
            completed_timestamp TEXT,
            results_json TEXT,
            participant_count INTEGER DEFAULT 0,
            round_count INTEGER DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS tournament_matches (
            uuid TEXT PRIMARY KEY,
            tournament_uuid TEXT NOT NULL,
            round_number INTEGER NOT NULL,
            match_number INTEGER NOT NULL,
            object1_uuid TEXT NOT NULL,
            object2_uuid TEXT NOT NULL,
            winner_uuid TEXT,
            evaluation_data TEXT, -- JSON object
            created_timestamp TEXT NOT NULL,
            completed_timestamp TEXT,
            FOREIGN KEY (tournament_uuid) REFERENCES tournaments(uuid),
            FOREIGN KEY (object1_uuid) REFERENCES codex_objects(uuid),
            FOREIGN KEY (object2_uuid) REFERENCES codex_objects(uuid),
            FOREIGN KEY (winner_uuid) REFERENCES codex_objects(uuid)
        );
        
        -- Series management
        CREATE TABLE IF NOT EXISTS series (
            uuid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            formulaicness_level REAL DEFAULT 0.5,
            franchise_mode BOOLEAN DEFAULT FALSE,
            consistency_rules TEXT, -- JSON object
            created_timestamp TEXT NOT NULL,
            last_modified TEXT NOT NULL,
            book_count INTEGER DEFAULT 0
        );
        
        -- Synthetic reader panels
        CREATE TABLE IF NOT EXISTS reader_panels (
            uuid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            demographics_json TEXT NOT NULL,
            panel_size INTEGER NOT NULL,
            created_timestamp TEXT NOT NULL,
            last_used TEXT,
            usage_count INTEGER DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS reader_evaluations (
            uuid TEXT PRIMARY KEY,
            panel_uuid TEXT NOT NULL,
            object_uuid TEXT NOT NULL,
            reader_persona_json TEXT NOT NULL,
            evaluation_results TEXT NOT NULL, -- JSON object
            created_timestamp TEXT NOT NULL,
            FOREIGN KEY (panel_uuid) REFERENCES reader_panels(uuid),
            FOREIGN KEY (object_uuid) REFERENCES codex_objects(uuid)
        );
        
        -- Element extraction and recombination
        CREATE TABLE IF NOT EXISTS story_elements (
            uuid TEXT PRIMARY KEY,
            element_type TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            source_object_uuid TEXT NOT NULL,
            extraction_confidence REAL DEFAULT 0.0,
            usage_count INTEGER DEFAULT 0,
            created_timestamp TEXT NOT NULL,
            FOREIGN KEY (source_object_uuid) REFERENCES codex_objects(uuid)
        );
        
        CREATE TABLE IF NOT EXISTS element_combinations (
            uuid TEXT PRIMARY KEY,
            combination_name TEXT,
            element_uuids TEXT NOT NULL, -- JSON array
            result_object_uuid TEXT,
            created_timestamp TEXT NOT NULL,
            FOREIGN KEY (result_object_uuid) REFERENCES codex_objects(uuid)
        );
        
        -- Batch processing jobs
        CREATE TABLE IF NOT EXISTS batch_jobs (
            uuid TEXT PRIMARY KEY,
            job_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'created',
            config_json TEXT,
            progress_data TEXT, -- JSON object
            created_timestamp TEXT NOT NULL,
            started_timestamp TEXT,
            completed_timestamp TEXT,
            error_message TEXT,
            processed_count INTEGER DEFAULT 0,
            total_count INTEGER DEFAULT 0
        );
        
        -- Collaborative sessions
        CREATE TABLE IF NOT EXISTS collaboration_sessions (
            uuid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            session_type TEXT NOT NULL,
            participants_json TEXT, -- JSON array
            status TEXT NOT NULL DEFAULT 'active',
            created_timestamp TEXT NOT NULL,
            ended_timestamp TEXT,
            object_count INTEGER DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS collaboration_contributions (
            uuid TEXT PRIMARY KEY,
            session_uuid TEXT NOT NULL,
            contributor_id TEXT NOT NULL,
            object_uuid TEXT NOT NULL,
            contribution_type TEXT NOT NULL,
            contribution_data TEXT, -- JSON object
            created_timestamp TEXT NOT NULL,
            FOREIGN KEY (session_uuid) REFERENCES collaboration_sessions(uuid),
            FOREIGN KEY (object_uuid) REFERENCES codex_objects(uuid)
        );
        """
    
    def _get_indexes_sql(self) -> str:
        """Get the performance indexes SQL."""
        return """
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_codex_objects_type ON codex_objects(object_type);
        CREATE INDEX IF NOT EXISTS idx_codex_objects_stage ON codex_objects(development_stage);
        CREATE INDEX IF NOT EXISTS idx_codex_objects_parent ON codex_objects(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_codex_objects_series ON codex_objects(series_uuid);
        CREATE INDEX IF NOT EXISTS idx_codex_objects_created ON codex_objects(created_timestamp);
        CREATE INDEX IF NOT EXISTS idx_codex_objects_modified ON codex_objects(last_modified);
        CREATE INDEX IF NOT EXISTS idx_codex_objects_status ON codex_objects(status);
        CREATE INDEX IF NOT EXISTS idx_codex_objects_genre ON codex_objects(genre);
        
        CREATE INDEX IF NOT EXISTS idx_tournaments_status ON tournaments(status);
        CREATE INDEX IF NOT EXISTS idx_tournaments_created ON tournaments(created_timestamp);
        CREATE INDEX IF NOT EXISTS idx_tournaments_type ON tournaments(tournament_type);
        
        CREATE INDEX IF NOT EXISTS idx_tournament_matches_tournament ON tournament_matches(tournament_uuid);
        CREATE INDEX IF NOT EXISTS idx_tournament_matches_round ON tournament_matches(round_number);
        CREATE INDEX IF NOT EXISTS idx_tournament_matches_object1 ON tournament_matches(object1_uuid);
        CREATE INDEX IF NOT EXISTS idx_tournament_matches_object2 ON tournament_matches(object2_uuid);
        
        CREATE INDEX IF NOT EXISTS idx_series_created ON series(created_timestamp);
        CREATE INDEX IF NOT EXISTS idx_series_modified ON series(last_modified);
        
        CREATE INDEX IF NOT EXISTS idx_reader_panels_created ON reader_panels(created_timestamp);
        CREATE INDEX IF NOT EXISTS idx_reader_evaluations_panel ON reader_evaluations(panel_uuid);
        CREATE INDEX IF NOT EXISTS idx_reader_evaluations_object ON reader_evaluations(object_uuid);
        CREATE INDEX IF NOT EXISTS idx_reader_evaluations_created ON reader_evaluations(created_timestamp);
        
        CREATE INDEX IF NOT EXISTS idx_story_elements_source ON story_elements(source_object_uuid);
        CREATE INDEX IF NOT EXISTS idx_story_elements_type ON story_elements(element_type);
        CREATE INDEX IF NOT EXISTS idx_story_elements_created ON story_elements(created_timestamp);
        
        CREATE INDEX IF NOT EXISTS idx_batch_jobs_status ON batch_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_batch_jobs_type ON batch_jobs(job_type);
        CREATE INDEX IF NOT EXISTS idx_batch_jobs_created ON batch_jobs(created_timestamp);
        
        CREATE INDEX IF NOT EXISTS idx_collaboration_sessions_status ON collaboration_sessions(status);
        CREATE INDEX IF NOT EXISTS idx_collaboration_sessions_created ON collaboration_sessions(created_timestamp);
        CREATE INDEX IF NOT EXISTS idx_collaboration_contributions_session ON collaboration_contributions(session_uuid);
        CREATE INDEX IF NOT EXISTS idx_collaboration_contributions_object ON collaboration_contributions(object_uuid);
        CREATE INDEX IF NOT EXISTS idx_collaboration_contributions_contributor ON collaboration_contributions(contributor_id);
        """
    
    def get_current_version(self) -> Optional[str]:
        """Get the current database schema version."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1"
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return None
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT version FROM schema_migrations ORDER BY applied_at"
                )
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return []
    
    def get_pending_migrations(self) -> List[Dict[str, Any]]:
        """Get list of migrations that need to be applied."""
        applied = set(self.get_applied_migrations())
        return [m for m in self.migrations if m["version"] not in applied]
    
    def apply_migration(self, migration: Dict[str, Any]) -> bool:
        """
        Apply a single migration.
        
        Args:
            migration: Migration dictionary with version, description, and sql
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Execute migration SQL
                conn.executescript(migration["sql"])
                
                # Record migration as applied
                conn.execute(
                    "INSERT INTO schema_migrations (version, description, applied_at) VALUES (?, ?, ?)",
                    (migration["version"], migration["description"], datetime.now().isoformat())
                )
                
                conn.commit()
                
            logger.info(f"Applied migration {migration['version']}: {migration['description']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply migration {migration['version']}: {e}")
            return False
    
    def migrate_to_latest(self) -> bool:
        """
        Apply all pending migrations to bring database to latest version.
        
        Returns:
            True if all migrations successful, False otherwise
        """
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("Database is already at latest version")
            return True
        
        logger.info(f"Applying {len(pending)} pending migrations")
        
        for migration in pending:
            if not self.apply_migration(migration):
                logger.error(f"Migration failed at {migration['version']}")
                return False
        
        logger.info("All migrations applied successfully")
        return True
    
    def rollback_migration(self, version: str) -> bool:
        """
        Rollback a specific migration (if rollback SQL is available).
        Note: This is a placeholder - rollback functionality would need
        specific rollback SQL for each migration.
        
        Args:
            version: Migration version to rollback
            
        Returns:
            True if successful, False otherwise
        """
        logger.warning(f"Rollback not implemented for migration {version}")
        return False
    
    def validate_schema(self) -> Dict[str, Any]:
        """
        Validate the current database schema.
        
        Returns:
            Dictionary with validation results
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check that all expected tables exist
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = set(row[0] for row in cursor.fetchall())
                
                expected_tables = {
                    'schema_migrations', 'codex_objects', 'tournaments', 'tournament_matches',
                    'series', 'reader_panels', 'reader_evaluations', 'story_elements',
                    'element_combinations', 'batch_jobs', 'collaboration_sessions',
                    'collaboration_contributions'
                }
                
                missing_tables = expected_tables - existing_tables
                extra_tables = existing_tables - expected_tables
                
                # Check foreign key constraints
                cursor = conn.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                
                return {
                    "valid": len(missing_tables) == 0 and len(fk_violations) == 0,
                    "missing_tables": list(missing_tables),
                    "extra_tables": list(extra_tables),
                    "foreign_key_violations": len(fk_violations),
                    "current_version": self.get_current_version(),
                    "applied_migrations": self.get_applied_migrations()
                }
                
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    def create_backup_before_migration(self) -> Optional[str]:
        """
        Create a backup of the database before applying migrations.
        
        Returns:
            Path to backup file or None if failed
        """
        try:
            backup_path = self.db_path.parent / f"{self.db_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            # Copy database file
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"Created database backup: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            return None


def initialize_ideation_database(db_path: str, create_backup: bool = True) -> bool:
    """
    Initialize or migrate an ideation database to the latest schema.
    
    Args:
        db_path: Path to database file
        create_backup: Whether to create backup before migration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        migration_manager = MigrationManager(db_path)
        
        # Create backup if requested and database exists
        if create_backup and Path(db_path).exists():
            backup_path = migration_manager.create_backup_before_migration()
            if not backup_path:
                logger.warning("Failed to create backup, proceeding anyway")
        
        # Apply all pending migrations
        success = migration_manager.migrate_to_latest()
        
        if success:
            # Validate the final schema
            validation = migration_manager.validate_schema()
            if validation["valid"]:
                logger.info("Database initialization completed successfully")
                return True
            else:
                logger.error(f"Schema validation failed: {validation}")
                return False
        else:
            logger.error("Database migration failed")
            return False
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def get_database_info(db_path: str) -> Dict[str, Any]:
    """
    Get information about the database schema and migrations.
    
    Args:
        db_path: Path to database file
        
    Returns:
        Dictionary with database information
    """
    try:
        migration_manager = MigrationManager(db_path)
        validation = migration_manager.validate_schema()
        
        return {
            "database_path": str(db_path),
            "database_exists": Path(db_path).exists(),
            "current_version": migration_manager.get_current_version(),
            "applied_migrations": migration_manager.get_applied_migrations(),
            "pending_migrations": [m["version"] for m in migration_manager.get_pending_migrations()],
            "schema_validation": validation
        }
        
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {
            "database_path": str(db_path),
            "error": str(e)
        }