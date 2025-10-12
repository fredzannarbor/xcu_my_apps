# Philately Collection Management System

***Save days or weeks of tedious data entry with tweezers and a
magnifying glass.***

## Overview

This project is a Python-based command-line system for managing a
philatelic (stamp) collection. Take snaps of every page in your album(s) with your digital camera, then watch and marvel as the script uses AI vision understanding and deep research to process entire directories of stamp album images, extract detailed metadata, and generate a comprehensive, queryable digital inventory. The model provides tools to analyze, visualize, and report on the stamps, enhancing your enjoyment of their beauty and  history, while increasing your understanding the philatelic and monetary value of your collection.

Key features include:

-   **Multi-Model AI Processing**: Analyzes stamp images to extract
    details like country, year, and condition using a two-pass system
    with configurable "low-cost" and "high-cost" vision models.
-   **Data Enrichment**: Uses powerful text models to enrich the initial
    data with estimated values, historical context, and philatelic
    remarks.
-   **False Positive Detection**: Includes a dedicated phase to
    re-examine high-value items and automatically flag illustrations or
    other non-stamp entities.
-   **Persistent, Auditable Storage**: Maintains a master inventory in
    `master_inventory.csv` that includes all processed stamps,
    deacquired items, and verification results.
-   **Comprehensive Reporting**: Generates detailed JSON summaries,
    high-value reports, and content-ready CSVs for platforms like
    Substack.
-   **Modular, Phase-Based Execution**: Allows you to run the entire
    pipeline or specific phases (e.g., analysis, enrichment, reporting)
    independently.
-   **Command-Line and GUI Interfaces**: Provides both a command-line tool (`philately`) for automated processing and a Streamlit-based GUI (`philately-ui`) for interactive use.

## Prerequisites

-   **Python**: Version 3.12 or higher.
-   **API Keys**: At least one API key for a supported provider (e.g.,
    Google, xAI). These should be set in a `.env` file.
-   **System Dependencies**:
    -   On Ubuntu/Debian: `sudo apt-get install libopencv-dev`.
    -   On macOS: `brew install opencv`.

## Installation

1.  **Clone the Repository**:

        git clone <repository-url>
        cd <repository-directory>

2.  **Create a Virtual Environment**:

        python3 -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate

3.  **Install the Package**:

        pip install .

4.  **Set Up Environment Variables**:

    Create a `.env` file in the project root and add your API key(s):

        echo "GOOGLE_API_KEY=your-google-api-key" > .env
        echo "XAI_API_KEY=your-xai-api-key" >> .env

5.  **Prepare Directory Structure**:
    -   Place stamp images in a directory (e.g., `stamps/`), organized
        into subdirectories for each album (e.g.,
        `stamps/Isle of Man/`).
    -   The `output` directory will be created automatically to store
        all generated files.

## Usage

This package provides two primary entry points: a command-line interface (CLI) and a graphical user interface (GUI).

### Command-Line Interface (CLI)

The `philately` command allows you to run the entire pipeline or specific phases using command-line flags.

#### Command-Line Flags

The command-line flags are the same as described in the table below.

### Graphical User Interface (GUI)

The `philately-ui` command launches a Streamlit-based web interface that allows you to configure and run the processing pipeline interactively.

    philately-ui

### Example Commands (CLI)

**1. Run the full pipeline on all images:**

    philately --image-dir ./stamps --output-dir ./output

**2. Run only the image analysis phase on the first 10 images:**

    philately --run-analysis --max-images 10

**3. Run the false-positive check on the top 3 most valuable stamps with
debug logging:**

    philately --run-false-positive-check --false-positive-check-limit 3 --debug

**4. Generate a Substack export with the top 20 most valuable items:**

    philately --run-substack-export --substack-items 20

**5. Re-run only the enrichment and summary phases:**

    philately --run-enrichment --run-summaries

### Command-Line Flags

<table>
<thead>
<tr>
<th>Flag</th>
<th>Default</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>--image-dir</code></td>
<td><code>stamps</code></td>
<td>Directory containing stamp images organized in album folders.</td>
</tr>
<tr>
<td><code>--output-dir</code></td>
<td><code>output</code></td>
<td>Directory to save all outputs.</td>
</tr>
<tr>
<td><code>--confidence-threshold</code></td>
<td><code>5</code></td>
<td>Confidence score (1-7) below which to trigger re-analysis with a
high-cost model.</td>
</tr>
<tr>
<td><code>--max-images</code></td>
<td><code>None</code></td>
<td>Limit the number of images to process for testing.</td>
</tr>
<tr>
<td><code>--high-value-threshold</code></td>
<td><code>1000</code></td>
<td>USD threshold to consider a stamp as high-value for reporting.</td>
</tr>
<tr>
<td><code>--debug</code></td>
<td><code>False</code></td>
<td>Enable debug-level logging for verbose output, including API
payloads.</td>
</tr>
<tr>
<td><code>--low-cost-model</code></td>
<td><code>gemini/gemini-1.5-flash-latest</code></td>
<td>The vision model for the initial, low-cost pass.</td>
</tr>
<tr>
<td><code>--high-cost-model</code></td>
<td><code>gemini/gemini-1.5-pro-latest</code></td>
<td>The vision model for the high-confidence re-analysis pass.</td>
</tr>
<tr>
<td><code>--narrative-model</code></td>
<td><code>gemini/gemini-1.5-pro-latest</code></td>
<td>The text model for enrichment and summaries.</td>
</tr>
<tr>
<td><code>--collection-summary-model</code></td>
<td><code>gemini/gemini-1.5-pro-latest</code></td>
<td>The high-context model for the final collection-wide summary.</td>
</tr>
<tr>
<td><code>--run-analysis</code></td>
<td><code>False</code></td>
<td>Run only the image analysis phase.</td>
</tr>
<tr>
<td><code>--run-enrichment</code></td>
<td><code>False</code></td>
<td>Run only the philatelic enrichment phase.</td>
</tr>
<tr>
<td><code>--run-summaries</code></td>
<td><code>False</code></td>
<td>Run the full clustering and summary phase.</td>
</tr>
<tr>
<td><code>--run-high-value-report</code></td>
<td><code>False</code></td>
<td>Run only the high-value stamp report generation phase.</td>
</tr>
<tr>
<td><code>--run-collection-summary-only</code></td>
<td><code>False</code></td>
<td>Run only the final collection-wide summary generation.</td>
</tr>
<tr>
<td><code>--run-false-positive-check</code></td>
<td><code>False</code></td>
<td>Run a re-examination of high-value stamps to find false
positives.</td>
</tr>
<tr>
<td><code>--false-positive-check-limit</code></td>
<td><code>5</code></td>
<td>Limit the number of stamps to check in the false-positive phase (0
for all).</td>
</tr>
<tr>
<td><code>--run-substack-export</code></td>
<td><code>False</code></td>
<td>Generate a CSV export formatted for Substack posts.</td>
</tr>
<tr>
<td><code>--substack-items</code></td>
<td><code>10</code></td>
<td>Number of top items to include in the Substack export (0 for
all).</td>
</tr>
</tbody>
</table>

## Output Files

All outputs are saved to the directory specified by `--output-dir`.

-   `master_inventory.csv`: The master database of all stamps, including
    detailed analysis and verification data.
-   `stamp_inventory.json`: A structured JSON file containing all data,
    including collection-wide statistics and narrative summaries.
-   `false_positive_check_report.csv`: A summary of high-value items
    that were checked for authenticity.
-   `high_value_summary.csv`: A CSV listing all stamps identified as
    high-value.
-   `substack_export.csv`: A CSV formatted for easy import into content
    platforms like Substack.
-   `cropped_entities/`: Directory of cropped images for each identified
    stamp.
-   `thumbnails/`: Directory of 100x100px thumbnails for each stamp.
-   `high_value_reports/`: Individual Markdown reports for each
    high-value stamp.

## Example Data Records

### 1. Master Inventory Record (`master_inventory.csv`)

A single row contains the complete data for one stamp.

<table>
<thead>
<tr>
<th>stamp_id</th>
<th>album</th>
<th>page_filename</th>
<th>common_name</th>
<th>nationality</th>
<th>year</th>
<th>face_value</th>
<th>condition</th>
<th>confidence</th>
<th>estimated_value_high</th>
<th>is_verified_real</th>
<th>verification_reason</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>a1b2c3d4-...</code></td>
<td><code>Isle of Man</code></td>
<td><code>IMG_1172.jpeg</code></td>
<td><code>1973 Manx Cat</code></td>
<td><code>Isle of Man</code></td>
<td><code>1973</code></td>
<td><code>3p</code></td>
<td><code>Mint</code></td>
<td><code>7</code></td>
<td><code>15</code></td>
<td><code>True</code></td>
<td><code>This appears to be a genuine, mounted stamp with clear perforations and color.</code></td>
</tr>
</tbody>
</table>

### 2. Cluster Summary (`stamp_inventory.json`)

Summaries provide statistics and a narrative for a specific group of
stamps (e.g., an album). #big

    {
        "album_Isle_of_Man": {
            "statistics": {
                "item_count": 58,
                "album_count": 1,
                "countries_represented": 1,
                "year_range": "1973 - 1998",
                "total_value_low": 150,
                "total_value_high": 450,
                "condition_distribution": {
                    "Mint": 45,
                    "Used": 13
                }
            },
            "narrative_summary": "This cluster from the 'Isle of Man' album represents a strong collection of modern issues, primarily from the 1970s and 1980s. The thematic focus is on local culture, transportation, and fauna, with the 'Manx Cat' and 'TT Races' series being prominent highlights. The overall condition is excellent, with a majority of items in mint condition. A notable gap is the absence of earlier Victorian-era issues."
        }
    }

### 3. False Positive Check Report (`false_positive_check_report.csv`)

This report provides a clear audit trail for the verification process.

<table>
<thead>
<tr>
<th>stamp_id</th>
<th>common_name</th>
<th>estimated_value_high</th>
<th>page_filename</th>
<th>is_verified_real</th>
<th>cropped_image_path</th>
<th>verification_reason</th>
<th>action_taken</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>e5f6g7h8-...</code></td>
<td><code>Penny Black</code></td>
<td><code>2500</code></td>
<td><code>IMG_1245.JPG</code></td>
<td><code>False</code></td>
<td><code>cropped_entities/e5f6g7h8-..._cropped.jpg</code></td>
<td><code>The image is a black and white printed illustration, lacking color and physical depth.</code></td>
<td><code>Marked as deacquired (illustration)</code></td>
</tr>
</tbody>
</table>