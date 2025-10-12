#!/usr/bin/env python3
"""
Rights Management CRUD Operations

High-level operations for managing works, publishers, territories, and contracts.
Provides business logic layer above the database.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
import json
from pathlib import Path

try:
    from .database import RightsDatabase
except ImportError:
    from database import RightsDatabase

logger = logging.getLogger(__name__)


class RightsManager:
    """
    High-level rights management operations.
    Provides business logic and validation for rights transactions.
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize with database connection."""
        self.db = RightsDatabase(db_path)

    def import_existing_rights_data(self, csv_path: str) -> Tuple[int, int, List[str]]:
        """
        Import existing rights data from CSV file.
        Returns (works_imported, contracts_imported, errors).
        """
        import csv

        works_imported = 0
        contracts_imported = 0
        errors = []

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Clean and validate row data
                        title = row.get('Title', '').strip()
                        isbn = row.get('ISBN', '').strip() or None
                        author_name = row.get('Author Name', '').strip()

                        if not title or not author_name:
                            errors.append(f"Row {row_num}: Missing title or author")
                            continue

                        # Try to find existing work or create new one
                        work_id = self.get_or_create_work(
                            title=title,
                            author_name=author_name,
                            isbn=isbn,
                            author_code=row.get('Author code', '').strip() or None
                        )

                        if work_id:
                            works_imported += 1

                            # Create contract if we have purchaser info
                            purchaser_org = row.get('Purchaser organization', '').strip()
                            rights_purchased = row.get('Rights purchased', '').strip()
                            contract_date = row.get('Date', '').strip()

                            if purchaser_org and rights_purchased and contract_date:
                                # Get or create publisher
                                publisher_id = self.get_or_create_publisher(
                                    organization_name=purchaser_org,
                                    contact_name=row.get('Purchaser contact', '').strip() or None
                                )

                                # Get or create territory
                                territory_id = self.get_or_create_territory_by_language(rights_purchased)

                                # Parse contract details
                                term = row.get('Term', '7 years').strip()
                                net_compensation = self._parse_decimal(row.get('Net Compensation', '0'))
                                author_share = self._parse_decimal(row.get('Author Share', '0.5'))
                                due_to_author = self._parse_decimal(row.get('Due to Author', '0'))

                                # Create contract
                                contract_start = self._parse_date(contract_date)
                                contract_end = self._calculate_end_date(contract_start, term)

                                self.db.add_rights_contract(
                                    work_id=work_id,
                                    publisher_id=publisher_id,
                                    territory_id=territory_id,
                                    rights_type='Translation',
                                    contract_start_date=contract_start,
                                    contract_end_date=contract_end,
                                    target_language=rights_purchased,
                                    net_compensation=net_compensation,
                                    author_share=author_share,
                                    amount_due_author=due_to_author,
                                    payment_status='Paid' if due_to_author > 0 else 'Pending'
                                )
                                contracts_imported += 1

                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        logger.error(f"Error importing row {row_num}: {e}")

        except Exception as e:
            errors.append(f"File error: {str(e)}")
            logger.error(f"Error reading CSV file: {e}")

        return works_imported, contracts_imported, errors

    def get_or_create_work(self, title: str, author_name: str, **kwargs) -> Optional[int]:
        """Get existing work or create new one."""
        # First try to find by ISBN if provided
        isbn = kwargs.get('isbn')
        if isbn:
            works = self.db.search_works(isbn)
            if works:
                return works[0]['id']

        # Try to find by title and author
        search_results = self.db.search_works(title)
        for work in search_results:
            if work['author_name'].lower() == author_name.lower():
                return work['id']

        # Create new work
        try:
            return self.db.add_work(title=title, author_name=author_name, **kwargs)
        except Exception as e:
            logger.error(f"Error creating work {title}: {e}")
            return None

    def get_or_create_publisher(self, organization_name: str, **kwargs) -> int:
        """Get existing publisher or create new one."""
        publishers = self.db.get_publishers()
        for publisher in publishers:
            if publisher['organization_name'].lower() == organization_name.lower():
                return publisher['id']

        # Create new publisher
        return self.db.add_publisher(organization_name=organization_name, **kwargs)

    def get_or_create_territory_by_language(self, language: str) -> int:
        """Get territory by language or create new one."""
        territories = self.db.get_territories()

        # Map common language names to territories
        language_map = {
            'bulgarian': 'Bulgaria',
            'korean': 'Korea',
            'german': 'Germany',
            'chinese': 'China',
            'italian': 'Italy',
            'french': 'France',
            'spanish': 'Spain',
            'japanese': 'Japan',
            'portuguese': 'Brazil',
            'russian': 'Russia',
            'dutch': 'Netherlands',
            'polish': 'Poland'
        }

        language_lower = language.lower()
        territory_name = language_map.get(language_lower, language.title())

        # Find existing territory
        for territory in territories:
            if (territory['territory_name'].lower() == territory_name.lower() or
                territory['primary_language'].lower() == language_lower):
                return territory['id']

        # Create new territory
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO territories (territory_name, primary_language) VALUES (?, ?)",
            (territory_name, language.title())
        )
        territory_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Created new territory: {territory_name}")
        return territory_id

    def _parse_decimal(self, value: str) -> float:
        """Parse decimal value from string."""
        if not value or value.strip() == '':
            return 0.0
        try:
            # Remove any currency symbols or commas
            cleaned = str(value).replace('$', '').replace(',', '').strip()
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

    def _parse_date(self, date_str: str) -> str:
        """Parse date string and return ISO format."""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')

        # Try common date formats
        formats = ['%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y']

        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue

        # Default to current date if parsing fails
        logger.warning(f"Could not parse date: {date_str}")
        return datetime.now().strftime('%Y-%m-%d')

    def _calculate_end_date(self, start_date: str, term: str) -> str:
        """Calculate contract end date from start date and term."""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')

            # Parse term (e.g., "7 years", "2 years")
            if 'year' in term.lower():
                years = int(''.join(filter(str.isdigit, term))) or 7
                end_date = start.replace(year=start.year + years)
                return end_date.strftime('%Y-%m-%d')

        except Exception as e:
            logger.warning(f"Error calculating end date: {e}")

        # Default to 7 years from start
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = start.replace(year=start.year + 7)
            return end_date.strftime('%Y-%m-%d')
        except:
            return datetime.now().replace(year=datetime.now().year + 7).strftime('%Y-%m-%d')

    def get_work_rights_summary(self, work_id: int) -> Dict[str, Any]:
        """Get comprehensive rights summary for a work."""
        work = self.db.get_work_by_id(work_id)
        if not work:
            return {}

        contracts = self.db.get_rights_contracts(work_id)

        # Calculate totals
        total_revenue = sum(c['net_compensation'] or 0 for c in contracts)
        total_due_author = sum(c['amount_due_author'] or 0 for c in contracts)

        # Group by territory/language
        territories_sold = {}
        for contract in contracts:
            key = f"{contract['territory_name']} ({contract['target_language'] or 'Original'})"
            if key not in territories_sold:
                territories_sold[key] = {
                    'publisher': contract['organization_name'],
                    'start_date': contract['contract_start_date'],
                    'end_date': contract['contract_end_date'],
                    'revenue': contract['net_compensation'] or 0,
                    'status': contract['payment_status']
                }

        return {
            'work': work,
            'contracts': contracts,
            'total_revenue': total_revenue,
            'total_due_author': total_due_author,
            'territories_sold': territories_sold,
            'rights_sold_count': len(contracts)
        }

    def get_available_territories_for_work(self, work_id: int) -> List[Dict[str, Any]]:
        """Get territories where rights haven't been sold for a work."""
        # Get all territories
        all_territories = self.db.get_territories()

        # Get sold territories for this work
        contracts = self.db.get_rights_contracts(work_id)
        sold_territory_ids = {c['territory_id'] for c in contracts}

        # Filter available territories
        available = [t for t in all_territories if t['id'] not in sold_territory_ids]

        return available

    def create_rights_offering(self, work_id: int, territory_id: Optional[int],
                             rights_type: str, asking_price: float, **kwargs) -> int:
        """Create a new rights offering for a work."""
        conn = self.db.connect()
        cursor = conn.cursor()

        fields = ['work_id', 'rights_type', 'asking_price']
        values = [work_id, rights_type, asking_price]
        placeholders = ['?', '?', '?']

        if territory_id:
            fields.append('territory_id')
            values.append(territory_id)
            placeholders.append('?')

        optional_fields = ['target_language', 'minimum_advance', 'preferred_royalty_rate',
                          'exclusive_offering', 'offering_notes']

        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                fields.append(field)
                values.append(kwargs[field])
                placeholders.append('?')

        query = f"INSERT INTO rights_offerings ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"

        cursor.execute(query, values)
        offering_id = cursor.lastrowid
        conn.commit()

        logger.info(f"Created rights offering (ID: {offering_id})")
        return offering_id

    def get_rights_revenue_summary(self) -> Dict[str, Any]:
        """Get overall rights revenue summary."""
        conn = self.db.connect()
        cursor = conn.cursor()

        # Total revenue and contracts
        cursor.execute("""
            SELECT
                COUNT(*) as total_contracts,
                SUM(net_compensation) as total_revenue,
                SUM(amount_due_author) as total_due_authors
            FROM rights_contracts
        """)
        totals = dict(cursor.fetchone())

        # Revenue by territory
        cursor.execute("""
            SELECT
                t.territory_name,
                COUNT(*) as contracts,
                SUM(rc.net_compensation) as revenue
            FROM rights_contracts rc
            JOIN territories t ON rc.territory_id = t.id
            GROUP BY t.territory_name
            ORDER BY revenue DESC
        """)
        by_territory = [dict(row) for row in cursor.fetchall()]

        # Revenue by year
        cursor.execute("""
            SELECT
                strftime('%Y', contract_start_date) as year,
                COUNT(*) as contracts,
                SUM(net_compensation) as revenue
            FROM rights_contracts
            GROUP BY strftime('%Y', contract_start_date)
            ORDER BY year DESC
        """)
        by_year = [dict(row) for row in cursor.fetchall()]

        return {
            'totals': totals,
            'by_territory': by_territory,
            'by_year': by_year
        }

    def close(self):
        """Close database connection."""
        self.db.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience function
def get_rights_manager(db_path: Optional[str] = None) -> RightsManager:
    """Get a RightsManager instance."""
    return RightsManager(db_path)