#!/usr/bin/env python3
"""
PDF Harvester Streamlit Page

Admin-only page for harvesting PDFs using Google search pagination.
Supports any Google search string in format: site:foo.com filetype:pdf {searchterm}
"""

import streamlit as st
import json
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# For imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from codexes.modules.crawlers import ZyteCrawler
from codexes.core.auth import get_user_role


class PDFHarvesterPage:
    """Streamlit page for PDF harvesting with memory and history."""

    def __init__(self):
        self.config_file = Path("configs/pdf_harvester_config.json")
        self.memory_file = Path("configs/pdf_harvester_memory.json")
        self.ensure_config_files()

    def ensure_config_files(self):
        """Ensure config files exist."""
        self.config_file.parent.mkdir(exist_ok=True)

        if not self.config_file.exists():
            default_config = {
                "search_history": [],
                "default_min_pages": 18,
                "default_max_docs": 300,
                "default_time_filter": "y",
                "bundles": {
                    "Intelligence Community": ["cia.gov", "nsa.gov", "odni.gov"],
                    "Law Enforcement": ["fbi.gov", "dhs.gov"],
                    "Defense": ["defense.gov", "army.mil", "navy.mil", "af.mil"],
                    "Individual Sites": ["cia.gov"]
                },
                "current_bundle": "Intelligence Community",
                "bundle_results": {},  # {bundle_name: {timestamp, new_docs_count}}
                "last_bundle_check": None
            }
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)

        if not self.memory_file.exists():
            default_memory = {
                "downloaded_urls": {},  # {site: [urls]}
                "last_updated": None
            }
            with open(self.memory_file, 'w') as f:
                json.dump(default_memory, f, indent=2)

    def load_config(self) -> Dict:
        """Load configuration."""
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def save_config(self, config: Dict):
        """Save configuration."""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def load_memory(self) -> Dict:
        """Load download memory."""
        with open(self.memory_file, 'r') as f:
            return json.load(f)

    def save_memory(self, memory: Dict):
        """Save download memory."""
        memory["last_updated"] = datetime.now().isoformat()
        with open(self.memory_file, 'w') as f:
            json.dump(memory, f, indent=2)

    def parse_google_search(self, search_string: str) -> Dict:
        """Parse Google search string and extract components."""
        search_string = search_string.strip()

        # Extract site
        site_match = re.search(r'site:([^\s]+)', search_string)
        site = site_match.group(1) if site_match else ""

        # Extract filetype
        filetype_match = re.search(r'filetype:([^\s]+)', search_string)
        filetype = filetype_match.group(1) if filetype_match else "pdf"

        # Extract additional search terms
        search_terms = search_string
        search_terms = re.sub(r'site:[^\s]+', '', search_terms)
        search_terms = re.sub(r'filetype:[^\s]+', '', search_terms)
        search_terms = search_terms.strip()

        return {
            "site": site,
            "filetype": filetype,
            "search_terms": search_terms,
            "full_query": search_string
        }

    def build_google_search_url(self, site: str, filetype: str, search_terms: str,
                               start: int = 0, num: int = 10, time_filter: str = "y") -> str:
        """Build Google search URL."""
        base_url = "https://www.google.com/search"

        query_parts = []
        if site:
            query_parts.append(f"site:{site}")
        if filetype:
            query_parts.append(f"filetype:{filetype}")
        if search_terms:
            query_parts.append(search_terms)

        query = " ".join(query_parts)
        url = f"{base_url}?q={query.replace(' ', '+')}&num={num}&tbs=qdr:{time_filter}&start={start}"

        return url

    def extract_pdf_urls_from_google_results(self, html: str, site: str) -> List[str]:
        """Extract PDF URLs from Google search results HTML."""
        pdf_urls = []

        # Pattern to find PDF URLs for the specific site
        pdf_pattern = rf'https?://[^\s"]*{re.escape(site)}[^\s"]*\.pdf'
        found_urls = re.findall(pdf_pattern, html, re.IGNORECASE)

        for url in found_urls:
            # Clean up URL encoding
            clean_url = (url.replace('%20', ' ')
                           .replace('%5B', '[')
                           .replace('%5D', ']')
                           .replace('%2C', ',')
                           .replace('%252C', ',')
                           .replace('%2520', ' '))

            if clean_url not in pdf_urls and clean_url.endswith('.pdf'):
                pdf_urls.append(clean_url)

        return pdf_urls

    def check_already_downloaded(self, pdf_urls: List[str], site: str) -> Dict:
        """Check which URLs have already been downloaded."""
        memory = self.load_memory()
        site_downloads = memory.get("downloaded_urls", {}).get(site, [])

        new_urls = []
        existing_urls = []

        for url in pdf_urls:
            if url in site_downloads:
                existing_urls.append(url)
            else:
                new_urls.append(url)

        return {
            "new_urls": new_urls,
            "existing_urls": existing_urls,
            "total_found": len(pdf_urls)
        }

    def mark_urls_as_downloaded(self, urls: List[str], site: str):
        """Mark URLs as downloaded in memory."""
        memory = self.load_memory()

        if "downloaded_urls" not in memory:
            memory["downloaded_urls"] = {}

        if site not in memory["downloaded_urls"]:
            memory["downloaded_urls"][site] = []

        for url in urls:
            if url not in memory["downloaded_urls"][site]:
                memory["downloaded_urls"][site].append(url)

        self.save_memory(memory)

    def render_page(self):
        """Render the PDF Harvester page."""
        st.title("🔍 PDF Harvester")
        st.markdown("*Admin-only tool for harvesting PDFs using Google search pagination*")

        # Check for API key
        api_key = os.getenv("ZYTE_API_KEY")
        if not api_key:
            st.error("❌ ZYTE_API_KEY environment variable not set!")
            st.info("Please set your Zyte API key in .env file")
            return

        # Get user role for admin features
        try:
            user_role = get_user_role()
        except:
            user_role = 'admin'  # Fallback for development

        # Load config
        config = self.load_config()
        memory = self.load_memory()

        # Sidebar with memory stats
        with st.sidebar:
            st.subheader("📊 Memory Stats")
            total_sites = len(memory.get("downloaded_urls", {}))
            total_downloads = sum(len(urls) for urls in memory.get("downloaded_urls", {}).values())
            saved_searches = len(config.get("search_history", []))

            st.metric("Sites Tracked", total_sites)
            st.metric("Total Downloads", total_downloads)
            st.metric("Saved Searches", saved_searches)

            if memory.get("last_updated"):
                last_updated = datetime.fromisoformat(memory["last_updated"])
                st.caption(f"Last updated: {last_updated.strftime('%Y-%m-%d %H:%M')}")

            # Memory management
            st.subheader("🗂️ Memory Management")
            if st.button("View Download History"):
                st.session_state.show_history = True

            # Clear saved searches
            saved_count = len(config.get("search_history", []))
            if saved_count > 0:
                if st.button(f"Clear All Saved Searches ({saved_count})"):
                    config["search_history"] = []
                    self.save_config(config)
                    st.success("All saved searches cleared!")
                    st.rerun()

            if st.button("Clear All Memory"):
                if st.button("⚠️ Confirm Clear", type="secondary"):
                    memory = {"downloaded_urls": {}, "last_updated": None}
                    self.save_memory(memory)
                    st.success("Memory cleared!")
                    st.rerun()

        # Bundle Selection
        st.subheader("📦 Search Bundles")

        bundles = config.get("bundles", {})
        current_bundle = config.get("current_bundle", "Individual Sites")

        # Bundle dropdown
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_bundle = st.selectbox(
                "Select Bundle",
                options=list(bundles.keys()),
                index=list(bundles.keys()).index(current_bundle) if current_bundle in bundles else 0,
                help="Choose a predefined bundle of sites to search"
            )

        with col2:
            bundle_mode = st.radio("Mode", ["Single Site", "Bundle Loop"], horizontal=True)

        # Update current bundle if changed
        if selected_bundle != current_bundle:
            config["current_bundle"] = selected_bundle
            self.save_config(config)

        # Show bundle contents
        if selected_bundle in bundles:
            bundle_sites = bundles[selected_bundle]
            st.info(f"**{selected_bundle}**: {', '.join(bundle_sites)}")
        else:
            bundle_sites = ["cia.gov"]  # Fallback

        # Bundle Management (Admin only)
        if user_role == 'admin':
            with st.expander("🔧 Bundle Management"):
                st.subheader("Create New Bundle")

                col1, col2 = st.columns([2, 1])
                with col1:
                    new_bundle_name = st.text_input("Bundle Name", placeholder="e.g., 'Financial Regulators'")
                with col2:
                    if st.button("Create Bundle", disabled=not new_bundle_name.strip()):
                        if new_bundle_name.strip() and new_bundle_name not in bundles:
                            bundles[new_bundle_name] = []
                            config["bundles"] = bundles
                            config["current_bundle"] = new_bundle_name
                            self.save_config(config)
                            st.success(f"Created bundle: {new_bundle_name}")
                            st.rerun()
                        elif new_bundle_name in bundles:
                            st.warning("Bundle already exists!")

                # Edit existing bundle
                if bundles:
                    st.subheader("Edit Bundle Sites")
                    edit_bundle = st.selectbox("Select bundle to edit", list(bundles.keys()), key="edit_bundle_select")

                    if edit_bundle:
                        current_sites = bundles[edit_bundle]

                        # Add site
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            new_site = st.text_input("Add site", placeholder="e.g., 'sec.gov'", key="new_site_input")
                        with col2:
                            if st.button("Add Site", disabled=not new_site.strip()):
                                if new_site.strip() and new_site not in current_sites:
                                    current_sites.append(new_site.strip())
                                    bundles[edit_bundle] = current_sites
                                    config["bundles"] = bundles
                                    self.save_config(config)
                                    st.success(f"Added {new_site} to {edit_bundle}")
                                    st.rerun()
                                elif new_site in current_sites:
                                    st.warning("Site already in bundle!")

                        # Remove sites
                        if current_sites:
                            st.write("Current sites:")
                            for i, site in enumerate(current_sites):
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.text(site)
                                with col2:
                                    if st.button("🗑️", key=f"remove_site_{i}", help=f"Remove {site}"):
                                        current_sites.remove(site)
                                        bundles[edit_bundle] = current_sites
                                        config["bundles"] = bundles
                                        self.save_config(config)
                                        st.success(f"Removed {site} from {edit_bundle}")
                                        st.rerun()

                        # Delete bundle
                        if st.button(f"🗑️ Delete Bundle: {edit_bundle}", type="secondary"):
                            if st.button(f"⚠️ Confirm Delete {edit_bundle}", key="confirm_delete_bundle"):
                                del bundles[edit_bundle]
                                config["bundles"] = bundles
                                if config.get("current_bundle") == edit_bundle:
                                    config["current_bundle"] = list(bundles.keys())[0] if bundles else "Individual Sites"
                                self.save_config(config)
                                st.success(f"Deleted bundle: {edit_bundle}")
                                st.rerun()

        # Conditional form based on mode
        if bundle_mode == "Single Site":
            # Single Site Configuration
            st.subheader("🔎 Search Configuration")

            # Google search string input - default to first site in bundle for single site mode
            default_site = bundle_sites[0] if bundle_sites else "cia.gov"
            default_search = f"site:{default_site} filetype:pdf"

            search_string = st.text_input(
                "Google Search String",
                value=st.session_state.get("search_string", default_search),
                help="Format: site:foo.com filetype:pdf {searchterm}",
                placeholder="site:cia.gov filetype:pdf intelligence reports"
            )

            # Store in session state for consistency
            st.session_state.search_string = search_string

            # Parse search string
            if search_string:
                parsed = self.parse_google_search(search_string)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.text_input("Site", value=parsed["site"], disabled=True)
                with col2:
                    st.text_input("Filetype", value=parsed["filetype"], disabled=True)
                with col3:
                    st.text_input("Search Terms", value=parsed["search_terms"], disabled=True)
        else:
            # Bundle Loop mode - no individual search configuration
            st.subheader("📦 Bundle Configuration")
            st.info(f"Bundle loop will search for **filetype:pdf** across all sites in **{selected_bundle}** bundle using the parameters below.")

            # Set search_string for bundle mode (used later in logic)
            search_string = "site:bundle filetype:pdf"  # Placeholder for bundle mode

        # Search Parameters (shown for both modes)
        st.subheader("⚙️ Search Parameters")
        col1, col2, col3 = st.columns(3)

        with col1:
            time_filter = st.selectbox(
                "Time Range",
                options=["y", "m", "w", "d"],
                format_func=lambda x: {"y": "Past Year", "m": "Past Month", "w": "Past Week", "d": "Past Day"}[x],
                index=0
            )

        with col2:
            max_docs = st.number_input(
                "Max Documents",
                min_value=10,
                max_value=500,
                value=config.get("default_max_docs", 300),
                step=10
            )

        with col3:
            min_pages = st.number_input(
                "Min Pages",
                min_value=1,
                max_value=100,
                value=config.get("default_min_pages", 18),
                step=1
            )

        # Advanced options in expander
        advanced_title = "⚙️ Advanced Options" + (" (applies to all sites in bundle)" if bundle_mode == "Bundle Loop" else "")
        with st.expander(advanced_title):
            col1, col2 = st.columns(2)

            with col1:
                override_memory = st.checkbox(
                    "Override Memory (re-download existing documents)",
                    value=False,
                    help="Check this to download documents even if they were previously downloaded"
                )

            with col2:
                timeout_seconds = st.number_input(
                    "Request Timeout (seconds)",
                    min_value=30,
                    max_value=300,
                    value=60,
                    step=15,
                    help="Timeout for each PDF request (increase for slow networks)"
                )

        # Output directory
        output_dir = st.text_input(
            "Output Directory",
            value="downloads/pdf_harvest",
            help="Directory to save downloaded PDFs"
        )

        # Saved searches
        if config.get("search_history"):
            st.subheader("💾 Saved Searches")
            saved_searches = config["search_history"]

            if saved_searches:
                for i, search in enumerate(saved_searches):
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        if st.button(f"🔄 {search['query']}", key=f"load_{i}"):
                            st.session_state.selected_search = search["query"]
                            st.rerun()

                    with col2:
                        search_date = datetime.fromisoformat(search['timestamp']).strftime('%m/%d')
                        st.caption(search_date)

                    with col3:
                        if st.button("🗑️", key=f"delete_{i}", help="Delete this saved search"):
                            config["search_history"].pop(i)
                            self.save_config(config)
                            st.success(f"Deleted search: {search['query'][:30]}...")
                            st.rerun()
            else:
                st.info("No saved searches yet. Use 'Save this search' checkbox below.")

        # Save search option
        col1, col2 = st.columns([3, 1])
        with col1:
            save_search = st.checkbox("💾 Save this search for future use",
                                     help="Check this to add the search to your saved searches list")

        # Run harvest button
        harvest_button_text = "🚀 Start Bundle Loop" if bundle_mode == "Bundle Loop" else "🚀 Start PDF Harvest"
        if st.button(harvest_button_text, type="primary"):
            if bundle_mode == "Bundle Loop":
                # Save search if requested
                if save_search:
                    # Check if search already exists
                    existing_searches = [s["query"] for s in config.get("search_history", [])]
                    bundle_query = f"Bundle: {selected_bundle}"
                    if bundle_query not in existing_searches:
                        config["search_history"].append({
                            "query": bundle_query,
                            "timestamp": datetime.now().isoformat(),
                            "site": f"Bundle ({', '.join(bundle_sites)})"
                        })
                        # Keep only last 20 searches
                        config["search_history"] = config["search_history"][-20:]
                        self.save_config(config)
                        st.success(f"✅ Bundle search saved: {selected_bundle}")
                    else:
                        st.info("ℹ️ This bundle search is already in your saved searches.")

                # Run bundle loop
                self.run_bundle_loop(
                    bundle_name=selected_bundle,
                    bundle_sites=bundle_sites,
                    time_filter=time_filter,
                    max_docs=max_docs,
                    min_pages=min_pages,
                    output_dir=output_dir,
                    override_memory=override_memory,
                    api_key=api_key,
                    timeout_seconds=timeout_seconds
                )
            else:
                # Single site mode
                if not search_string.strip():
                    st.error("Please enter a Google search string")
                    return

                # Parse and validate search string
                parsed = self.parse_google_search(search_string)
                if not parsed["site"]:
                    st.error("Please include site: in your search string")
                    return

                # Save to search history only if checkbox is checked
                if save_search:
                    # Check if search already exists
                    existing_searches = [s["query"] for s in config.get("search_history", [])]
                    if search_string not in existing_searches:
                        config["search_history"].append({
                            "query": search_string,
                            "timestamp": datetime.now().isoformat(),
                            "site": parsed["site"]
                        })
                        # Keep only last 20 searches
                        config["search_history"] = config["search_history"][-20:]
                        self.save_config(config)
                        st.success(f"✅ Search saved: {search_string[:50]}...")
                    else:
                        st.info("ℹ️ This search is already in your saved searches.")

                # Run the harvest
                self.run_harvest(
                    parsed=parsed,
                    time_filter=time_filter,
                    max_docs=max_docs,
                    min_pages=min_pages,
                    output_dir=output_dir,
                    override_memory=override_memory,
                    api_key=api_key,
                    timeout_seconds=timeout_seconds
                )

        # Show download history if requested
        if st.session_state.get("show_history", False):
            self.show_download_history(memory)

    def run_harvest(self, parsed: Dict, time_filter: str, max_docs: int,
                   min_pages: int, output_dir: str, override_memory: bool, api_key: str,
                   timeout_seconds: int = 60):
        """Run the PDF harvest process."""

        progress_bar = st.progress(0)
        status_text = st.empty()
        results_container = st.container()
        debug_container = st.container()

        # Add debug info section
        with debug_container:
            st.subheader("🔍 Debug Information")
            debug_expander = st.expander("Debug Details", expanded=True)
            debug_info = []

        try:
            # Initialize crawler
            crawler = ZyteCrawler(api_key, timeout=timeout_seconds)

            debug_info.append(f"Initialized ZyteCrawler (timeout: {timeout_seconds}s)")
            debug_info.append(f"Search: site:{parsed['site']} filetype:{parsed['filetype']} {parsed['search_terms']} | {time_filter} | max:{max_docs} min:{min_pages}p")

            # Step 1: Search Google with pagination
            status_text.text("🔍 Searching Google for PDF URLs...")

            all_pdf_urls = []
            page_size = 10
            max_pages = min(30, (max_docs + page_size - 1) // page_size)

            debug_info.append(f"Starting Google search ({max_pages} pages)")

            with debug_expander:
                for line in debug_info:
                    st.text(line)

            for page in range(max_pages):
                start = page * page_size
                progress = (page + 1) / max_pages * 0.5  # First 50% for searching
                progress_bar.progress(progress)

                status_text.text(f"🔍 Fetching results {start}-{start+page_size-1} (page {page+1}/{max_pages})")

                try:
                    # Build Google search URL
                    google_url = self.build_google_search_url(
                        parsed["site"], parsed["filetype"], parsed["search_terms"],
                        start, page_size, time_filter
                    )

                    # Fetch with Zyte
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

                    response = requests.post('https://api.zyte.com/v1/extract', headers=headers, json=data, timeout=timeout_seconds)
                    response.raise_for_status()

                    html = response.json().get('browserHtml', '')
                    page_pdf_urls = self.extract_pdf_urls_from_google_results(html, parsed["site"])

                    # Add new URLs
                    new_urls_this_page = 0
                    for url in page_pdf_urls:
                        if url not in all_pdf_urls:
                            all_pdf_urls.append(url)
                            new_urls_this_page += 1

                    # Concise combined line
                    if len(page_pdf_urls) > 0:
                        debug_info.append(f"Page {page+1}: {len(page_pdf_urls)} found, {new_urls_this_page} new → {len(all_pdf_urls)} total")

                    # Update debug display
                    with debug_expander:
                        for line in debug_info:
                            st.text(line)

                    if len(page_pdf_urls) == 0:
                        debug_info.append(f"No PDFs found on page {page+1}, stopping search")
                        break

                    time.sleep(2)  # Rate limiting

                except Exception as e:
                    error_msg = f"❌ Error on page {page+1}: {e}"
                    debug_info.append(error_msg)
                    st.warning(error_msg)
                    continue

            debug_info.append(f"Search Complete: Found {len(all_pdf_urls)} total PDF URLs")

            with debug_expander:
                for line in debug_info:
                    st.text(line)

            st.success(f"✅ Found {len(all_pdf_urls)} total PDF URLs")

            # Step 2: Check memory for duplicates
            if not override_memory:
                debug_info.append("🧠 Checking memory for duplicates...")
                memory_check = self.check_already_downloaded(all_pdf_urls, parsed["site"])

                debug_info.append(f"Memory: {memory_check['total_found']} found | {len(memory_check['new_urls'])} new | {len(memory_check['existing_urls'])} downloaded")

                if memory_check["existing_urls"] and len(memory_check["existing_urls"]) <= 3:
                    for url in memory_check["existing_urls"]:
                        debug_info.append(f"  Previously: {Path(url).name}")
                elif len(memory_check["existing_urls"]) > 3:
                    debug_info.append(f"  Previously downloaded: {len(memory_check['existing_urls'])} documents")

                with debug_expander:
                    for line in debug_info:
                        st.text(line)

                with results_container:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Found", memory_check["total_found"])
                    with col2:
                        st.metric("New URLs", len(memory_check["new_urls"]))
                    with col3:
                        st.metric("Already Downloaded", len(memory_check["existing_urls"]))

                if memory_check["existing_urls"]:
                    st.info(f"Skipping {len(memory_check['existing_urls'])} previously downloaded documents")

                pdf_urls_to_process = memory_check["new_urls"]
            else:
                pdf_urls_to_process = all_pdf_urls
                debug_info.append(f"⚠️ Override mode: Processing all {len(all_pdf_urls)} URLs regardless of download history")
                st.info("Override mode: Processing all URLs regardless of download history")

            if not pdf_urls_to_process:
                st.warning("No new documents to process!")
                return

            # Step 3: Evaluate and download
            debug_info.append(f"Evaluating {len(pdf_urls_to_process)} PDFs:")
            with debug_expander:
                for line in debug_info:
                    st.text(line)

            status_text.text(f"📊 Evaluating {len(pdf_urls_to_process)} PDFs for page count...")

            qualifying_docs = []
            processed = 0
            evaluation_data = []

            for pdf_url in pdf_urls_to_process:
                processed += 1
                progress = 0.5 + (processed / len(pdf_urls_to_process)) * 0.3  # 50-80% for evaluation
                progress_bar.progress(progress)

                status_text.text(f"📊 Evaluating {processed}/{len(pdf_urls_to_process)}: {Path(pdf_url).name}")

                try:
                    page_count = crawler.get_pdf_page_count(pdf_url)

                    # Add to evaluation data
                    evaluation_data.append({
                        'Filename': Path(pdf_url).name,
                        'Pages': page_count,
                        'Status': '✅ Qualified' if page_count >= min_pages else f'❌ Too Short ({min_pages}+ required)',
                        'Category': crawler.categorize_pdf(page_count) if page_count > 0 else 'N/A'
                    })

                    if page_count >= min_pages:
                        doc_info = {
                            'url': pdf_url,
                            'pages': page_count,
                            'category': crawler.categorize_pdf(page_count),
                            'filename': crawler._generate_filename(pdf_url, 2025, page_count)
                        }
                        qualifying_docs.append(doc_info)

                    time.sleep(1)  # Rate limiting

                except Exception as e:
                    evaluation_data.append({
                        'Filename': Path(pdf_url).name,
                        'Pages': 'ERROR',
                        'Status': '💥 Evaluation Failed',
                        'Category': 'N/A'
                    })
                    st.warning(f"Error evaluating {pdf_url}: {e}")
                    continue

            # Create and display evaluation DataFrame
            if evaluation_data:
                evaluation_df = pd.DataFrame(evaluation_data)
                debug_info.append(f"Evaluation completed: {len(evaluation_data)} documents processed")

            with debug_expander:
                for line in debug_info:
                    st.text(line)

                # Display evaluation table as DataFrame
                if evaluation_data:
                    st.subheader("📊 Document Evaluation Results")
                    st.dataframe(
                        evaluation_df,
                        use_container_width=True,
                        column_config={
                            "Filename": st.column_config.TextColumn("Document", width="large"),
                            "Pages": st.column_config.NumberColumn("Pages", width="small"),
                            "Status": st.column_config.TextColumn("Status", width="medium"),
                            "Category": st.column_config.TextColumn("Size Category", width="small")
                        }
                    )

            st.success(f"✅ Found {len(qualifying_docs)} documents with ≥{min_pages} pages")

            # Step 4: Download
            if qualifying_docs:
                status_text.text(f"📥 Downloading {len(qualifying_docs)} qualifying documents...")

                downloaded = 0
                downloaded_urls = []

                for i, doc in enumerate(qualifying_docs):
                    progress = 0.8 + (i / len(qualifying_docs)) * 0.2  # 80-100% for downloading
                    progress_bar.progress(progress)

                    status_text.text(f"📥 Downloading {i+1}/{len(qualifying_docs)}: {doc['filename']}")

                    try:
                        success = crawler.download_pdf(doc['url'], doc['filename'], output_dir)

                        if success:
                            downloaded += 1
                            downloaded_urls.append(doc['url'])
                            debug_info.append(f"✅ Downloaded: {doc['filename']} ({doc['pages']} pages)")
                        else:
                            debug_info.append(f"❌ Download failed: {doc['filename']}")
                            st.warning(f"❌ Download failed: {doc['filename']}")

                        time.sleep(2)  # Rate limiting

                    except Exception as e:
                        debug_info.append(f"💥 Download error: {doc['filename']} - {e}")
                        st.warning(f"Error downloading {doc['filename']}: {e}")
                        continue

                # Update memory
                if downloaded_urls:
                    self.mark_urls_as_downloaded(downloaded_urls, parsed["site"])

                # Add final download summary to debug
                debug_info.append(f"Download complete: {downloaded}/{len(qualifying_docs)} successful")

                # Update debug display with download results
                with debug_expander:
                    for line in debug_info:
                        st.text(line)

                # Final results
                progress_bar.progress(1.0)
                status_text.text("✅ Harvest complete!")

                with results_container:
                    st.subheader("📊 Final Results")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total URLs Found", len(all_pdf_urls))
                    with col2:
                        st.metric("Qualified Documents", len(qualifying_docs))
                    with col3:
                        st.metric("Successfully Downloaded", downloaded)
                    with col4:
                        st.metric("Success Rate", f"{downloaded/len(qualifying_docs)*100:.1f}%" if qualifying_docs else "0%")

                    if downloaded > 0:
                        st.success(f"🎉 Successfully downloaded {downloaded} documents to {output_dir}")

                    # Show evaluation summary
                    if 'evaluation_df' in locals():
                        st.subheader("📄 Document Evaluation Summary")

                        # Summary stats
                        qualified_count = len(evaluation_df[evaluation_df['Status'].str.contains('✅')])
                        too_short_count = len(evaluation_df[evaluation_df['Status'].str.contains('❌')])
                        error_count = len(evaluation_df[evaluation_df['Status'].str.contains('💥')])

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("✅ Qualified", qualified_count)
                        with col2:
                            st.metric("❌ Too Short", too_short_count)
                        with col3:
                            st.metric("💥 Errors", error_count)

                        # Show full evaluation table
                        st.dataframe(
                            evaluation_df,
                            use_container_width=True,
                            column_config={
                                "Filename": st.column_config.TextColumn("Document", width="large"),
                                "Pages": st.column_config.NumberColumn("Pages", width="small"),
                                "Status": st.column_config.TextColumn("Status", width="medium"),
                                "Category": st.column_config.TextColumn("Size Category", width="small")
                            }
                        )

                        # Show download details for qualified docs
                        if downloaded > 0 and st.checkbox("Show download details"):
                            df = pd.DataFrame(qualifying_docs)
                            st.dataframe(df[['filename', 'pages', 'category']])

            else:
                st.warning("No documents met the minimum page requirement")

        except Exception as e:
            st.error(f"❌ Error during harvest: {e}")

    def run_bundle_loop(self, bundle_name: str, bundle_sites: List[str], time_filter: str,
                       max_docs: int, min_pages: int, output_dir: str, override_memory: bool,
                       api_key: str, timeout_seconds: int = 60):
        """Run harvest for all sites in a bundle."""

        st.subheader(f"📦 Bundle Loop: {bundle_name}")
        st.info(f"Processing {len(bundle_sites)} sites: {', '.join(bundle_sites)}")

        bundle_progress = st.progress(0)
        bundle_status = st.empty()
        bundle_results = []

        for i, site in enumerate(bundle_sites):
            progress = (i / len(bundle_sites))
            bundle_progress.progress(progress)
            bundle_status.text(f"🔄 Processing site {i+1}/{len(bundle_sites)}: {site}")

            st.subheader(f"🔍 Processing: {site}")

            # Create search string for this site
            search_string = f"site:{site} filetype:pdf"
            parsed = self.parse_google_search(search_string)

            # Create a unique output directory for this site
            site_output_dir = f"{output_dir}/{site.replace('.', '_')}"

            try:
                # Track results for this site
                site_results = {"site": site, "total_found": 0, "qualified": 0, "downloaded": 0, "errors": []}

                # Run harvest for this site
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.container()
                debug_container = st.container()

                # Initialize memory and crawler for this site
                memory = self.load_memory()
                crawler = ZyteCrawler(api_key, timeout=timeout_seconds)

                # Initialize debugging
                with debug_container:
                    debug_expander = st.expander(f"🔍 Debug Information - {site}", expanded=False)

                debug_info = []
                status_text.text(f"🔍 Searching {site} for PDF documents...")

                # Parse search parameters
                time_filter_map = {"y": "past year", "m": "past month", "w": "past week", "d": "past day"}
                debug_info.append(f"Search: {search_string} | {time_filter_map.get(time_filter, time_filter)} | max:{max_docs} min:{min_pages}p")

                # Step 1: Search for PDFs
                all_pdf_urls = []

                # Build Google search URL and paginate
                for page in range(min(30, (max_docs + 9) // 10)):
                    try:
                        google_url = f"https://www.google.com/search?q=site:{site}+filetype:pdf&num=10&tbs=qdr:{time_filter}&start={page*10}"

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

                        response = requests.post('https://api.zyte.com/v1/extract', headers=headers, json=data, timeout=timeout_seconds)
                        response.raise_for_status()

                        html = response.json().get('browserHtml', '')
                        page_pdf_urls = self.extract_pdf_urls_from_google_results(html, site)

                        # Add new URLs
                        new_urls_this_page = 0
                        for url in page_pdf_urls:
                            if url not in all_pdf_urls:
                                all_pdf_urls.append(url)
                                new_urls_this_page += 1

                        # Concise combined line
                        if len(page_pdf_urls) > 0:
                            debug_info.append(f"Page {page+1}: {len(page_pdf_urls)} found, {new_urls_this_page} new → {len(all_pdf_urls)} total")

                        if len(page_pdf_urls) == 0:
                            break

                        time.sleep(2)  # Rate limiting

                    except Exception as e:
                        debug_info.append(f"❌ Error on page {page+1}: {e}")
                        continue

                site_results["total_found"] = len(all_pdf_urls)
                debug_info.append(f"Search Complete: Found {len(all_pdf_urls)} total PDF URLs")

                # Step 2: Memory check
                if not override_memory:
                    memory_check = self.check_already_downloaded(all_pdf_urls, site)
                    pdf_urls_to_process = memory_check["new_urls"]
                    debug_info.append(f"Memory: {memory_check['total_found']} found | {len(memory_check['new_urls'])} new | {len(memory_check['existing_urls'])} downloaded")
                else:
                    pdf_urls_to_process = all_pdf_urls

                if pdf_urls_to_process:
                    # Step 3: Evaluate and download
                    status_text.text(f"📊 Evaluating {len(pdf_urls_to_process)} PDFs for {site}...")

                    qualifying_docs = []
                    downloaded = 0

                    for j, pdf_url in enumerate(pdf_urls_to_process):
                        try:
                            page_count = crawler.get_pdf_page_count(pdf_url)

                            if page_count >= min_pages:
                                doc_info = {
                                    'url': pdf_url,
                                    'pages': page_count,
                                    'category': crawler.categorize_pdf(page_count),
                                    'filename': crawler._generate_filename(pdf_url, 2025, page_count)
                                }
                                qualifying_docs.append(doc_info)

                                # Download immediately
                                success = crawler.download_pdf(doc_info['url'], doc_info['filename'], site_output_dir)
                                if success:
                                    downloaded += 1
                                    debug_info.append(f"✅ Downloaded: {doc_info['filename']} ({page_count} pages)")
                                else:
                                    debug_info.append(f"❌ Download failed: {doc_info['filename']}")

                            time.sleep(1)  # Rate limiting

                        except Exception as e:
                            debug_info.append(f"💥 Error processing {pdf_url}: {e}")
                            site_results["errors"].append(str(e))
                            continue

                    site_results["qualified"] = len(qualifying_docs)
                    site_results["downloaded"] = downloaded

                    # Update memory for this site
                    if downloaded > 0:
                        downloaded_urls = [doc['url'] for doc in qualifying_docs if downloaded > 0]
                        self.mark_urls_as_downloaded(downloaded_urls, site)

                # Update debug display
                with debug_expander:
                    for line in debug_info:
                        st.text(line)

                # Show results for this site
                with results_container:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(f"📄 {site} - Total Found", site_results["total_found"])
                    with col2:
                        st.metric("✅ Qualified", site_results["qualified"])
                    with col3:
                        st.metric("📥 Downloaded", site_results["downloaded"])

                bundle_results.append(site_results)

            except Exception as e:
                st.error(f"❌ Error processing {site}: {e}")
                site_results = {"site": site, "total_found": 0, "qualified": 0, "downloaded": 0, "errors": [str(e)]}
                bundle_results.append(site_results)

        # Final bundle summary
        bundle_progress.progress(1.0)
        bundle_status.text("✅ Bundle loop complete!")

        st.subheader("📊 Bundle Summary")

        total_found = sum(r["total_found"] for r in bundle_results)
        total_qualified = sum(r["qualified"] for r in bundle_results)
        total_downloaded = sum(r["downloaded"] for r in bundle_results)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Sites Processed", len(bundle_sites))
        with col2:
            st.metric("Total Found", total_found)
        with col3:
            st.metric("Total Qualified", total_qualified)
        with col4:
            st.metric("Total Downloaded", total_downloaded)

        # Detailed results table
        if bundle_results:
            df = pd.DataFrame(bundle_results)
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "site": st.column_config.TextColumn("Site", width="medium"),
                    "total_found": st.column_config.NumberColumn("Found", width="small"),
                    "qualified": st.column_config.NumberColumn("Qualified", width="small"),
                    "downloaded": st.column_config.NumberColumn("Downloaded", width="small")
                }
            )

    def show_download_history(self, memory: Dict):
        """Show download history."""
        st.subheader("📁 Download History")

        downloaded_urls = memory.get("downloaded_urls", {})

        if not downloaded_urls:
            st.info("No download history found")
            return

        for site, urls in downloaded_urls.items():
            with st.expander(f"{site} ({len(urls)} documents)"):
                for url in urls:
                    st.text(url)


def render():
    """Main render function for the page."""
    page = PDFHarvesterPage()
    page.render_page()


if __name__ == "__main__":
    render()