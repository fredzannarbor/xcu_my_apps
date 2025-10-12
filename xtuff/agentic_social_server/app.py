#!/usr/bin/env python3
"""
AI Social Server - Main Entry Point

Launch the AI Social Feed application.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def main():
    """Main entry point for the social server."""
    import streamlit.web.cli as stcli

    # Default to main app (which shows social feed)
    page_file = "main_app.py"

    if len(sys.argv) > 1:
        if sys.argv[1] == "profile":
            page_file = "pages/23_Profile_Home.py"
        elif sys.argv[1] == "login":
            page_file = "pages/24_Login_Register.py"

    sys.argv = [
        "streamlit",
        "run",
        page_file,
        "--server.port=8501",
        "--server.address=localhost"
    ]

    stcli.main()

if __name__ == "__main__":
    main()