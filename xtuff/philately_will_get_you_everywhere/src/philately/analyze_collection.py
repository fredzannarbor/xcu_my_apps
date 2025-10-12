import pandas as pd
import io
import re
import logging

# --- Logging Setup ---
# This helps in debugging by printing informational messages.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def analyze_philately_summary(csv_content: str):
    """
    Reads philately data from a CSV string, analyzes it, and prints a summary for each album.

    This function is designed to be robust, handling data cleaning and providing
    both detailed and aggregated analysis.

    Args:
        csv_content: A string containing the CSV data.

    Returns:
        A pandas DataFrame containing the aggregated analysis for each album,
        or None if an error occurs.
    """
    print("--- Starting Philately Collection Analysis ---\n")

    try:
        # Use io.StringIO to read the string content as if it were a file
        df = pd.read_csv(io.StringIO(csv_content))

        # --- Data Cleaning and Preparation ---
        # This section ensures the data is in the correct format for calculations.

        def parse_estimated_value(value_str):
            """
            Extracts a numeric value from the 'estimated_value' column.
            It handles currency symbols and value ranges (e.g., "$10-$20")
            by taking the lower bound of the range.
            """
            if pd.isna(value_str) or not isinstance(value_str, str):
                return 0.0

            # Remove currency symbols and spaces for clean parsing
            cleaned_value = re.sub(r'[$\s]', '', str(value_str))

            # Handle ranges by taking the first number
            if '-' in cleaned_value:
                parts = cleaned_value.split('-')
                try:
                    # Return the first part of the range as a float
                    return float(parts[0])
                except (ValueError, IndexError):
                    return 0.0
            else:
                try:
                    return float(cleaned_value)
                except ValueError:
                    return 0.0

        # Apply the parsing function to create a new numeric column for calculations
        df['estimated_value_numeric'] = df['estimated_value'].apply(parse_estimated_value)

        # Ensure 'year' is numeric, converting any non-numeric values to NaN (Not a Number)
        df['year_numeric'] = pd.to_numeric(df['year'], errors='coerce')

        # Validate that the required 'album' column exists
        if 'album' not in df.columns:
            logger.error("CSV data must contain an 'album' column for analysis.")
            return None

        # --- Analysis ---
        # Group data by the 'album' column to analyze each album separately.
        grouped_by_album = df.groupby('album')

        # Perform aggregation to calculate key statistics for each album.
        analysis = grouped_by_album.agg(
            total_stamps=('album', 'size'),
            total_catalogue_value=('estimated_value_numeric', 'sum'),
            average_stamp_value=('estimated_value_numeric', 'mean'),
            unique_countries=('nationality', 'nunique'),
            earliest_year=('year_numeric', 'min'),
            latest_year=('year_numeric', 'max')
        )

        # --- Print Detailed Per-Album Analysis ---
        print("--- Detailed Analysis Per Album ---\n")
        for album_name, album_group in grouped_by_album:
            print(f"Album: {album_name}")
            print("=" * (len(album_name) + 7))

            # Get the calculated stats for the current album from our analysis DataFrame
            album_stats = analysis.loc[album_name]

            print(f"  - Total Stamps: {int(album_stats['total_stamps'])}")
            print(f"  - Total Estimated Value: ${album_stats['total_catalogue_value']:.2f}")
            print(f"  - Average Stamp Value: ${album_stats['average_stamp_value']:.2f}")
            print(f"  - Number of Unique Countries: {int(album_stats['unique_countries'])}")

            # Handle cases where year data might be missing
            earliest = int(album_stats['earliest_year']) if pd.notna(album_stats['earliest_year']) else 'N/A'
            latest = int(album_stats['latest_year']) if pd.notna(album_stats['latest_year']) else 'N/A'
            print(f"  - Year Range of Stamps: {earliest} - {latest}")

            # Additional analysis: Condition breakdown
            condition_counts = album_group['condition'].value_counts().to_dict()
            print("  - Condition Breakdown:")
            for condition, count in condition_counts.items():
                print(f"    - {str(condition).strip()}: {count} stamp(s)")

            # Additional analysis: High-value items
            high_value_stamps = album_group[album_group['estimated_value_numeric'] > 50]
            if not high_value_stamps.empty:
                print(f"  - High-Value Stamps (> $50): {len(high_value_stamps)} item(s)")
                for _, stamp_row in high_value_stamps.iterrows():
                    print(f"    - {stamp_row['common_name']} ({stamp_row['nationality']}, {stamp_row['year']}): ${stamp_row['estimated_value_numeric']:.2f}")
            else:
                print("  - No high-value stamps (> $50) in this album.")

            print("-" * 30 + "\n")

        return analysis

    except pd.errors.EmptyDataError:
        logger.error("The provided CSV data is empty.")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during analysis: {e}", exc_info=True)
        return None

# --- Main Execution Block ---
if __name__ == "__main__":
    # Define the path to your master CSV file.
    # This script assumes 'test_master.csv' is in the same directory.
    # You can change this to the full path if it's located elsewhere.
    csv_file_path = 'resources/data_tables/test_master.csv'

    try:
        # Read the entire content of the CSV file into a string.
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            csv_data = f.read()

        # Run the analysis function with the data from the file.
        analysis_results = analyze_philately_summary(csv_data)

        # If the analysis was successful, print the final aggregated table.
        if analysis_results is not None:
            print("\n--- Aggregated Summary Table ---")
            # .round(2) is used for cleaner display of float values.
            print(analysis_results.round(2))
            print("\n--- Analysis Complete ---")

    except FileNotFoundError:
        logger.error(f"Error: The file '{csv_file_path}' was not found.")
        print(f"Error: The file '{csv_file_path}' was not found.")
        print("Please make sure the CSV file is in the correct directory or update the path in the script.")
    except Exception as e:
        logger.error(f"An error occurred while reading or processing the file: {e}", exc_info=True)
        print(f"An error occurred: {e}")
