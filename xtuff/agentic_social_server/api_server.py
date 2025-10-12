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

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def main():
    """Launch the FastAPI server."""
    import uvicorn

    print("🚀 Starting Social Xtuff Text-to-Post API...")
    print("📡 API will be available at: http://localhost:59312")
    print("📖 API docs will be available at: http://localhost:59312/docs")

    uvicorn.run(
        "social_server.api.text_to_post_api:app",
        host="127.0.0.1",
        port=59312,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()