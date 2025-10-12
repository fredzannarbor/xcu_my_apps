"""
Date Utilities Module

This module provides functionality for date calculations, particularly for publication date assignment.
"""

import logging
import calendar
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

def get_all_tuesdays_in_month(year: int, month: int) -> List[datetime]:
    """
    Get all Tuesdays in a given month.
    
    Args:
        year: Year
        month: Month (1-12)
        
    Returns:
        List of datetime objects representing all Tuesdays in the month
    """
    # Validate input
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be between 1 and 12, got {month}")
    
    # Get the first day of the month
    first_day = datetime(year, month, 1)
    
    # Find the first Tuesday (weekday 1 is Tuesday)
    days_until_tuesday = (1 - first_day.weekday()) % 7
    first_tuesday = first_day + timedelta(days=days_until_tuesday)
    
    # Get all Tuesdays in the month
    tuesdays = []
    current = first_tuesday
    while current.month == month:
        tuesdays.append(current)
        current += timedelta(days=7)
    
    return tuesdays

def distribute_books_across_tuesdays(
    num_books: int, 
    year: int, 
    month: int, 
    min_date: Optional[datetime] = None,
    max_date: Optional[datetime] = None
) -> List[datetime]:
    """
    Distribute books evenly across Tuesdays in a month.
    
    Args:
        num_books: Number of books to distribute
        year: Year
        month: Month (1-12)
        min_date: Minimum date to consider (optional)
        max_date: Maximum date to consider (optional)
        
    Returns:
        List of datetime objects representing publication dates for each book
    """
    # Get all Tuesdays in the month
    tuesdays = get_all_tuesdays_in_month(year, month)
    
    # Filter by min and max dates if provided
    if min_date:
        tuesdays = [d for d in tuesdays if d >= min_date]
    if max_date:
        tuesdays = [d for d in tuesdays if d <= max_date]
    
    if not tuesdays:
        raise ValueError(f"No Tuesdays found in {calendar.month_name[month]} {year} within the specified date range")
    
    # Distribute books evenly
    dates = []
    num_tuesdays = len(tuesdays)
    
    for i in range(num_books):
        # Distribute evenly across available Tuesdays
        tuesday_index = i % num_tuesdays
        dates.append(tuesdays[tuesday_index])
    
    return dates

def extract_month_year_from_schedule(schedule_path: str) -> Tuple[int, int]:
    """
    Extract month and year from a schedule JSON file.
    
    Args:
        schedule_path: Path to the schedule JSON file
        
    Returns:
        Tuple of (month, year)
    """
    try:
        with open(schedule_path, 'r', encoding='utf-8') as f:
            schedule_data = json.load(f)
        
        # Try to find month and year in the schedule data
        if "publishing_schedule" in schedule_data:
            for month_data in schedule_data["publishing_schedule"]:
                if "month" in month_data and "year" in month_data:
                    month_name = month_data["month"]
                    year = int(month_data["year"])
                    
                    # Convert month name to number
                    try:
                        month = datetime.strptime(month_name, "%B").month
                    except ValueError:
                        # Try abbreviated month name
                        month = datetime.strptime(month_name, "%b").month
                    
                    return month, year
        
        # If not found in the expected structure, look for any date field
        for key, value in schedule_data.items():
            if isinstance(value, str) and ("date" in key.lower() or "month" in key.lower()):
                try:
                    date = datetime.strptime(value, "%Y-%m-%d")
                    return date.month, date.year
                except ValueError:
                    pass
                try:
                    date = datetime.strptime(value, "%B %Y")
                    return date.month, date.year
                except ValueError:
                    pass
        
        # If still not found, use current month and year
        now = datetime.now()
        logger.warning(f"Could not extract month and year from schedule, using current: {now.month}/{now.year}")
        return now.month, now.year
    
    except Exception as e:
        logger.error(f"Error extracting month and year from schedule: {e}")
        now = datetime.now()
        return now.month, now.year

def extract_month_year_from_tranche(tranche_name: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract month and year from a tranche configuration.
    
    Args:
        tranche_name: Name of the tranche configuration
        
    Returns:
        Tuple of (month, year) or (None, None) if not found
    """
    try:
        # Try to load the tranche configuration
        tranche_path = Path(f"configs/tranches/{tranche_name}.json")
        if not tranche_path.exists():
            logger.warning(f"Tranche configuration not found: {tranche_path}")
            return None, None
        
        with open(tranche_path, 'r', encoding='utf-8') as f:
            tranche_data = json.load(f)
        
        # Try to find month and year in the tranche data
        if "tranche_info" in tranche_data:
            info = tranche_data["tranche_info"]
            
            # Check for target_month and target_year
            if "target_month" in info and "target_year" in info:
                month_str = info["target_month"]
                year_str = info["target_year"]
                
                # Parse month
                try:
                    if month_str.isdigit():
                        month = int(month_str)
                    else:
                        # Try to parse month name
                        month = datetime.strptime(month_str, "%B").month
                except ValueError:
                    try:
                        # Try abbreviated month name
                        month = datetime.strptime(month_str, "%b").month
                    except ValueError:
                        # Try month and year combined
                        try:
                            date = datetime.strptime(month_str, "%B %Y")
                            month = date.month
                            year = date.year
                            return month, year
                        except ValueError:
                            logger.warning(f"Could not parse month: {month_str}")
                            month = None
                
                # Parse year
                try:
                    year = int(year_str)
                except ValueError:
                    logger.warning(f"Could not parse year: {year_str}")
                    year = None
                
                return month, year
        
        logger.warning(f"Could not find month and year in tranche configuration: {tranche_name}")
        return None, None
    
    except Exception as e:
        logger.error(f"Error extracting month and year from tranche: {e}")
        return None, None

def assign_publication_dates(
    book_count: int,
    tranche_name: Optional[str] = None,
    schedule_path: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None
) -> List[str]:
    """
    Assign publication dates to books, distributing them across Tuesdays.
    
    Args:
        book_count: Number of books to assign dates to
        tranche_name: Name of the tranche configuration (optional)
        schedule_path: Path to the schedule JSON file (optional)
        month: Month (1-12) (optional)
        year: Year (optional)
        
    Returns:
        List of publication dates in ISO format (YYYY-MM-DD)
    """
    # Try to get month and year from various sources
    if month is None or year is None:
        if tranche_name:
            tranche_month, tranche_year = extract_month_year_from_tranche(tranche_name)
            if tranche_month and tranche_year:
                month = tranche_month
                year = tranche_year
        
        if (month is None or year is None) and schedule_path:
            schedule_month, schedule_year = extract_month_year_from_schedule(schedule_path)
            if schedule_month and schedule_year:
                month = schedule_month
                year = schedule_year
    
    # If still not set, use current month and year
    if month is None or year is None:
        now = datetime.now()
        month = now.month
        year = now.year
        logger.warning(f"Using current month and year: {month}/{year}")
    
    # Distribute books across Tuesdays
    dates = distribute_books_across_tuesdays(book_count, year, month)
    
    # Convert to ISO format
    return [d.strftime("%Y-%m-%d") for d in dates]