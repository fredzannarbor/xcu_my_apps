# /Users/fred/xcu_my_apps/nimble/codexes-factory/scripts/convert_to_pdfx1a.py
# version 1.9
"""
Converts a directory of PDF files to the PDF/X-1a:2001 standard for professional
printing.

This script uses Ghostscript to perform the conversion. It iterates through all
PDF files in a specified input directory, converts them, and saves the results
in an output directory.

Prerequisites:
- Ghostscript must be installed and accessible in the system's PATH.
  (e.g., via `brew install ghostscript` on macOS or `sudo apt-get install ghostscript`
  on Debian/Ubuntu).

Usage:
  python scripts/convert_to_pdfx1a.py /path/to/input_pdfs /path/to/output_pdfs
"""

import argparse
import logging
import shutil
import subprocess
from pathlib import Path

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


def find_ghostscript() -> str:
    """Finds the Ghostscript executable in the system's PATH."""
    gs_executable = shutil.which('gs') or shutil.which('gswin64c') or shutil.which('gswin32c')
    if not gs_executable:
        raise FileNotFoundError(
            "Ghostscript executable not found. Please ensure Ghostscript is installed and in your system's PATH."
        )
    return gs_executable


def find_pdfx_def_file() -> Path:
    """
    Attempts to find the PDFX_def.ps file required by Ghostscript.
    Searches in common installation locations.
    """
    common_paths = [
        "/usr/share/ghostscript/",
        "/usr/local/share/ghostscript/",
        "/opt/homebrew/share/ghostscript/",
        "C:/Program Files/gs/"
    ]

    for p in common_paths:
        base_path = Path(p)
        if base_path.is_dir():
            # Ghostscript often has versioned subdirectories
            for version_dir in base_path.iterdir():
                if version_dir.is_dir():
                    def_file = version_dir / "lib" / "PDFX_def.ps"
                    if def_file.exists():
                        logging.info(f"Found PDFX_def.ps at: {def_file}")
                        return def_file

    raise FileNotFoundError(
        "Could not automatically find 'PDFX_def.ps'. Please locate it in your Ghostscript installation directory."
    )


def convert_pdfs_to_pdfx1a(input_dir: Path, output_dir: Path):
    """
    Converts all PDF files in the input directory to PDF/X-1a format.
    """
    try:
        gs_path = find_ghostscript()
        pdfx_def_path = find_pdfx_def_file()
    except FileNotFoundError as e:
        logging.error(f"❌ Prerequisite not found: {e}")
        return

    if not input_dir.is_dir():
        logging.error(f"❌ Input directory not found: {input_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = list(input_dir.glob("*.pdf"))

    if not pdf_files:
        logging.warning(f"⚠️ No PDF files found in {input_dir}")
        return

    logging.info(f"Found {len(pdf_files)} PDF(s) to convert in {input_dir}.")
    success_count = 0
    fail_count = 0

    for pdf_path in pdf_files:
        output_pdf_path = output_dir / f"{pdf_path.stem}_pdfx1a.pdf"
        logging.info(f"Processing '{pdf_path.name}' -> '{output_pdf_path.name}'...")

        gs_command = [
            gs_path,
            '-dNOSAFER',                        # Disable sandbox for file access
            '-dBATCH',                          # Exit after processing
            '-dNOPAUSE',                        # No user interaction
            '-sDEVICE=pdfwrite',                # Use the PDF writer device
            '-dPDFX',                           # Enable PDF/X-1a mode
            '-dCompatibilityLevel=1.3',         # PDF/X-1a is based on PDF 1.3; flattens transparency
            '-sColorConversionStrategy=CMYK',   # Convert all colors to CMYK
            # Define a new, valid OutputIntent to override the broken one from the source PDF
            '-sOutputConditionIdentifier="Custom"',
            '-sOutputCondition="Default CMYK Profile"',
            '-sOutputICCProfile=default_cmyk.icc', # Use a standard, built-in ICC profile
            f'-sOutputFile={output_pdf_path}',
            str(pdfx_def_path),
            str(pdf_path)
        ]

        try:
            result = subprocess.run(gs_command, check=True, capture_output=True, text=True)
            logging.info(f"✅ Successfully converted {pdf_path.name}")
            success_count += 1
        except subprocess.CalledProcessError as e:
            logging.error(f"❌ Failed to convert {pdf_path.name}.")
            if e.stdout:
                logging.error(f"   Ghostscript stdout:\n{e.stdout.strip()}")
            if e.stderr:
                logging.error(f"   Ghostscript stderr:\n{e.stderr.strip()}")
            fail_count += 1

    logging.info("--- Conversion Complete ---")
    logging.info(f"Successfully converted: {success_count} file(s)")
    if fail_count > 0:
        logging.warning(f"Failed to convert: {fail_count} file(s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a directory of PDFs to PDF/X-1a format.")
    parser.add_argument("input_dir", type=Path, help="Directory containing the source PDF files.")
    parser.add_argument("output_dir", type=Path, help="Directory where the converted PDF/X-1a files will be saved.")
    args = parser.parse_args()

    convert_pdfs_to_pdfx1a(args.input_dir, args.output_dir)