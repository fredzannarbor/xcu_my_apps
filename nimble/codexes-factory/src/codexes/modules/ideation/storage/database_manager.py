"""
Database management for ideation system.
Handles SQLite database operations with connection pooling and transaction management.
"""

import sqlite3
import json
import logging
import threading
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from queue import Queue

from ..core.codex_object import CodexObject, CodexObjectType, DevelopmentStage

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database operations with connection pooling and transaction handling.
    Implements Requirements 0.1, 0.2, 0.3 for content storage and retrieval.
    """
    
    def __init__(self, db_path: str, pool_size: int = 5):
        """
        Initialize database manager with connection pooling.
        
        Args:
            db_path: Path to SQLite database file
            pool_size: Maximum number of connections in pool
        """
        self.db_path = Path(db_path)
        self.pool_size = pool_size
        self.connection_pool = Queue(maxsize=pool_size)
        self.pool_lock = threading.Lock()
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._initialize_database()
        
        # Fill connection pool
        self._initialize_connection_pool()
        
        logger.info(f"DatabaseManager initialized with database at {self.db_path}")
    
    def _initialize_database(self):
        """Initialize database schema with all required tables."""
        schema_sql = self._get_schema_sql()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(schema_sql)
                conn.commit()
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise
    
    def _get_schema_sql(self) -> str:
        """Get the complete database schema SQL."""
        return """
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
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_codex_objects_type ON codex_objects(object_type);
        CREATE INDEX IF NOT EXISTS idx_codex_objects_stage ON codex_objects(development_stage);
        CREATE INDEX IF NOT EXISTS idx_codex_objects_parent ON codex_objects(parent_uuid);
        CREATE INDEX IF NOT EXISTS idx_codex_objects_series ON codex_objects(series_uuid);
        CREATE INDEX IF NOT EXISTS idx_codex_objects_created ON codex_objects(created_timestamp);
        CREATE INDEX IF NOT EXISTS idx_codex_objects_modified ON codex_objects(last_modified);
        
        CREATE INDEX IF NOT EXISTS idx_tournaments_status ON tournaments(status);
        CREATE INDEX IF NOT EXISTS idx_tournaments_created ON tournaments(created_timestamp);
        
        CREATE INDEX IF NOT EXISTS idx_tournament_matches_tournament ON tournament_matches(tournament_uuid);
        CREATE INDEX IF NOT EXISTS idx_tournament_matches_round ON tournament_matches(round_number);
        
        CREATE INDEX IF NOT EXISTS idx_reader_evaluations_panel ON reader_evaluations(panel_uuid);
        CREATE INDEX IF NOT EXISTS idx_reader_evaluations_object ON reader_evaluations(object_uuid);
        
        CREATE INDEX IF NOT EXISTS idx_story_elements_source ON story_elements(source_object_uuid);
        CREATE INDEX IF NOT EXISTS idx_story_elements_type ON story_elements(element_type);
        
        CREATE INDEX IF NOT EXISTS idx_batch_jobs_status ON batch_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_batch_jobs_type ON batch_jobs(job_type);
        
        CREATE INDEX IF NOT EXISTS idx_collaboration_sessions_status ON collaboration_sessions(status);
        CREATE INDEX IF NOT EXISTS idx_collaboration_contributions_session ON collaboration_contributions(session_uuid);
        """
    
    def _initialize_connection_pool(self):
        """Initialize the connection pool with configured number of connections."""
        for _ in range(self.pool_size):
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            conn.execute("PRAGMA journal_mode = WAL")  # Enable WAL mode for better concurrency
            self.connection_pool.put(conn)
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool."""
        conn = None
        try:
            with self.pool_lock:
                conn = self.connection_pool.get(timeout=10.0)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                with self.pool_lock:
                    self.connection_pool.put(conn)
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            raise
    
    def execute_transaction(self, operations: List[Tuple[str, Tuple]]) -> bool:
        """Execute multiple operations in a single transaction."""
        try:
            with self.get_connection() as conn:
                for query, params in operations:
                    conn.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return False
    
    def close(self):
        """Close all connections in the pool."""
        with self.pool_lock:
            while not self.connection_pool.empty():
                conn = self.connection_pool.get()
                conn.close()
        logger.info("Database connections closed")


class IdeationDatabase:
    """
    High-level database interface for ideation system operations.
    Provides methods for storing and retrieving CodexObjects and related data.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize with a database manager instance."""
        self.db = db_manager
        logger.info("IdeationDatabase initialized")
    
    # CodexObject operations
    
    def save_codex_object(self, obj: CodexObject) -> bool:
        """Save a CodexObject to the database."""
        try:
            query = """
            INSERT OR REPLACE INTO codex_objects (
                uuid, shortuuid, object_type, development_stage, title, content,
                logline, description, genre, target_audience, confidence_score,
                word_count, parent_uuid, series_uuid, source_elements, derived_from,
                created_timestamp, last_modified, processing_history, llm_responses,
                generation_metadata, tournament_performance, reader_feedback,
                evaluation_scores, status, tags, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                obj.uuid, obj.shortuuid, obj.object_type.value, obj.development_stage.value,
                obj.title, obj.content, obj.logline, obj.description, obj.genre,
                obj.target_audience, obj.confidence_score, obj.word_count,
                obj.parent_uuid, obj.series_uuid,
                json.dumps(obj.source_elements), json.dumps(obj.derived_from),
                obj.created_timestamp, obj.last_modified,
                json.dumps(obj.processing_history), json.dumps(obj.llm_responses),
                json.dumps(obj.generation_metadata), json.dumps(obj.tournament_performance),
                json.dumps(obj.reader_feedback), json.dumps(obj.evaluation_scores),
                obj.status, json.dumps(obj.tags), obj.notes
            )
            
            affected_rows = self.db.execute_update(query, params)
            success = affected_rows > 0
            
            if success:
                logger.info(f"Saved CodexObject {obj.shortuuid} to database")
            else:
                logger.warning(f"Failed to save CodexObject {obj.shortuuid}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving CodexObject {obj.shortuuid}: {e}")
            return False
    
    def load_codex_object(self, uuid: str) -> Optional[CodexObject]:
        """Load a CodexObject from the database by UUID."""
        try:
            query = "SELECT * FROM codex_objects WHERE uuid = ?"
            results = self.db.execute_query(query, (uuid,))
            
            if not results:
                return None
            
            row = results[0]
            return self._row_to_codex_object(row)
            
        except Exception as e:
            logger.error(f"Error loading CodexObject {uuid}: {e}")
            return None
    
    def _row_to_codex_object(self, row: sqlite3.Row) -> CodexObject:
        """Convert database row to CodexObject."""
        try:
            obj = CodexObject(
                uuid=row['uuid'],
                object_type=CodexObjectType(row['object_type']),
                development_stage=DevelopmentStage(row['development_stage']),
                title=row['title'] or "",
                content=row['content'] or "",
                logline=row['logline'] or "",
                description=row['description'] or "",
                genre=row['genre'] or "",
                target_audience=row['target_audience'] or "",
                confidence_score=row['confidence_score'] or 0.0,
                word_count=row['word_count'] or 0,
                parent_uuid=row['parent_uuid'],
                series_uuid=row['series_uuid'],
                source_elements=json.loads(row['source_elements'] or '[]'),
                derived_from=json.loads(row['derived_from'] or '[]'),
                created_timestamp=row['created_timestamp'],
                last_modified=row['last_modified'],
                processing_history=json.loads(row['processing_history'] or '[]'),
                llm_responses=json.loads(row['llm_responses'] or '{}'),
                generation_metadata=json.loads(row['generation_metadata'] or '{}'),
                tournament_performance=json.loads(row['tournament_performance'] or '{}'),
                reader_feedback=json.loads(row['reader_feedback'] or '[]'),
                evaluation_scores=json.loads(row['evaluation_scores'] or '{}'),
                status=row['status'] or 'created',
                tags=json.loads(row['tags'] or '[]'),
                notes=row['notes'] or ""
            )
            
            # Override the auto-generated shortuuid with stored value
            obj.shortuuid = row['shortuuid']
            
            return obj
            
        except Exception as e:
            logger.error(f"Error converting row to CodexObject: {e}")
            raise
    
    def find_codex_objects(self, 
                          object_type: Optional[CodexObjectType] = None,
                          development_stage: Optional[DevelopmentStage] = None,
                          parent_uuid: Optional[str] = None,
                          series_uuid: Optional[str] = None,
                          limit: int = 100,
                          offset: int = 0) -> List[CodexObject]:
        """Find CodexObjects matching specified criteria."""
        try:
            conditions = []
            params = []
            
            if object_type:
                conditions.append("object_type = ?")
                params.append(object_type.value)
            
            if development_stage:
                conditions.append("development_stage = ?")
                params.append(development_stage.value)
            
            if parent_uuid:
                conditions.append("parent_uuid = ?")
                params.append(parent_uuid)
            
            if series_uuid:
                conditions.append("series_uuid = ?")
                params.append(series_uuid)
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
            SELECT * FROM codex_objects
            {where_clause}
            ORDER BY created_timestamp DESC
            LIMIT ? OFFSET ?
            """
            
            params.extend([limit, offset])
            results = self.db.execute_query(query, tuple(params))
            
            return [self._row_to_codex_object(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error finding CodexObjects: {e}")
            return []
    
    def delete_codex_object(self, uuid: str) -> bool:
        """Delete a CodexObject from the database."""
        try:
            query = "DELETE FROM codex_objects WHERE uuid = ?"
            affected_rows = self.db.execute_update(query, (uuid,))
            success = affected_rows > 0
            
            if success:
                logger.info(f"Deleted CodexObject {uuid}")
            else:
                logger.warning(f"CodexObject {uuid} not found for deletion")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting CodexObject {uuid}: {e}")
            return False
    
    def count_codex_objects(self, 
                           object_type: Optional[CodexObjectType] = None,
                           development_stage: Optional[DevelopmentStage] = None) -> int:
        """Count CodexObjects matching specified criteria."""
        try:
            conditions = []
            params = []
            
            if object_type:
                conditions.append("object_type = ?")
                params.append(object_type.value)
            
            if development_stage:
                conditions.append("development_stage = ?")
                params.append(development_stage.value)
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"SELECT COUNT(*) FROM codex_objects{where_clause}"
            results = self.db.execute_query(query, tuple(params))
            
            return results[0][0] if results else 0
            
        except Exception as e:
            logger.error(f"Error counting CodexObjects: {e}")
            return 0
    
    # Tournament operations
    
    def save_tournament(self, tournament_data: Dict[str, Any]) -> bool:
        """Save tournament data to the database."""
        try:
            query = """
            INSERT OR REPLACE INTO tournaments (
                uuid, name, tournament_type, status, config_json,
                created_timestamp, started_timestamp, completed_timestamp,
                results_json, participant_count, round_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                tournament_data['uuid'],
                tournament_data['name'],
                tournament_data['tournament_type'],
                tournament_data['status'],
                json.dumps(tournament_data.get('config', {})),
                tournament_data['created_timestamp'],
                tournament_data.get('started_timestamp'),
                tournament_data.get('completed_timestamp'),
                json.dumps(tournament_data.get('results', {})),
                tournament_data.get('participant_count', 0),
                tournament_data.get('round_count', 0)
            )
            
            affected_rows = self.db.execute_update(query, params)
            success = affected_rows > 0
            
            if success:
                logger.info(f"Saved tournament {tournament_data['uuid']}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving tournament: {e}")
            return False
    
    def load_tournament(self, uuid: str) -> Optional[Dict[str, Any]]:
        """Load tournament data from the database."""
        try:
            query = "SELECT * FROM tournaments WHERE uuid = ?"
            results = self.db.execute_query(query, (uuid,))
            
            if not results:
                return None
            
            row = results[0]
            return {
                'uuid': row['uuid'],
                'name': row['name'],
                'tournament_type': row['tournament_type'],
                'status': row['status'],
                'config': json.loads(row['config_json'] or '{}'),
                'created_timestamp': row['created_timestamp'],
                'started_timestamp': row['started_timestamp'],
                'completed_timestamp': row['completed_timestamp'],
                'results': json.loads(row['results_json'] or '{}'),
                'participant_count': row['participant_count'],
                'round_count': row['round_count']
            }
            
        except Exception as e:
            logger.error(f"Error loading tournament {uuid}: {e}")
            return None
    
    # Series operations
    
    def save_series(self, series_data: Dict[str, Any]) -> bool:
        """Save series data to the database."""
        try:
            query = """
            INSERT OR REPLACE INTO series (
                uuid, name, description, formulaicness_level, franchise_mode,
                consistency_rules, created_timestamp, last_modified, book_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                series_data['uuid'],
                series_data['name'],
                series_data.get('description', ''),
                series_data.get('formulaicness_level', 0.5),
                series_data.get('franchise_mode', False),
                json.dumps(series_data.get('consistency_rules', {})),
                series_data['created_timestamp'],
                series_data.get('last_modified', series_data['created_timestamp']),
                series_data.get('book_count', 0)
            )
            
            affected_rows = self.db.execute_update(query, params)
            success = affected_rows > 0
            
            if success:
                logger.info(f"Saved series {series_data['uuid']}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving series: {e}")
            return False
    
    # Utility methods
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get statistics about database contents."""
        try:
            stats = {}
            
            # Count objects by type
            for obj_type in CodexObjectType:
                count = self.count_codex_objects(object_type=obj_type)
                stats[f"codex_objects_{obj_type.value}"] = count
            
            # Count tournaments
            results = self.db.execute_query("SELECT COUNT(*) FROM tournaments")
            stats['tournaments'] = results[0][0] if results else 0
            
            # Count series
            results = self.db.execute_query("SELECT COUNT(*) FROM series")
            stats['series'] = results[0][0] if results else 0
            
            # Count reader panels
            results = self.db.execute_query("SELECT COUNT(*) FROM reader_panels")
            stats['reader_panels'] = results[0][0] if results else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def cleanup_orphaned_records(self) -> int:
        """Clean up orphaned records and return count of cleaned records."""
        try:
            cleanup_operations = [
                # Remove tournament matches for non-existent tournaments
                ("DELETE FROM tournament_matches WHERE tournament_uuid NOT IN (SELECT uuid FROM tournaments)", ()),
                
                # Remove reader evaluations for non-existent panels or objects
                ("DELETE FROM reader_evaluations WHERE panel_uuid NOT IN (SELECT uuid FROM reader_panels)", ()),
                ("DELETE FROM reader_evaluations WHERE object_uuid NOT IN (SELECT uuid FROM codex_objects)", ()),
                
                # Remove story elements for non-existent objects
                ("DELETE FROM story_elements WHERE source_object_uuid NOT IN (SELECT uuid FROM codex_objects)", ()),
                
                # Remove collaboration contributions for non-existent sessions or objects
                ("DELETE FROM collaboration_contributions WHERE session_uuid NOT IN (SELECT uuid FROM collaboration_sessions)", ()),
                ("DELETE FROM collaboration_contributions WHERE object_uuid NOT IN (SELECT uuid FROM codex_objects)", ())
            ]
            
            total_cleaned = 0
            for query, params in cleanup_operations:
                affected = self.db.execute_update(query, params)
                total_cleaned += affected
            
            if total_cleaned > 0:
                logger.info(f"Cleaned up {total_cleaned} orphaned records")
            
            return total_cleaned
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0