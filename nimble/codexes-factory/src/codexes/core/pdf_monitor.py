#!/usr/bin/env python3
"""
PDF Harvest Monitoring System

Provides automated monitoring of PDF harvest bundles with configurable intervals.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import paths handling
import sys
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from codexes.modules.crawlers import ZyteCrawler
except ModuleNotFoundError:
    from src.codexes.modules.crawlers import ZyteCrawler


class PDFHarvestMonitor:
    """Monitor PDF harvest bundles for new documents."""

    def __init__(self):
        self.config_dir = Path("configs")
        self.config_file = self.config_dir / "pdf_harvester_config.json"
        self.monitor_file = self.config_dir / "monitor_state.json"
        self.config_dir.mkdir(exist_ok=True)

        self.is_running = False
        self.monitor_thread = None
        self.last_check = None
        self.new_docs_found = 0

        # Ensure monitor state file exists
        if not self.monitor_file.exists():
            self._save_monitor_state({
                "last_check": None,
                "total_new_docs": 0,
                "last_bundle_results": {},
                "monitoring_enabled": False
            })

    def _load_pdf_config(self) -> Dict:
        """Load PDF harvester configuration."""
        if not self.config_file.exists():
            return {
                "bundles": {
                    "Intelligence Community": ["cia.gov", "nsa.gov", "odni.gov"],
                    "Law Enforcement": ["fbi.gov", "dhs.gov"],
                },
                "current_bundle": "Intelligence Community",
                "default_min_pages": 18,
                "default_max_docs": 50,  # Reduced for monitoring
                "default_time_filter": "y"
            }

        with open(self.config_file, 'r') as f:
            return json.load(f)

    def _save_monitor_state(self, state: Dict):
        """Save monitor state."""
        with open(self.monitor_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)

    def _load_monitor_state(self) -> Dict:
        """Load monitor state."""
        if not self.monitor_file.exists():
            return {
                "last_check": None,
                "total_new_docs": 0,
                "last_bundle_results": {},
                "monitoring_enabled": False
            }

        with open(self.monitor_file, 'r') as f:
            return json.load(f)

    def get_notification_status(self) -> Tuple[bool, int, Optional[str]]:
        """
        Get current notification status.

        Returns:
            Tuple of (has_new_docs, new_docs_count, last_check_time)
        """
        state = self._load_monitor_state()

        has_new_docs = state.get("total_new_docs", 0) > 0
        new_docs_count = state.get("total_new_docs", 0)
        last_check = state.get("last_check")

        return has_new_docs, new_docs_count, last_check

    def clear_notifications(self):
        """Clear new document notifications."""
        state = self._load_monitor_state()
        state["total_new_docs"] = 0
        self._save_monitor_state(state)

    def run_single_check(self, bundle_name: str = None) -> Dict:
        """
        Run a single monitoring check for the specified bundle.

        Args:
            bundle_name: Bundle to check (defaults to current_bundle)

        Returns:
            Dict with check results
        """
        api_key = os.getenv("ZYTE_API_KEY")
        if not api_key:
            return {"error": "ZYTE_API_KEY not configured"}

        config = self._load_pdf_config()
        state = self._load_monitor_state()

        if bundle_name is None:
            bundle_name = config.get("current_bundle", "Intelligence Community")

        bundles = config.get("bundles", {})
        if bundle_name not in bundles:
            return {"error": f"Bundle '{bundle_name}' not found"}

        bundle_sites = bundles[bundle_name]

        # Monitoring uses reduced parameters for efficiency
        min_pages = config.get("default_min_pages", 18)
        max_docs = min(config.get("default_max_docs", 50), 50)  # Cap at 50 for monitoring
        time_filter = config.get("default_time_filter", "y")

        results = {
            "bundle_name": bundle_name,
            "sites_checked": len(bundle_sites),
            "total_new_docs": 0,
            "site_results": {},
            "check_time": datetime.now().isoformat(),
            "errors": []
        }

        try:
            crawler = ZyteCrawler(api_key, timeout=60)

            for site in bundle_sites:
                site_result = {"new_docs": 0, "qualified_docs": 0, "errors": []}

                try:
                    # Quick search for new PDFs
                    google_url = f"https://www.google.com/search?q=site:{site}+filetype:pdf&num=10&tbs=qdr:{time_filter}&start=0"

                    import requests
                    import base64
                    headers = {
                        'Authorization': f'Basic {base64.b64encode(f"{api_key}:".encode()).decode()}',
                        'Content-Type': 'application/json'
                    }

                    data = {
                        'url': google_url,
                        'browserHtml': True,
                        'javascript': True
                    }

                    response = requests.post('https://api.zyte.com/v1/extract', headers=headers, json=data, timeout=60)
                    response.raise_for_status()

                    html = response.json().get('browserHtml', '')

                    # Extract PDF URLs
                    import re
                    pdf_pattern = rf'https?://[^\s"]*{re.escape(site)}[^\s"]*\.pdf'
                    found_urls = re.findall(pdf_pattern, html, re.IGNORECASE)

                    pdf_urls = []
                    for url in found_urls:
                        clean_url = (url.replace('%20', ' ')
                                       .replace('%5B', '[')
                                       .replace('%5D', ']')
                                       .replace('%2C', ',')
                                       .replace('%252C', ',')
                                       .replace('%2520', ' '))
                        if clean_url not in pdf_urls and clean_url.endswith('.pdf'):
                            pdf_urls.append(clean_url)

                    # Limit to max_docs for monitoring efficiency
                    pdf_urls = pdf_urls[:max_docs]

                    # Quick check against memory to find new documents
                    memory_file = self.config_dir.parent / "configs" / "pdf_harvester_memory.json"
                    if memory_file.exists():
                        with open(memory_file, 'r') as f:
                            memory = json.load(f)
                        downloaded_urls = memory.get("downloaded_urls", {}).get(site, [])
                        new_urls = [url for url in pdf_urls if url not in downloaded_urls]
                    else:
                        new_urls = pdf_urls

                    # Count qualified documents (>= min_pages) from new URLs
                    qualified_count = 0
                    for url in new_urls[:10]:  # Check first 10 for efficiency
                        try:
                            page_count = crawler.get_pdf_page_count(url)
                            if page_count >= min_pages:
                                qualified_count += 1
                        except Exception as e:
                            site_result["errors"].append(f"Error checking {url}: {str(e)}")

                        # Add delay for rate limiting
                        time.sleep(1)

                    site_result["new_docs"] = len(new_urls)
                    site_result["qualified_docs"] = qualified_count
                    results["total_new_docs"] += qualified_count

                except Exception as e:
                    site_result["errors"].append(f"Error processing {site}: {str(e)}")
                    results["errors"].append(f"{site}: {str(e)}")

                results["site_results"][site] = site_result

        except Exception as e:
            results["errors"].append(f"General error: {str(e)}")

        # Update monitor state
        state["last_check"] = results["check_time"]
        state["total_new_docs"] += results["total_new_docs"]
        state["last_bundle_results"] = results
        self._save_monitor_state(state)

        return results

    def start_monitoring(self, interval_hours: int = 6):
        """
        Start automated monitoring.

        Args:
            interval_hours: Hours between checks
        """
        if self.is_running:
            return

        self.is_running = True

        state = self._load_monitor_state()
        state["monitoring_enabled"] = True
        self._save_monitor_state(state)

        def monitor_loop():
            while self.is_running:
                try:
                    self.run_single_check()
                    # Sleep for interval
                    time.sleep(interval_hours * 3600)
                except Exception as e:
                    # Log error but continue monitoring
                    state = self._load_monitor_state()
                    state.setdefault("monitor_errors", []).append({
                        "time": datetime.now().isoformat(),
                        "error": str(e)
                    })
                    self._save_monitor_state(state)
                    time.sleep(300)  # Wait 5 minutes before retry

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop automated monitoring."""
        self.is_running = False

        state = self._load_monitor_state()
        state["monitoring_enabled"] = False
        self._save_monitor_state(state)

    def is_monitoring_enabled(self) -> bool:
        """Check if monitoring is currently enabled."""
        state = self._load_monitor_state()
        return state.get("monitoring_enabled", False) and self.is_running


# Global monitor instance
_monitor_instance = None

def get_monitor() -> PDFHarvestMonitor:
    """Get global monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PDFHarvestMonitor()
    return _monitor_instance