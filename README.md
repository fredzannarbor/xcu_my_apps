# CIA PDF Finder Agent

An intelligent agent that scans directories for PDF documents originating from the Central Intelligence Agency (CIA).

## Features

- **Recursive PDF scanning** - Finds all PDFs in a directory and subdirectories
- **Intelligent CIA detection** - Uses multiple confidence-weighted indicators including:
  - Official CIA letterhead markers
  - FOIA release stamps and document numbers
  - CIA-specific terminology and locations
  - Classification markings
- **Progress tracking** - Visual progress bar during scanning
- **Detailed reporting** - Shows confidence scores, file metadata, and matching indicators
- **Configurable thresholds** - Adjust minimum confidence score to tune sensitivity

## Installation

1. Ensure Python 3.12.6+ is installed
2. Install required dependencies:

```bash
pip install PyMuPDF tqdm
```

## Usage

### Basic usage (scans ~/Downloads by default):

```bash
python cia_pdf_finder.py
```

### Scan a specific directory:

```bash
python cia_pdf_finder.py --directory /path/to/documents
```

### Adjust confidence threshold:

```bash
python cia_pdf_finder.py --min-confidence 50
```

### Full example:

```bash
python cia_pdf_finder.py -d ~/Documents/research -c 40
```

## How It Works

The agent uses a three-tier confidence scoring system:

1. **High Confidence Indicators (40 points each)**:
   - "Central Intelligence Agency" text
   - CIA headquarters/Langley references
   - FOIA release stamps mentioning CIA
   - CIA document reference numbers (e.g., CIA-RDP...)

2. **Medium Confidence Indicators (15 points each)**:
   - "CIA" acronym usage
   - Langley, Virginia mentions
   - Director of Central Intelligence references
   - Classification markings with CIA

3. **Low Confidence Indicators (5 points each)**:
   - Intelligence community terminology
   - FOIA request mentions
   - Covert operations language

Documents are scored based on which indicators are found (max 100%), and only those meeting the minimum confidence threshold are reported.

## Output

The agent generates a detailed report showing:
- Total number of potential CIA documents found
- For each document:
  - File name and full path
  - Confidence score (0-100%)
  - Page count
  - File size
  - Matching indicators that triggered detection

## Performance Notes

- Only the first 10 pages of each PDF are analyzed for efficiency
- Large directories may take several minutes to process
- Progress bar provides real-time feedback during scanning

## License

Part of the Codexes Factory project.
