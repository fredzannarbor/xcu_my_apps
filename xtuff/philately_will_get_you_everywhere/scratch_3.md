<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Philately Collection Management System</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
            line-height: 1.6;
            color: #24292f;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
        }
        h1, h2, h3 {
            border-bottom: 1px solid #d0d7de;
            padding-bottom: 0.3em;
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
        }
        h1 { font-size: 2em; }
        h2 { font-size: 1.5em; }
        h3 { font-size: 1.25em; }
        p { margin-bottom: 16px; }
        ul, ol {
            padding-left: 2em;
            margin-bottom: 16px;
        }
        li { margin-bottom: 0.5em; }
        code {
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
            font-size: 85%;
            background-color: rgba(175, 184, 193, 0.2);
            border-radius: 6px;
            padding: 0.2em 0.4em;
        }
        pre {
            background-color: #f6f8fa;
            border-radius: 6px;
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            line-height: 1.45;
        }
        pre code {
            background-color: transparent;
            padding: 0;
            border-radius: 0;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 16px;
            display: block;
            overflow: auto;
        }
        th, td {
            border: 1px solid #d0d7de;
            padding: 8px 12px;
            text-align: left;
        }
        th {
            background-color: #f6f8fa;
            font-weight: 600;
        }
        tr:nth-child(even) {
            background-color: #f6f8fa;
        }
        a {
            color: #0969da;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>

    <h1>Philately Collection Management System</h1>
    <p><strong><em>Save days or weeks of tedious data entry with tweezers and a magnifying glass.</em></strong></p>

    <h2>Overview</h2>
    <p>This project is a Python-based command-line system for managing a philatelic (stamp) collection. It leverages modern AI to process entire directories of stamp album images, extract detailed metadata, and generate a comprehensive, queryable inventory. By using <code>litellm</code>, it supports multiple AI model providers (e.g., Google Gemini, xAI Grok) for maximum flexibility and cost-effectiveness.</p>
    <p>Key features include:</p>
    <ul>
        <li><strong>Multi-Model AI Processing</strong>: Analyzes stamp images to extract details like country, year, and condition using a two-pass system with configurable "low-cost" and "high-cost" vision models.</li>
        <li><strong>Data Enrichment</strong>: Uses powerful text models to enrich the initial data with estimated values, historical context, and philatelic remarks.</li>
        <li><strong>False Positive Detection</strong>: Includes a dedicated phase to re-examine high-value items and automatically flag illustrations or other non-stamp entities.</li>
        <li><strong>Persistent, Auditable Storage</strong>: Maintains a master inventory in <code>master_inventory.csv</code> that includes all processed stamps, deacquired items, and verification results.</li>
        <li><strong>Comprehensive Reporting</strong>: Generates detailed JSON summaries, high-value reports, and content-ready CSVs for platforms like Substack.</li>
        <li><strong>Modular, Phase-Based Execution</strong>: Allows you to run the entire pipeline or specific phases (e.g., analysis, enrichment, reporting) independently.</li>
    </ul>

    <h2>Prerequisites</h2>
    <ul>
        <li><strong>Python</strong>: Version 3.12 or higher.</li>
        <li><strong>API Keys</strong>: At least one API key for a supported provider (e.g., Google, xAI). These should be set in a <code>.env</code> file.</li>
        <li><strong>System Dependencies</strong>:
            <ul>
                <li>On Ubuntu/Debian: <code>sudo apt-get install libopencv-dev</code>.</li>
                <li>On macOS: <code>brew install opencv</code>.</li>
            </ul>
        </li>
    </ul>

    <h2>Installation</h2>
    <ol>
        <li><strong>Clone the Repository</strong>:
            <pre><code class="language-bash">git clone &lt;repository-url&gt;
cd &lt;repository-directory&gt;</code></pre>
        </li>
        <li><strong>Create a Virtual Environment</strong>:
            <pre><code class="language-bash">python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate</code></pre>
        </li>
        <li><strong>Install Dependencies</strong>:
            <pre><code class="language-bash">pip install -r requirements.txt</code></pre>
            <p>Ensure <code>requirements.txt</code> includes:</p>
            <pre><code>pandas
opencv-python
python-dotenv
litellm</code></pre>
        </li>
        <li><strong>Set Up Environment Variables</strong>:
            <p>Create a <code>.env</code> file in the project root and add your API key(s):</p>
            <pre><code class="language-bash">echo "GOOGLE_API_KEY=your-google-api-key" &gt; .env
echo "XAI_API_KEY=your-xai-api-key" &gt;&gt; .env</code></pre>
        </li>
        <li><strong>Prepare Directory Structure</strong>:
            <ul>
                <li>Place stamp images in a directory (e.g., <code>stamps/</code>), organized into subdirectories for each album (e.g., <code>stamps/Isle of Man/</code>).</li>
                <li>The <code>output</code> directory will be created automatically to store all generated files.</li>
            </ul>
        </li>
    </ol>

    <h2>Usage</h2>
    <p>The primary script for all processing is <code>philately/processor_v2.py</code>. You can run the entire pipeline or specific phases using command-line flags.</p>

    <h3>Command-Line Flags</h3>
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
                <td>Confidence score (1-7) below which to trigger re-analysis with a high-cost model.</td>
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
                <td>Enable debug-level logging for verbose output, including API payloads.</td>
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
                <td>Run a re-examination of high-value stamps to find false positives.</td>
            </tr>
            <tr>
                <td><code>--false-positive-check-limit</code></td>
                <td><code>5</code></td>
                <td>Limit the number of stamps to check in the false-positive phase (0 for all).</td>
            </tr>
            <tr>
                <td><code>--run-substack-export</code></td>
                <td><code>False</code></td>
                <td>Generate a CSV export formatted for Substack posts.</td>
            </tr>
            <tr>
                <td><code>--substack-items</code></td>
                <td><code>10</code></td>
                <td>Number of top items to include in the Substack export (0 for all).</td>
            </tr>
        </tbody>
    </table>

    <h3>Example Commands</h3>
    <p><strong>1. Run the full pipeline on all images:</strong><br>(This is the default behavior if no phase flags are specified)</p>
    <pre><code class="language-bash">python philately/processor_v2.py --image-dir ./stamps --output-dir ./output</code></pre>
    <p><strong>2. Run only the image analysis phase on the first 10 images:</strong></p>
    <pre><code class="language-bash">python philately/processor_v2.py --run-analysis --max-images 10</code></pre>
    <p><strong>3. Run the false-positive check on the top 3 most valuable stamps with debug logging:</strong></p>
    <pre><code class="language-bash">python philately/processor_v2.py --run-false-positive-check --false-positive-check-limit 3 --debug</code></pre>
    <p><strong>4. Generate a Substack export with the top 20 most valuable items:</strong></p>
    <pre><code class="language-bash">python philately/processor_v2.py --run-substack-export --substack-items 20</code></pre>
    <p><strong>5. Re-run only the enrichment and summary phases:</strong></p>
    <pre><code class="language-bash">python philately/processor_v2.py --run-enrichment --run-summaries</code></pre>

    <h2>Output Files</h2>
    <p>All outputs are saved to the directory specified by <code>--output-dir</code>.</p>
    <ul>
        <li><code>master_inventory.csv</code>: The master database of all stamps, including detailed analysis and verification data.</li>
        <li><code>stamp_inventory.json</code>: A structured JSON file containing all data, including collection-wide statistics and narrative summaries.</li>
        <li><code>false_positive_check_report.csv</code>: A summary of high-value items that were checked for authenticity.</li>
        <li><code>high_value_summary.csv</code>: A CSV listing all stamps identified as high-value.</li>
        <li><code>substack_export.csv</code>: A CSV formatted for easy import into content platforms like Substack.</li>
        <li><code>cropped_entities/</code>: Directory of cropped images for each identified stamp.</li>
        <li><code>thumbnails/</code>: Directory of 100x100px thumbnails for each stamp.</li>
        <li><code>high_value_reports/</code>: Individual Markdown reports for each high-value stamp.</li>
    </ul>

    <h2>Example Data Records</h2>
    <h3>1. Master Inventory Record (<code>master_inventory.csv</code>)</h3>
    <p>A single row contains the complete data for one stamp.</p>
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

    <h3>2. Cluster Summary (<code>stamp_inventory.json</code>)</h3>
    <p>Summaries provide statistics and a narrative for a specific group of stamps (e.g., an album).</p>
    <pre><code class="language-json">{
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
}</code></pre>

    <h3>3. False Positive Check Report (<code>false_positive_check_report.csv</code>)</h3>
    <p>This report provides a clear audit trail for the verification process.</p>
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

</body>
</html>