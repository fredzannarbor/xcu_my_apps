#!/usr/bin/env python3
"""
API Server Launcher for Social Xtuff Text-to-Post API
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports and shared modules
sys.path.insert(0, '/Users/fred/xcu_my_apps')
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import shared auth for SSO (for future API authentication)
from shared.auth import get_shared_auth, is_authenticated

def main():
    """Launch the FastAPI server."""
    import uvicorn

    print("🚀 Starting Social Xtuff Text-to-Post API...")
    print("📡 API will be available at: http://localhost:59312")
    print("📖 API docs will be available at: http://localhost:59312/docs")

    uvicorn.run(
        "social_server.api.text_to_post_api:app",
        host="0.0.0.0",
        port=59312,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()