#!/usr/bin/env python3
"""
Background task runner for Maya Reader Panels with 15-minute progress reports.
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import signal
import os

# Global flag for graceful shutdown
shutdown_flag = False

def signal_handler(signum, frame):
    global shutdown_flag
    print("\nReceived shutdown signal. Completing current review...")
    shutdown_flag = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def count_completed_reviews(output_dir: Path) -> dict:
    """Count completed reviews from saved JSON files."""
    counts = {
        'children_9_10': 0,
        'parents': 0,
        'reading_experts': 0,
        'purchasing': 0
    }

    if not output_dir.exists():
        return counts

    for panel_name in counts.keys():
        # Find most recent file for this panel
        pattern = f"{panel_name}_feedback_*.json"
        files = list(output_dir.glob(pattern))

        if files:
            # Get the most recent file
            latest_file = max(files, key=lambda p: p.stat().st_mtime)

            try:
                with open(latest_file) as f:
                    data = json.load(f)
                    counts[panel_name] = data.get('total_reviews', 0)
            except:
                pass

    return counts


def print_progress_report(output_dir: Path, target_counts: dict, start_time: float):
    """Print a formatted progress report."""
    completed = count_completed_reviews(output_dir)
    total_completed = sum(completed.values())
    total_target = sum(target_counts.values())

    elapsed_minutes = (time.time() - start_time) / 60
    rate = total_completed / elapsed_minutes if elapsed_minutes > 0 else 0
    remaining = total_target - total_completed
    eta_minutes = remaining / rate if rate > 0 else 0

    print("\n" + "="*80)
    print(f"PROGRESS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print(f"Elapsed Time: {elapsed_minutes:.1f} minutes")
    print(f"Overall Progress: {total_completed}/{total_target} ({100*total_completed/total_target:.1f}%)")
    print(f"Rate: {rate:.1f} reviews/minute")
    print(f"ETA: {eta_minutes:.1f} minutes ({eta_minutes/60:.1f} hours)")
    print()
    print("Panel Status:")
    print("-" * 80)

    for panel_name, target in target_counts.items():
        current = completed[panel_name]
        pct = 100 * current / target if target > 0 else 0
        status = "✓" if current >= target else "⋯"
        print(f"  {status} {panel_name:20s}: {current:3d}/{target:3d} ({pct:5.1f}%)")

    print("="*80 + "\n")


def run_panels_with_progress():
    """Run panels in background with periodic progress updates."""

    # Configuration
    output_dir = Path('data/reader_panels/maya_story_reel')
    target_counts = {
        'children_9_10': 100,
        'parents': 80,
        'reading_experts': 50,
        'purchasing': 40
    }

    # Start time
    start_time = time.time()

    # Print initial report
    print("\n" + "="*80)
    print("LAUNCHING MAYA'S STORY REEL READER PANELS")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Target Reviews: {sum(target_counts.values())}")
    print(f"Model: ollama/deepseek-r1")
    print(f"Progress reports every 15 minutes")
    print("="*80 + "\n")

    # Launch the main script as a subprocess
    script_path = Path(__file__).parent / 'run_maya_reader_panels.py'

    process = subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    last_report_time = start_time
    report_interval = 15 * 60  # 15 minutes in seconds

    try:
        # Monitor process and print progress
        while process.poll() is None:
            # Read output line by line
            line = process.stdout.readline()
            if line:
                print(line, end='')

            # Check if it's time for a progress report
            current_time = time.time()
            if current_time - last_report_time >= report_interval:
                print_progress_report(output_dir, target_counts, start_time)
                last_report_time = current_time

            # Check shutdown flag
            if shutdown_flag:
                print("\nShutdown requested. Terminating subprocess...")
                process.terminate()
                process.wait(timeout=30)
                break

            time.sleep(0.1)  # Brief sleep to prevent busy waiting

        # Print final output
        remaining_output = process.stdout.read()
        if remaining_output:
            print(remaining_output)

        # Final progress report
        print("\n" + "="*80)
        print("FINAL PROGRESS REPORT")
        print("="*80)
        print_progress_report(output_dir, target_counts, start_time)

        # Summary
        completed = count_completed_reviews(output_dir)
        total_completed = sum(completed.values())
        total_target = sum(target_counts.values())

        if total_completed >= total_target:
            print("✓ ALL PANELS COMPLETED SUCCESSFULLY!")
        else:
            print(f"⚠ Partially completed: {total_completed}/{total_target} reviews")

        return_code = process.returncode if process.returncode is not None else 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Terminating subprocess...")
        process.terminate()
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
        return_code = 1

    except Exception as e:
        print(f"\nError running panels: {e}")
        process.terminate()
        return_code = 1

    finally:
        # Ensure process is cleaned up
        if process.poll() is None:
            process.kill()

    return return_code


if __name__ == "__main__":
    sys.exit(run_panels_with_progress())
