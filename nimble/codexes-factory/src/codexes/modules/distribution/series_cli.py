#!/usr/bin/env python
"""
Series CLI Module

This module provides a command-line interface for managing series metadata.
"""

import argparse
import json
import logging
import sys
from typing import Dict, Any, List, Optional

from .series_registry import SeriesRegistry, SeriesNotFoundError, SeriesAccessDeniedError, SeriesDeleteError

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        stream=sys.stdout
    )


def list_series(registry: SeriesRegistry, publisher_id: Optional[str] = None) -> None:
    """
    List all series in the registry.
    
    Args:
        registry: SeriesRegistry instance
        publisher_id: Optional publisher ID to filter by
    """
    if publisher_id:
        series_list = registry.get_series_for_publisher(publisher_id)
        print(f"Series for publisher '{publisher_id}':")
    else:
        series_list = list(registry.series.values())
        print("All series:")
    
    if not series_list:
        print("No series found.")
        return
    
    # Print series information
    for series in series_list:
        books = registry.get_books_in_series(series.id)
        print(f"- {series.name} (ID: {series.id})")
        print(f"  Publisher: {series.publisher_id}")
        print(f"  Multi-Publisher: {'Yes' if series.multi_publisher else 'No'}")
        print(f"  Books: {len(books)}")
        if series.description:
            print(f"  Description: {series.description}")
        print()


def show_series(registry: SeriesRegistry, series_id: str) -> None:
    """
    Show detailed information about a series.
    
    Args:
        registry: SeriesRegistry instance
        series_id: ID of the series to show
    """
    try:
        # Get series information
        series = registry.get_series_by_id(series_id)
        
        # Get books in the series
        books = registry.get_books_in_series(series_id)
        
        # Print series information
        print(f"Series: {series.name} (ID: {series.id})")
        print(f"Publisher: {series.publisher_id}")
        print(f"Multi-Publisher: {'Yes' if series.multi_publisher else 'No'}")
        print(f"Created: {series.creation_date.strftime('%Y-%m-%d')}")
        print(f"Last Updated: {series.last_updated.strftime('%Y-%m-%d')}")
        if series.description:
            print(f"Description: {series.description}")
        
        # Print books in the series
        print(f"\nBooks in series ({len(books)}):")
        if books:
            for book in sorted(books, key=lambda b: b.sequence_number):
                print(f"- #{book.sequence_number}: {book.book_id}")
                print(f"  Added: {book.addition_date.strftime('%Y-%m-%d')}")
        else:
            print("No books in this series.")
            
    except SeriesNotFoundError:
        print(f"Error: Series with ID '{series_id}' not found.")
        sys.exit(1)


def create_series(registry: SeriesRegistry, name: str, publisher_id: str, 
                 multi_publisher: bool = False, description: Optional[str] = None) -> None:
    """
    Create a new series.
    
    Args:
        registry: SeriesRegistry instance
        name: Name of the series
        publisher_id: ID of the publisher
        multi_publisher: Whether the series allows multiple publishers
        description: Optional description of the series
    """
    try:
        # Create the series
        series_id = registry.create_series(name, publisher_id, multi_publisher, description)
        print(f"Created series '{name}' with ID: {series_id}")
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def update_series(registry: SeriesRegistry, series_id: str, updates: Dict[str, Any], 
                 publisher_id: Optional[str] = None) -> None:
    """
    Update a series.
    
    Args:
        registry: SeriesRegistry instance
        series_id: ID of the series to update
        updates: Dictionary of fields to update
        publisher_id: Optional ID of the publisher making the update
    """
    try:
        # Update the series
        registry.update_series(series_id, updates, publisher_id)
        print(f"Updated series with ID: {series_id}")
        
    except SeriesNotFoundError:
        print(f"Error: Series with ID '{series_id}' not found.")
        sys.exit(1)
    except SeriesAccessDeniedError:
        print(f"Error: Publisher '{publisher_id}' does not have access to series '{series_id}'.")
        sys.exit(1)


def delete_series(registry: SeriesRegistry, series_id: str, 
                 publisher_id: Optional[str] = None, force: bool = False) -> None:
    """
    Delete a series.
    
    Args:
        registry: SeriesRegistry instance
        series_id: ID of the series to delete
        publisher_id: Optional ID of the publisher making the deletion
        force: Whether to force deletion even if books are assigned
    """
    try:
        # Delete the series
        registry.delete_series(series_id, publisher_id, force)
        print(f"Deleted series with ID: {series_id}")
        
    except SeriesNotFoundError:
        print(f"Error: Series with ID '{series_id}' not found.")
        sys.exit(1)
    except SeriesAccessDeniedError:
        print(f"Error: Publisher '{publisher_id}' does not have access to series '{series_id}'.")
        sys.exit(1)
    except SeriesDeleteError:
        print(f"Error: Cannot delete series '{series_id}' with assigned books. Use --force to override.")
        sys.exit(1)


def add_book(registry: SeriesRegistry, series_id: str, book_id: str, 
            sequence_number: Optional[int] = None, publisher_id: Optional[str] = None) -> None:
    """
    Add a book to a series.
    
    Args:
        registry: SeriesRegistry instance
        series_id: ID of the series
        book_id: ID of the book
        sequence_number: Optional sequence number
        publisher_id: Optional ID of the publisher adding the book
    """
    try:
        # Add the book to the series
        assigned_sequence = registry.add_book_to_series(series_id, book_id, sequence_number, publisher_id)
        print(f"Added book '{book_id}' to series with sequence number: {assigned_sequence}")
        
    except SeriesNotFoundError:
        print(f"Error: Series with ID '{series_id}' not found.")
        sys.exit(1)
    except SeriesAccessDeniedError:
        print(f"Error: Publisher '{publisher_id}' does not have access to series '{series_id}'.")
        sys.exit(1)
    except SequenceNumberConflictError:
        print(f"Error: Sequence number {sequence_number} is already taken in series '{series_id}'.")
        sys.exit(1)


def remove_book(registry: SeriesRegistry, series_id: str, book_id: str, 
               publisher_id: Optional[str] = None) -> None:
    """
    Remove a book from a series.
    
    Args:
        registry: SeriesRegistry instance
        series_id: ID of the series
        book_id: ID of the book
        publisher_id: Optional ID of the publisher removing the book
    """
    try:
        # Remove the book from the series
        result = registry.remove_book_from_series(series_id, book_id, publisher_id)
        
        if result:
            print(f"Removed book '{book_id}' from series '{series_id}'.")
        else:
            print(f"Book '{book_id}' not found in series '{series_id}'.")
        
    except SeriesNotFoundError:
        print(f"Error: Series with ID '{series_id}' not found.")
        sys.exit(1)
    except SeriesAccessDeniedError:
        print(f"Error: Publisher '{publisher_id}' does not have access to series '{series_id}'.")
        sys.exit(1)


def show_statistics(registry: SeriesRegistry) -> None:
    """
    Show statistics about the series registry.
    
    Args:
        registry: SeriesRegistry instance
    """
    # Get statistics
    stats = registry.get_statistics()
    
    # Print statistics
    print("Series Registry Statistics:")
    print(f"Total Series: {stats['total_series']}")
    print(f"Total Books: {stats['total_books']}")
    print(f"Publishers: {', '.join(stats['publishers'])}")
    print(f"Multi-Publisher Series: {stats['multi_publisher_series']}")
    
    print("\nSeries by Size:")
    for size, count in sorted(stats['series_by_size'].items()):
        print(f"- {size} books: {count} series")


def export_registry(registry: SeriesRegistry, output_file: str) -> None:
    """
    Export the series registry to a JSON file.
    
    Args:
        registry: SeriesRegistry instance
        output_file: Path to the output file
    """
    try:
        # Convert series and series books to dictionaries
        series_dicts = [series.to_dict() for series in registry.series.values()]
        series_book_dicts = []
        for books in registry.series_books.values():
            series_book_dicts.extend([book.to_dict() for book in books])
        
        # Create export data
        export_data = {
            "series": series_dicts,
            "series_books": series_book_dicts
        }
        
        # Write to file
        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Exported series registry to {output_file}")
        
    except Exception as e:
        print(f"Error exporting registry: {e}")
        sys.exit(1)


def import_registry(registry: SeriesRegistry, input_file: str) -> None:
    """
    Import series data into the registry from a JSON file.
    
    Args:
        registry: SeriesRegistry instance
        input_file: Path to the input file
    """
    try:
        # Read from file
        with open(input_file, "r") as f:
            import_data = json.load(f)
        
        # Import series
        series_count = 0
        for series_data in import_data.get("series", []):
            try:
                # Check if series already exists
                existing_series = registry.get_series_by_name(series_data["name"], series_data["publisher_id"])
                
                if existing_series:
                    # Update existing series
                    registry.update_series(existing_series[0].id, series_data)
                else:
                    # Create new series
                    registry.create_series(
                        name=series_data["name"],
                        publisher_id=series_data["publisher_id"],
                        multi_publisher=series_data.get("multi_publisher", False),
                        description=series_data.get("description")
                    )
                
                series_count += 1
                
            except Exception as e:
                print(f"Error importing series {series_data.get('name', 'unknown')}: {e}")
        
        # Import series books
        book_count = 0
        for book_data in import_data.get("series_books", []):
            try:
                # Add book to series
                registry.add_book_to_series(
                    series_id=book_data["series_id"],
                    book_id=book_data["book_id"],
                    sequence_number=book_data["sequence_number"]
                )
                
                book_count += 1
                
            except Exception as e:
                print(f"Error importing book {book_data.get('book_id', 'unknown')}: {e}")
        
        print(f"Imported {series_count} series and {book_count} books")
        
    except Exception as e:
        print(f"Error importing registry: {e}")
        sys.exit(1)


def main():
    """Main function for the series CLI."""
    parser = argparse.ArgumentParser(description="Series Metadata Management CLI")
    parser.add_argument("--registry", default="data/series_registry.json", help="Path to the series registry file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all series")
    list_parser.add_argument("--publisher", help="Filter by publisher ID")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show series details")
    show_parser.add_argument("series_id", help="ID of the series to show")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new series")
    create_parser.add_argument("name", help="Name of the series")
    create_parser.add_argument("publisher", help="ID of the publisher")
    create_parser.add_argument("--multi-publisher", action="store_true", help="Allow multiple publishers")
    create_parser.add_argument("--description", help="Description of the series")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update a series")
    update_parser.add_argument("series_id", help="ID of the series to update")
    update_parser.add_argument("--name", help="New name for the series")
    update_parser.add_argument("--multi-publisher", action="store_true", help="Allow multiple publishers")
    update_parser.add_argument("--description", help="New description for the series")
    update_parser.add_argument("--publisher", help="ID of the publisher making the update")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a series")
    delete_parser.add_argument("series_id", help="ID of the series to delete")
    delete_parser.add_argument("--publisher", help="ID of the publisher making the deletion")
    delete_parser.add_argument("--force", action="store_true", help="Force deletion even if books are assigned")
    
    # Add book command
    add_parser = subparsers.add_parser("add-book", help="Add a book to a series")
    add_parser.add_argument("series_id", help="ID of the series")
    add_parser.add_argument("book_id", help="ID of the book")
    add_parser.add_argument("--sequence", type=int, help="Sequence number for the book")
    add_parser.add_argument("--publisher", help="ID of the publisher adding the book")
    
    # Remove book command
    remove_parser = subparsers.add_parser("remove-book", help="Remove a book from a series")
    remove_parser.add_argument("series_id", help="ID of the series")
    remove_parser.add_argument("book_id", help="ID of the book")
    remove_parser.add_argument("--publisher", help="ID of the publisher removing the book")
    
    # Statistics command
    subparsers.add_parser("stats", help="Show statistics about the series registry")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export the series registry to a JSON file")
    export_parser.add_argument("output_file", help="Path to the output file")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import series data into the registry from a JSON file")
    import_parser.add_argument("input_file", help="Path to the input file")
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Create registry
    registry = SeriesRegistry(args.registry)
    
    # Execute command
    if args.command == "list":
        list_series(registry, args.publisher)
    elif args.command == "show":
        show_series(registry, args.series_id)
    elif args.command == "create":
        create_series(registry, args.name, args.publisher, args.multi_publisher, args.description)
    elif args.command == "update":
        updates = {}
        if args.name:
            updates["name"] = args.name
        if args.description:
            updates["description"] = args.description
        if args.multi_publisher:
            updates["multi_publisher"] = True
        
        update_series(registry, args.series_id, updates, args.publisher)
    elif args.command == "delete":
        delete_series(registry, args.series_id, args.publisher, args.force)
    elif args.command == "add-book":
        add_book(registry, args.series_id, args.book_id, args.sequence, args.publisher)
    elif args.command == "remove-book":
        remove_book(registry, args.series_id, args.book_id, args.publisher)
    elif args.command == "stats":
        show_statistics(registry)
    elif args.command == "export":
        export_registry(registry, args.output_file)
    elif args.command == "import":
        import_registry(registry, args.input_file)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()