#!/usr/bin/env python3
"""
Social Xtuff - Main Entry Point

Launch the Social Xtuff intelligent social media platform.
"""

import sys
from pathlib import Path

def main():
    """Main entry point for the social server."""
    import streamlit.web.cli as stcli

    # Get the package root directory
    package_root = Path(__file__).parent.parent.parent

    # Default to social feed page
    page_file = str(package_root / "src" / "social_server" / "pages" / "22_AI_Social_Feed.py")

    if len(sys.argv) > 1:
        if sys.argv[1] == "profile":
            page_file = str(package_root / "src" / "social_server" / "pages" / "23_Profile_Home.py")
        elif sys.argv[1] == "login":
            page_file = str(package_root / "src" / "social_server" / "pages" / "24_Login_Register.py")

    sys.argv = [
        "streamlit",
        "run",
        page_file,
        "--server.port=8503",
        "--server.address=localhost"
    ]

    stcli.main()

if __name__ == "__main__":
    main()