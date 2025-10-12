#!/usr/bin/env python3
"""
Rights Management Database Module

SQLite database for tracking rights sales by territory, language, and time period.
Includes works, contracts, territories, and contact information.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
import json

logger = logging.getLogger(__name__)

class RightsDatabase:
    """
    Database manager for rights management system.
    Handles works, contracts, territories, publishers, and contacts.
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection."""
        if db_path is None:
            # Default to resources/data_tables/ directory
            self.db_path = Path(__file__).parent.parent.parent.parent / "resources" / "data_tables" / "rights_management.db"
        else:
            self.db_path = Path(db_path)

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = None
        self._initialize_database()

    def connect(self):
        """Establish database connection."""
        if self.connection is None:
            self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
        return self.connection

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def _initialize_database(self):
        """Create database tables if they don't exist."""
        conn = self.connect()
        cursor = conn.cursor()

        # Works table - core books/publications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subtitle TEXT,
                isbn TEXT UNIQUE,
                author_name TEXT NOT NULL,
                author_code TEXT,
                publication_date TEXT,
                imprint TEXT,
                genre TEXT,
                page_count INTEGER,
                description TEXT,
                original_language TEXT DEFAULT 'English',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Publishers/Rights Purchasers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS publishers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_name TEXT NOT NULL,
                contact_name TEXT,
                contact_email TEXT,
                contact_phone TEXT,
                address TEXT,
                country TEXT,
                primary_language TEXT,
                specialties TEXT,  -- JSON array of genres/specialties
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Territories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS territories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                territory_name TEXT UNIQUE NOT NULL,
                territory_code TEXT UNIQUE,
                primary_language TEXT,
                currency TEXT,
                market_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Rights Contracts table - main transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rights_contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_id INTEGER NOT NULL,
                publisher_id INTEGER NOT NULL,
                territory_id INTEGER NOT NULL,
                rights_type TEXT NOT NULL,  -- 'Translation', 'Distribution', 'Audio', etc.
                target_language TEXT,
                contract_start_date TEXT NOT NULL,
                contract_end_date TEXT NOT NULL,
                exclusive BOOLEAN DEFAULT 1,
                advance_payment DECIMAL(10,2),
                royalty_rate DECIMAL(5,4),
                net_compensation DECIMAL(10,2),
                author_share DECIMAL(3,2) DEFAULT 0.5,
                amount_due_author DECIMAL(10,2),
                payment_status TEXT DEFAULT 'Pending',  -- 'Pending', 'Paid', 'Overdue'
                contract_notes TEXT,
                contract_file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (work_id) REFERENCES works (id),
                FOREIGN KEY (publisher_id) REFERENCES publishers (id),
                FOREIGN KEY (territory_id) REFERENCES territories (id)
            )
        """)

        # Rights Offerings table - for tracking potential deals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rights_offerings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_id INTEGER NOT NULL,
                territory_id INTEGER,
                target_language TEXT,
                rights_type TEXT NOT NULL,
                asking_price DECIMAL(10,2),
                minimum_advance DECIMAL(10,2),
                preferred_royalty_rate DECIMAL(5,4),
                exclusive_offering BOOLEAN DEFAULT 1,
                offering_status TEXT DEFAULT 'Available',  -- 'Available', 'In Negotiation', 'Sold', 'Withdrawn'
                offering_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (work_id) REFERENCES works (id),
                FOREIGN KEY (territory_id) REFERENCES territories (id)
            )
        """)

        conn.commit()

        # Insert default territories if empty
        cursor.execute("SELECT COUNT(*) FROM territories")
        if cursor.fetchone()[0] == 0:
            self._insert_default_territories(cursor)
            conn.commit()

        logger.info(f"Rights management database initialized at {self.db_path}")

    def _insert_default_territories(self, cursor):
        """Insert common territories for rights management."""
        territories = [
            ('United States', 'US', 'English', 'USD', 'Primary English-language market'),
            ('United Kingdom', 'UK', 'English', 'GBP', 'UK and Commonwealth rights'),
            ('Germany', 'DE', 'German', 'EUR', 'German-language territory'),
            ('France', 'FR', 'French', 'EUR', 'French-language territory'),
            ('Italy', 'IT', 'Italian', 'EUR', 'Italian-language territory'),
            ('Spain', 'ES', 'Spanish', 'EUR', 'Spanish-language territory'),
            ('China', 'CN', 'Chinese', 'CNY', 'Simplified Chinese territory'),
            ('Japan', 'JP', 'Japanese', 'JPY', 'Japanese-language territory'),
            ('Korea', 'KR', 'Korean', 'KRW', 'Korean-language territory'),
            ('Brazil', 'BR', 'Portuguese', 'BRL', 'Portuguese-language territory'),
            ('Russia', 'RU', 'Russian', 'RUB', 'Russian-language territory'),
            ('India', 'IN', 'Hindi/English', 'INR', 'Indian subcontinent'),
            ('Australia', 'AU', 'English', 'AUD', 'Australia and New Zealand'),
            ('Canada', 'CA', 'English/French', 'CAD', 'Canadian territory'),
            ('Netherlands', 'NL', 'Dutch', 'EUR', 'Dutch-language territory'),
            ('Poland', 'PL', 'Polish', 'PLN', 'Polish-language territory'),
            ('Bulgaria', 'BG', 'Bulgarian', 'BGN', 'Bulgarian-language territory'),
            ('World English', 'WE', 'English', 'USD', 'Global English rights excluding specific territories'),
            ('World Rights', 'WR', 'Multiple', 'USD', 'Global rights all languages')
        ]

        cursor.executemany(
            "INSERT INTO territories (territory_name, territory_code, primary_language, currency, market_notes) VALUES (?, ?, ?, ?, ?)",
            territories
        )

    def add_work(self, title: str, author_name: str, isbn: Optional[str] = None, **kwargs) -> int:
        """Add a new work to the database."""
        conn = self.connect()
        cursor = conn.cursor()

        fields = ['title', 'author_name']
        values = [title, author_name]
        placeholders = ['?', '?']

        if isbn:
            fields.append('isbn')
            values.append(isbn)
            placeholders.append('?')

        # Add optional fields
        optional_fields = ['subtitle', 'author_code', 'publication_date', 'imprint',
                          'genre', 'page_count', 'description', 'original_language']

        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                fields.append(field)
                values.append(kwargs[field])
                placeholders.append('?')

        query = f"INSERT INTO works ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"

        try:
            cursor.execute(query, values)
            work_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Added work: {title} (ID: {work_id})")
            return work_id
        except sqlite3.IntegrityError as e:
            logger.error(f"Error adding work {title}: {e}")
            raise

    def add_publisher(self, organization_name: str, **kwargs) -> int:
        """Add a new publisher to the database."""
        conn = self.connect()
        cursor = conn.cursor()

        fields = ['organization_name']
        values = [organization_name]
        placeholders = ['?']

        optional_fields = ['contact_name', 'contact_email', 'contact_phone', 'address',
                          'country', 'primary_language', 'specialties', 'notes']

        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                fields.append(field)
                if field == 'specialties' and isinstance(kwargs[field], list):
                    values.append(json.dumps(kwargs[field]))
                else:
                    values.append(kwargs[field])
                placeholders.append('?')

        query = f"INSERT INTO publishers ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"

        cursor.execute(query, values)
        publisher_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Added publisher: {organization_name} (ID: {publisher_id})")
        return publisher_id

    def add_rights_contract(self, work_id: int, publisher_id: int, territory_id: int,
                           rights_type: str, contract_start_date: str, contract_end_date: str,
                           **kwargs) -> int:
        """Add a new rights contract."""
        conn = self.connect()
        cursor = conn.cursor()

        fields = ['work_id', 'publisher_id', 'territory_id', 'rights_type',
                 'contract_start_date', 'contract_end_date']
        values = [work_id, publisher_id, territory_id, rights_type,
                 contract_start_date, contract_end_date]
        placeholders = ['?'] * 6

        optional_fields = ['target_language', 'exclusive', 'advance_payment', 'royalty_rate',
                          'net_compensation', 'author_share', 'amount_due_author',
                          'payment_status', 'contract_notes', 'contract_file_path']

        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                fields.append(field)
                values.append(kwargs[field])
                placeholders.append('?')

        query = f"INSERT INTO rights_contracts ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"

        cursor.execute(query, values)
        contract_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Added rights contract (ID: {contract_id})")
        return contract_id

    def get_works(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all works from database."""
        conn = self.connect()
        cursor = conn.cursor()

        query = "SELECT * FROM works ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def get_publishers(self) -> List[Dict[str, Any]]:
        """Get all publishers from database."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM publishers ORDER BY organization_name")
        return [dict(row) for row in cursor.fetchall()]

    def get_territories(self) -> List[Dict[str, Any]]:
        """Get all territories from database."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM territories ORDER BY territory_name")
        return [dict(row) for row in cursor.fetchall()]

    def get_rights_contracts(self, work_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get rights contracts, optionally filtered by work."""
        conn = self.connect()
        cursor = conn.cursor()

        if work_id:
            query = """
                SELECT rc.*, w.title, w.author_name, p.organization_name, t.territory_name
                FROM rights_contracts rc
                JOIN works w ON rc.work_id = w.id
                JOIN publishers p ON rc.publisher_id = p.id
                JOIN territories t ON rc.territory_id = t.id
                WHERE rc.work_id = ?
                ORDER BY rc.contract_start_date DESC
            """
            cursor.execute(query, (work_id,))
        else:
            query = """
                SELECT rc.*, w.title, w.author_name, p.organization_name, t.territory_name
                FROM rights_contracts rc
                JOIN works w ON rc.work_id = w.id
                JOIN publishers p ON rc.publisher_id = p.id
                JOIN territories t ON rc.territory_id = t.id
                ORDER BY rc.contract_start_date DESC
            """
            cursor.execute(query)

        return [dict(row) for row in cursor.fetchall()]

    def search_works(self, search_term: str) -> List[Dict[str, Any]]:
        """Search works by title, author, or ISBN."""
        conn = self.connect()
        cursor = conn.cursor()

        query = """
            SELECT * FROM works
            WHERE title LIKE ? OR author_name LIKE ? OR isbn LIKE ?
            ORDER BY title
        """
        search_pattern = f"%{search_term}%"
        cursor.execute(query, (search_pattern, search_pattern, search_pattern))

        return [dict(row) for row in cursor.fetchall()]

    def get_work_by_id(self, work_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific work by ID."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM works WHERE id = ?", (work_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_work(self, work_id: int, **kwargs) -> bool:
        """Update work information."""
        if not kwargs:
            return False

        conn = self.connect()
        cursor = conn.cursor()

        # Add updated_at timestamp
        kwargs['updated_at'] = datetime.now().isoformat()

        fields = []
        values = []
        for field, value in kwargs.items():
            fields.append(f"{field} = ?")
            values.append(value)

        values.append(work_id)
        query = f"UPDATE works SET {', '.join(fields)} WHERE id = ?"

        cursor.execute(query, values)
        conn.commit()

        return cursor.rowcount > 0

    def delete_work(self, work_id: int) -> bool:
        """Delete a work and associated contracts."""
        conn = self.connect()
        cursor = conn.cursor()

        try:
            # Delete associated contracts first
            cursor.execute("DELETE FROM rights_contracts WHERE work_id = ?", (work_id,))
            cursor.execute("DELETE FROM rights_offerings WHERE work_id = ?", (work_id,))

            # Delete the work
            cursor.execute("DELETE FROM works WHERE id = ?", (work_id,))

            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error deleting work {work_id}: {e}")
            conn.rollback()
            return False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience function for getting database instance
def get_rights_database(db_path: Optional[str] = None) -> RightsDatabase:
    """Get a RightsDatabase instance."""
    return RightsDatabase(db_path)