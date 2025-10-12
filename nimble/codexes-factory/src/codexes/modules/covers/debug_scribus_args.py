import sys
import os

# This script's only job is to report what arguments it received.
# We will write to a file to be absolutely sure we capture the output.
debug_file_path = "/tmp/scribus_debug_output.txt"

try:
    with open(debug_file_path, "w") as f:
        f.write("--- Scribus Debug Script Activated ---\n")
        f.write(f"Python Executable: {sys.executable}\n")
        f.write(f"Current Working Directory: {os.getcwd()}\n")
        f.write(f"Received sys.argv: {sys.argv}\n")
        f.write(f"Number of arguments: {len(sys.argv)}\n")

    # Also print to stdout, which should appear in your main log
    print("--- Scribus Debug Script STDOUT ---")
    with open(debug_file_path, "r") as f:
        print(f.read())
    print("--- End Scribus Debug Script STDOUT ---")

except Exception as e:
    print(f"Error in debug script: {e}")

# Exit cleanly
sys.exit(0)
