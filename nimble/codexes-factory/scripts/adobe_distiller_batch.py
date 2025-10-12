#!/usr/bin/env python3
"""
Batch process PostScript files to PDF/X-1a using Adobe Distiller via subprocess.

This script processes PostScript files in small batches to prevent Adobe Distiller
from running out of memory. It automatically detects the Adobe Distiller executable
and processes files in configurable batch sizes.

Prerequisites:
- Adobe Acrobat Pro with Distiller must be installed
- PostScript files to convert
- Appropriate PDF/X-1a settings file (optional)

Usage:
  python scripts/adobe_distiller_batch.py /path/to/postscript_files /path/to/output_pdfs
  python scripts/adobe_distiller_batch.py /path/to/postscript_files /path/to/output_pdfs --batch-size 5
  python scripts/adobe_distiller_batch.py /path/to/postscript_files /path/to/output_pdfs --settings-file /path/to/pdfx1a.joboptions
"""

import argparse
import logging
import subprocess
import time
from pathlib import Path
from typing import List, Optional
import sys
import platform
import psutil
import os
import signal
import gc
import weakref

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


def find_adobe_distiller() -> Optional[str]:
    """
    Attempts to find the Adobe Distiller executable.
    Returns the path to the executable or None if not found.
    """
    system = platform.system().lower()

    if system == "windows":
        # Common Windows paths for Adobe Distiller
        possible_paths = [
            "C:/Program Files/Adobe/Acrobat DC/Acrobat/acrodist.exe",
            "C:/Program Files (x86)/Adobe/Acrobat DC/Acrobat/acrodist.exe",
            "C:/Program Files/Adobe/Acrobat 2020/Acrobat/acrodist.exe",
            "C:/Program Files (x86)/Adobe/Acrobat 2020/Acrobat/acrodist.exe",
            "C:/Program Files/Adobe/Acrobat 2017/Acrobat/acrodist.exe",
            "C:/Program Files (x86)/Adobe/Acrobat 2017/Acrobat/acrodist.exe",
        ]
    elif system == "darwin":  # macOS
        # Common macOS paths for Adobe Distiller
        possible_paths = [
            "/Applications/Adobe Acrobat DC/Acrobat Distiller.app/Contents/MacOS/Distiller",
            "/Applications/Adobe Acrobat 2020/Acrobat Distiller.app/Contents/MacOS/Distiller",
            "/Applications/Adobe Acrobat 2017/Acrobat Distiller.app/Contents/MacOS/Distiller",
        ]
    else:
        logging.warning(f"Unsupported operating system: {system}")
        return None

    for path in possible_paths:
        if Path(path).exists():
            logging.info(f"Found Adobe Distiller at: {path}")
            return path

    logging.error("Adobe Distiller executable not found in common locations")
    return None


def get_memory_usage() -> float:
    """
    Get current system memory usage as a percentage.
    """
    return psutil.virtual_memory().percent


def kill_distiller_processes():
    """
    Kill any running Adobe Distiller processes.
    """
    killed_count = 0

    # Use more memory-efficient process scanning
    try:
        # Get list of PIDs first, then check each one individually to avoid loading all process info
        pids = psutil.pids()
        for pid in pids:
            try:
                proc = psutil.Process(pid)
                name = proc.name().lower()
                if 'distiller' in name:
                    logging.info(f"Killing Distiller process: {pid}")
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                        killed_count += 1
                    except psutil.TimeoutExpired:
                        proc.kill()
                        killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logging.warning(f"Error during process cleanup: {e}")

    # Force garbage collection
    gc.collect()

    if killed_count > 0:
        logging.info(f"Killed {killed_count} Distiller process(es)")
        time.sleep(3)  # Wait for cleanup

    return killed_count


def process_single_file(distiller_path: str, ps_file: Path, output_dir: Path,
                       settings_file: Optional[Path] = None, memory_threshold: float = 85.0) -> bool:
    """
    Process a single PostScript file with memory monitoring.
    Returns True if successful, False otherwise.
    """
    output_pdf = output_dir / f"{ps_file.stem}.pdf"
    logging.info(f"Processing: {ps_file.name} -> {output_pdf.name}")

    # Check memory before starting
    initial_memory = get_memory_usage()
    logging.info(f"Memory usage before processing: {initial_memory:.1f}%")

    if initial_memory > memory_threshold:
        logging.warning(f"Memory usage ({initial_memory:.1f}%) exceeds threshold ({memory_threshold}%), restarting Distiller")
        kill_distiller_processes()

    # Build the Adobe Distiller command
    cmd = [distiller_path]

    # Add settings file if provided
    if settings_file and settings_file.exists():
        cmd.extend(["-jobOptions", str(settings_file)])

    # Add input and output files
    cmd.extend([str(ps_file), str(output_pdf)])

    distiller_process = None
    try:
        # Start Adobe Distiller process with limited buffering
        distiller_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,  # Don't buffer stdout
            stderr=subprocess.DEVNULL,  # Don't buffer stderr
            text=True
        )

        # Monitor memory usage during processing
        start_time = time.time()
        timeout = 900  # 15 minutes

        while distiller_process.poll() is None:
            current_memory = get_memory_usage()

            # Check if memory threshold exceeded
            if current_memory > memory_threshold:
                logging.warning(f"Memory usage ({current_memory:.1f}%) exceeded threshold during processing")
                logging.info("Terminating Distiller process due to high memory usage")
                distiller_process.terminate()
                try:
                    distiller_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    distiller_process.kill()
                kill_distiller_processes()  # Clean up any other Distiller processes
                return False

            # Check for timeout
            if time.time() - start_time > timeout:
                logging.error(f"❌ Timeout processing: {ps_file.name}")
                distiller_process.terminate()
                try:
                    distiller_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    distiller_process.kill()
                kill_distiller_processes()
                return False

            time.sleep(1)  # Check every 1 second - reduced from 2 but still prevents busy waiting

            # Force garbage collection every 10 iterations to prevent accumulation
            if int(time.time() - start_time) % 20 == 0:  # Every 20 seconds
                gc.collect()

        # Process completed, check result
        return_code = distiller_process.returncode

        # Ensure process is fully terminated before proceeding
        try:
            distiller_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logging.warning(f"Process didn't terminate cleanly for {ps_file.name}")

        if return_code == 0 and output_pdf.exists():
            final_memory = get_memory_usage()
            logging.info(f"✅ Successfully converted: {ps_file.name} (Memory: {final_memory:.1f}%)")
            return True
        else:
            # Don't call communicate() since we're using DEVNULL
            logging.error(f"❌ Failed to process: {ps_file.name} (return code: {return_code})")
            return False

    except Exception as e:
        logging.error(f"❌ Unexpected error processing {ps_file.name}: {e}")
        if distiller_process and distiller_process.poll() is None:
            distiller_process.terminate()
            try:
                distiller_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                distiller_process.kill()
        return False
    finally:
        # Ensure process handle is cleaned up
        if distiller_process:
            try:
                distiller_process.stdout = None
                distiller_process.stderr = None
            except:
                pass
        # Force garbage collection after each file
        gc.collect()


def process_postscript_files(input_dir: Path, output_dir: Path,
                           memory_threshold: float = 85.0,
                           settings_file: Optional[Path] = None,
                           delay_between_files: int = 5):
    """
    Process PostScript files in batches to prevent memory issues.
    """
    # Check initial memory usage - abort if already high
    initial_memory = get_memory_usage()
    if initial_memory > 70.0:
        logging.error(f"❌ Initial memory usage too high: {initial_memory:.1f}%. Please restart to free memory.")
        return

    # Find Adobe Distiller
    distiller_path = find_adobe_distiller()
    if not distiller_path:
        logging.error("❌ Adobe Distiller not found. Please ensure Adobe Acrobat Pro is installed.")
        return

    # Validate input directory
    if not input_dir.is_dir():
        logging.error(f"❌ Input directory not found: {input_dir}")
        return

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find PostScript files - use iterators to avoid loading all paths into memory
    ps_files = []
    for pattern in ["*.ps", "*.eps"]:
        ps_files.extend(input_dir.glob(pattern))

    if not ps_files:
        logging.warning(f"⚠️ No PostScript files found in {input_dir}")
        return

    logging.info(f"Found {len(ps_files)} PostScript file(s) to convert")
    logging.info(f"Memory monitoring enabled with {memory_threshold}% threshold")
    logging.info(f"Processing files individually with {delay_between_files}s delay between files")

    # Validate settings file if provided
    if settings_file and not settings_file.exists():
        logging.warning(f"⚠️ Settings file not found: {settings_file}")
        settings_file = None

    total_success = 0
    total_failure = 0

    # Process files individually with memory monitoring
    for i, ps_file in enumerate(ps_files, 1):
        # Emergency memory check before each file
        current_memory = get_memory_usage()
        if current_memory > 90.0:
            logging.error(f"❌ EMERGENCY: Memory usage at {current_memory:.1f}% - aborting to prevent system crash")
            logging.error(f"Processed {total_success}/{i-1} files before emergency stop")
            kill_distiller_processes()  # Clean up any running processes
            return

        logging.info(f"--- Processing File {i}/{len(ps_files)}: {ps_file.name} ---")

        # Ensure no other Distiller processes are running before starting this file
        if i > 1:  # Skip for first file
            existing_processes = kill_distiller_processes()
            if existing_processes > 0:
                logging.info(f"Cleaned up {existing_processes} lingering Distiller process(es)")
                time.sleep(2)  # Brief pause after cleanup

        success = process_single_file(
            distiller_path, ps_file, output_dir, settings_file, memory_threshold
        )

        if success:
            total_success += 1
        else:
            total_failure += 1

        # Add delay between files to allow memory cleanup
        if i < len(ps_files):  # Don't delay after the last file
            logging.info(f"Waiting {delay_between_files} seconds before next file...")
            # Force garbage collection between files
            gc.collect()
            time.sleep(delay_between_files)
            # Additional garbage collection after delay
            gc.collect()

    # Final summary
    logging.info("--- Conversion Complete ---")
    logging.info(f"Total files processed: {len(ps_files)}")
    logging.info(f"Successfully converted: {total_success}")
    if total_failure > 0:
        logging.warning(f"Failed to convert: {total_failure}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch convert PostScript files to PDF using Adobe Distiller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/adobe_distiller_batch.py input_ps/ output_pdf/
  python scripts/adobe_distiller_batch.py input_ps/ output_pdf/ --memory-threshold 80.0
  python scripts/adobe_distiller_batch.py input_ps/ output_pdf/ --settings-file pdfx1a.joboptions
        """
    )

    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing PostScript files (.ps, .eps)"
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory where PDF files will be saved"
    )
    parser.add_argument(
        "--memory-threshold",
        type=float,
        default=85.0,
        help="Memory usage percentage threshold to restart Distiller (default: 85.0)"
    )
    parser.add_argument(
        "--settings-file",
        type=Path,
        help="Adobe Distiller job options file (.joboptions) for PDF/X-1a settings"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=5,
        help="Seconds to wait between files (default: 5)"
    )

    args = parser.parse_args()

    # Validate memory threshold
    if not 50.0 <= args.memory_threshold <= 95.0:
        logging.error("❌ Memory threshold must be between 50.0 and 95.0")
        sys.exit(1)

    process_postscript_files(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        memory_threshold=args.memory_threshold,
        settings_file=args.settings_file,
        delay_between_files=args.delay
    )


if __name__ == "__main__":
    main()