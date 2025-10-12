#!/usr/bin/env python3
"""
Schedule File Converter - Convert ISBN schedule files between CSV and JSON formats.
"""
import argparse
import sys
import os
import json
import csv
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScheduleConverter:
    """Convert schedule files between CSV and JSON formats"""
    
    def __init__(self):
        self.supported_fields = [
            'stream', 'title','description', 'special_requests', 'recommended_sources', 'book_id', 'scheduled_date', 'isbn',
            'imprint', 'publisher', 'format', 'priority', 'notes']

    def csv_to_json(self, csv_file: str, json_file: str, pretty: bool = True) -> bool:
        """Convert CSV schedule file to JSON format"""
        try:
            books = []
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):
                    book = {}
                    
                    # Process each field
                    for field in self.supported_fields:
                        value = row.get(field, '').strip()
                        
                        # Convert priority to integer if present
                        if field == 'priority' and value:
                            try:
                                book[field] = int(value)
                            except ValueError:
                                logger.warning(f"Row {row_num}: Invalid priority '{value}', using 1")
                                book[field] = 1
                        else:
                            book[field] = value
                    
                    # Only add books with required fields
                    if book.get('title') and book.get('book_id') and book.get('scheduled_date'):
                        books.append(book)
                    else:
                        logger.warning(f"Row {row_num}: S   kipping incomplete record")
            
            # Write JSON file
            with open(json_file, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(books, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(books, f, ensure_ascii=False)
            
            logger.info(f"Converted {len(books)} books from CSV to JSON")
            return True
            
        except Exception as e:
            logger.error(f"Error converting CSV to JSON: {e}")
            return False
    
    def json_to_csv(self, json_file: str, csv_file: str) -> bool:
        """Convert JSON schedule file to CSV format"""
        try:
            # Read JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both single object and array
            if isinstance(data, dict):
                books = [data]
            elif isinstance(data, list):
                books = data
            else:
                raise ValueError("JSON must contain an object or array of objects")
            
            # Write CSV file
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.supported_fields)
                writer.writeheader()
                
                for book in books:
                    # Create row with all supported fields
                    row = {}
                    for field in self.supported_fields:
                        value = book.get(field, '')
                        
                        # Convert priority to string
                        if field == 'priority' and isinstance(value, int):
                            row[field] = str(value)
                        else:
                            row[field] = str(value) if value is not None else ''
                    
                    writer.writerow(row)
            
            logger.info(f"Converted {len(books)} books from JSON to CSV")
            return True
            
        except Exception as e:
            logger.error(f"Error converting JSON to CSV: {e}")
            return False
    
    def validate_schedule_file(self, file_path: str) -> Dict[str, Any]:
        """Validate a schedule file and return statistics"""
        try:
            stats = {
                'total_books': 0,
                'valid_books': 0,
                'manual_isbns': 0,
                'auto_isbns': 0,
                'missing_required': 0,
                'invalid_isbns': 0,
                'errors': []
            }
            
            if file_path.lower().endswith('.csv'):
                books = self._read_csv_books(file_path)
            elif file_path.lower().endswith('.json'):
                books = self._read_json_books(file_path)
            else:
                raise ValueError("Unsupported file format. Use .csv or .json")
            
            stats['total_books'] = len(books)
            
            for idx, book in enumerate(books, start=1):
                # Check required fields
                required_fields = ['title', 'book_id', 'scheduled_date']
                missing_fields = [field for field in required_fields if not book.get(field, '').strip()]
                
                if missing_fields:
                    stats['missing_required'] += 1
                    stats['errors'].append(f"Book {idx}: Missing required fields: {', '.join(missing_fields)}")
                    continue
                
                stats['valid_books'] += 1
                
                # Check ISBN
                isbn = book.get('isbn', '').strip()
                if isbn:
                    if len(isbn) == 13 and isbn.isdigit():
                        stats['manual_isbns'] += 1
                    else:
                        stats['invalid_isbns'] += 1
                        stats['errors'].append(f"Book {idx}: Invalid ISBN format '{isbn}'")
                else:
                    stats['auto_isbns'] += 1
            
            return stats
            
        except Exception as e:
            return {
                'total_books': 0,
                'valid_books': 0,
                'manual_isbns': 0,
                'auto_isbns': 0,
                'missing_required': 0,
                'invalid_isbns': 0,
                'errors': [f"Error reading file: {e}"]
            }
    
    def _read_csv_books(self, csv_file: str) -> List[Dict[str, Any]]:
        """Read books from CSV file"""
        books = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                books.append(dict(row))
        return books
    
    def _read_json_books(self, json_file: str) -> List[Dict[str, Any]]:
        """Read books from JSON file"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            return data
        else:
            raise ValueError("JSON must contain an object or array of objects")
    
    def merge_schedule_files(self, file1: str, file2: str, output_file: str, 
                           output_format: str = 'csv') -> bool:
        """Merge two schedule files into one"""
        try:
            # Read both files
            books1 = []
            books2 = []
            
            if file1.lower().endswith('.csv'):
                books1 = self._read_csv_books(file1)
            elif file1.lower().endswith('.json'):
                books1 = self._read_json_books(file1)
            
            if file2.lower().endswith('.csv'):
                books2 = self._read_csv_books(file2)
            elif file2.lower().endswith('.json'):
                books2 = self._read_json_books(file2)
            
            # Merge books (file2 takes precedence for duplicates)
            merged_books = {}
            
            # Add books from first file
            for book in books1:
                book_id = book.get('book_id', '').strip()
                if book_id:
                    merged_books[book_id] = book
            
            # Add/update books from second file
            for book in books2:
                book_id = book.get('book_id', '').strip()
                if book_id:
                    merged_books[book_id] = book
            
            # Convert to list
            final_books = list(merged_books.values())
            
            # Write output file
            if output_format.lower() == 'csv':
                self._write_csv_books(final_books, output_file)
            elif output_format.lower() == 'json':
                self._write_json_books(final_books, output_file)
            else:
                raise ValueError("Output format must be 'csv' or 'json'")
            
            logger.info(f"Merged {len(books1)} + {len(books2)} books into {len(final_books)} unique books")
            return True
            
        except Exception as e:
            logger.error(f"Error merging files: {e}")
            return False
    
    def _write_csv_books(self, books: List[Dict[str, Any]], csv_file: str):
        """Write books to CSV file"""
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.supported_fields)
            writer.writeheader()
            
            for book in books:
                row = {}
                for field in self.supported_fields:
                    value = book.get(field, '')
                    row[field] = str(value) if value is not None else ''
                writer.writerow(row)
    
    def _write_json_books(self, books: List[Dict[str, Any]], json_file: str):
        """Write books to JSON file"""
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(books, f, indent=2, ensure_ascii=False)

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Schedule File Converter - Convert between CSV and JSON formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert CSV to JSON
  python schedule_converter.py csv-to-json --input schedule.csv --output schedule.json
  
  # Convert JSON to CSV
  python schedule_converter.py json-to-csv --input schedule.json --output schedule.csv
  
  # Validate a schedule file
  python schedule_converter.py validate --file schedule.csv
  
  # Merge two schedule files
  python schedule_converter.py merge --file1 schedule1.csv --file2 schedule2.json --output merged.csv --format csv
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # CSV to JSON command
    csv_to_json_parser = subparsers.add_parser('csv-to-json', help='Convert CSV to JSON')
    csv_to_json_parser.add_argument('--input', '-i', required=True, help='Input CSV file')
    csv_to_json_parser.add_argument('--output', '-o', required=True, help='Output JSON file')
    csv_to_json_parser.add_argument('--compact', action='store_true', help='Compact JSON output (no pretty printing)')
    
    # JSON to CSV command
    json_to_csv_parser = subparsers.add_parser('json-to-csv', help='Convert JSON to CSV')
    json_to_csv_parser.add_argument('--input', '-i', required=True, help='Input JSON file')
    json_to_csv_parser.add_argument('--output', '-o', required=True, help='Output CSV file')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate schedule file')
    validate_parser.add_argument('--file', required=True, help='Schedule file to validate')
    validate_parser.add_argument('--show-errors', action='store_true', help='Show detailed error messages')
    
    # Merge command
    merge_parser = subparsers.add_parser('merge', help='Merge two schedule files')
    merge_parser.add_argument('--file1', required=True, help='First schedule file')
    merge_parser.add_argument('--file2', required=True, help='Second schedule file')
    merge_parser.add_argument('--output', required=True, help='Output file')
    merge_parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='Output format')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    converter = ScheduleConverter()
    
    try:
        if args.command == 'csv-to-json':
            if not os.path.exists(args.input):
                print(f"❌ Input file not found: {args.input}")
                sys.exit(1)
            
            success = converter.csv_to_json(args.input, args.output, pretty=not args.compact)
            if success:
                print(f"✅ Successfully converted {args.input} to {args.output}")
            else:
                print("❌ Conversion failed")
                sys.exit(1)
        
        elif args.command == 'json-to-csv':
            if not os.path.exists(args.input):
                print(f"❌ Input file not found: {args.input}")
                sys.exit(1)
            
            success = converter.json_to_csv(args.input, args.output)
            if success:
                print(f"✅ Successfully converted {args.input} to {args.output}")
            else:
                print("❌ Conversion failed")
                sys.exit(1)
        
        elif args.command == 'validate':
            if not os.path.exists(args.file):
                print(f"❌ File not found: {args.file}")
                sys.exit(1)
            
            stats = converter.validate_schedule_file(args.file)
            
            print(f"📊 Validation Results for {args.file}:")
            print(f"   📚 Total books: {stats['total_books']}")
            print(f"   ✅ Valid books: {stats['valid_books']}")
            print(f"   🎯 Manual ISBNs: {stats['manual_isbns']}")
            print(f"   🤖 Auto ISBNs: {stats['auto_isbns']}")
            print(f"   ❌ Missing required fields: {stats['missing_required']}")
            print(f"   📖 Invalid ISBNs: {stats['invalid_isbns']}")
            
            if stats['errors']:
                print(f"   🚨 Total errors: {len(stats['errors'])}")
                if args.show_errors:
                    print("\n📋 Error Details:")
                    for error in stats['errors']:
                        print(f"      • {error}")
            
            if stats['valid_books'] == stats['total_books'] and not stats['errors']:
                print("\n🎉 File is valid and ready for import!")
            else:
                print(f"\n⚠️  File has issues that should be addressed before import")
        
        elif args.command == 'merge':
            if not os.path.exists(args.file1):
                print(f"❌ File not found: {args.file1}")
                sys.exit(1)
            if not os.path.exists(args.file2):
                print(f"❌ File not found: {args.file2}")
                sys.exit(1)
            
            success = converter.merge_schedule_files(args.file1, args.file2, args.output, args.format)
            if success:
                print(f"✅ Successfully merged {args.file1} and {args.file2} into {args.output}")
            else:
                print("❌ Merge failed")
                sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()