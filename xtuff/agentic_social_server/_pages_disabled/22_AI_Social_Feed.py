#!/usr/bin/env python3
"""
AI Social Feed Page - Redirects to main social server
"""

import sys
from pathlib import Path

# Add project root and src to path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st

# Import and run the main Social Xtuff
import importlib.util
feed_spec = importlib.util.spec_from_file_location("social_xtuff", str(Path(__file__).parent.parent / "src/social_server/Social_Xtuff.py"))
feed_module = importlib.util.module_from_spec(feed_spec)
feed_spec.loader.exec_module(feed_module)

# Run the main feed function
if __name__ == "__main__":
    feed_module.main()