# /Users/fred/xcu_my_apps/nimble/codexes-factory/tools/report_isbns.py
# version 1.0.0
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path to allow for relative imports if needed in the future
sys.path.insert(0, str(Path(__file__).parent.parent))


def report_assigned_isbns(db_file: Path, count: int):
    """
    Loads the ISBN database, finds assigned ISBNs, and reports on the most recent N.

    Args:
        db_file (Path): The path to the ISBN database JSON file.
        count (int): The number of recent assignments to report.
    """
    if not db_file.exists():
        print(f"Error: Database file not found at {db_file}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON from {db_file}", file=sys.stderr)
        sys.exit(1)

    assigned_isbns = []
    for publisher_id, isbns in data.items():
        for isbn_data in isbns:
            if isbn_data.get('status') == 'assigned' and 'assignment_date' in isbn_data:
                # Add publisher_id for context
                isbn_data['publisher_id'] = publisher_id
                assigned_isbns.append(isbn_data)

    if not assigned_isbns:
        print("No assigned ISBNs found in the database.")
        return

    # Sort by assignment_date in reverse chronological order
    assigned_isbns.sort(
        key=lambda x: datetime.fromisoformat(x['assignment_date'].replace('Z', '+00:00')),
        reverse=True
    )

    # Get the top N results
    results_to_show = assigned_isbns[:count]

    print(f"--- Showing the {len(results_to_show)} Most Recently Assigned ISBNs ---")
    print("-" * 70)
    for item in results_to_show:
        date_str = datetime.fromisoformat(item['assignment_date'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
        print(f"  ISBN:          {item.get('isbn13', 'N/A')}")
        print(f"  Title:         {item.get('title', 'N/A')}")
        print(f"  Author:        {item.get('author', 'N/A')}")
        print(f"  Assigned On:   {date_str}")
        print(f"  Publisher:     {item.get('publisher_id', 'N/A')}")
        print("-" * 70)


def main():
    """Main function to parse arguments and run the report."""
    parser = argparse.ArgumentParser(
        description="Report on the most recently assigned ISBNs from the database.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=10,
        help="The number of recent assignments to show."
    )
    parser.add_argument(
        "-db", "--db-file",
        default="data/isbn_database.json",
        help="Path to the ISBN database JSON file."
    )
    args = parser.parse_args()

    report_assigned_isbns(db_file=Path(args.db_file), count=args.count)


if __name__ == "__main__":
    main()