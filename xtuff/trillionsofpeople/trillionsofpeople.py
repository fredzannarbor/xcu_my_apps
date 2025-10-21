#!/usr/bin/env python3
"""
TrillionsOfPeople.info - Dynamic Web Application Entry Point
One row for every person who ever lived, might have lived, or may live someday.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add xcu_my_apps to path for shared imports
sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Import shared auth for SSO
from shared.auth import get_shared_auth, is_authenticated

# Import and run the modern web application
from src.trillions_of_people.web.app import TrillionsWebApp

def main():
    """Main entry point for the web application."""
    app = TrillionsWebApp()
    app.run()

if __name__ == "__main__":
    main()
