"""
Philately Collection Management System - Streamlit UI
Version 1.1.0 - Migrated to shared authentication system
"""

import streamlit as st
import sys
from pathlib import Path
import logging
from io import StringIO
import pandas as pd

sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
    from shared.ui import render_unified_sidebar
except ImportError as e:
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()

from philately.processor_v2 import PhilatelyProcessor

# Configure logging
logger = logging.getLogger(__name__)

# Initialize shared authentication system
try:
    shared_auth = get_shared_auth()
    logger.info("Shared authentication system initialized")
except Exception as e:
    logger.error(f"Failed to initialize shared auth: {e}")
    st.error("Authentication system unavailable.")

# --- Logging Handler for Streamlit ---
class StreamlitLogHandler(logging.Handler):
    """A logging handler that writes records to a Streamlit text area."""

    def __init__(self, text_area):
        super().__init__()
        self.text_area = text_area
        self.buffer = StringIO()

    def emit(self, record):
        self.buffer.write(self.format(record) + "\n")
        self.text_area.text_area(
            "Live Log Output",
            self.buffer.getvalue(),
            height=400,
            key="log_output_area",
        )

def main():
    """Main function to run the Streamlit UI."""
    st.set_page_config(
        page_title="Philately Processor",
        layout="wide",
    )

    # Sync session state from shared auth
    if is_authenticated():
        user_info = get_user_info()
        st.session_state.username = user_info.get('username')
        st.session_state.user_name = user_info.get('user_name')
        st.session_state.user_email = user_info.get('user_email')
        logger.info(f"User authenticated via shared auth: {st.session_state.username}")
    else:
        if "username" not in st.session_state:
            st.session_state.username = None

    # Hide native Streamlit navigation
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

    # Render unified sidebar
    render_unified_sidebar(
        app_name="Philately Collection Manager",
        show_auth=True,
        show_xtuff_nav=True
    )

    st.title("Philately Collection Management System 🤖 🖼️")
    st.markdown(
        "An AI-powered tool to analyze, catalog, and manage your stamp collection."
    )

    # --- Main Window UI Controls ---

    with st.expander("⚙️ Configuration", expanded=True):
        st.subheader("Directory Paths")
        image_dir = st.text_input(
            "Image Directory Path",
            "stamps",
            help="Path to the directory containing stamp images organized in album folders.",
        )
        output_dir = st.text_input(
            "Output Directory Path",
            "output",
            help="Path to the directory where all output files will be saved.",
        )

        st.subheader("AI Model Selection")
        c1, c2 = st.columns(2)
        with c1:
            low_cost_model = st.text_input(
                "Low-Cost Vision Model", "gemini/gemini-1.5-flash-latest"
            )
            narrative_model = st.text_input(
                "Narrative/Enrichment Model", "gemini/gemini-1.5-pro-latest"
            )
        with c2:
            high_cost_model = st.text_input(
                "High-Cost Vision Model", "gemini/gemini-1.5-pro-latest"
            )
            collection_summary_model = st.text_input(
                "Collection Summary Model", "gemini/gemini-1.5-pro-latest"
            )

        st.subheader("Processing Parameters")
        c1, c2, c3 = st.columns(3)
        with c1:
            confidence_threshold = st.slider(
                "Confidence Threshold",
                1,
                7,
                5,
                help="Confidence score (1-7) below which to trigger re-analysis with a high-cost model.",
            )
        with c2:
            high_value_threshold = st.number_input(
                "High-Value Threshold ($)",
                min_value=0,
                value=1000,
                help="USD threshold to consider a stamp as high-value for reporting.",
            )
        with c3:
            max_images = st.number_input(
                "Max Images to Process (0 for all)",
                min_value=0,
                value=0,
                help="Limit the number of images for testing. Set to 0 to process all images.",
            )

    with st.expander("⚙️ Execution & Phases", expanded=True):
        st.subheader("Execution Phases")
        all_phases = [
            "Image Analysis",
            "Philatelic Enrichment",
            "Clustering and Summaries",
            "High-Value Report",
            "False Positive Check",
            "Substack Export",
            "Collection-Wide Summary Only",
        ]
        selected_phases = st.multiselect(
            "Select phases to run (or leave empty to run all)",
            all_phases,
            default=[],
            help="If no phases are selected, the entire pipeline will run sequentially.",
        )

        # --- Phase-Specific Options ---
        c1, c2 = st.columns(2)
        with c1:
            if "False Positive Check" in selected_phases or not selected_phases:
                false_positive_check_limit = st.number_input(
                    "False Positive Check Limit (0 for all)",
                    min_value=0,
                    value=5,
                    help="Limit the number of stamps to check in the false-positive phase.",
                )
            else:
                false_positive_check_limit = 5
        with c2:
            if "Substack Export" in selected_phases or not selected_phases:
                substack_items = st.number_input(
                    "Substack Export Items (0 for all)",
                    min_value=0,
                    value=10,
                    help="Number of top items to include in the Substack export.",
                )
            else:
                substack_items = 10

        debug_mode = st.checkbox(
            "Enable Debug Mode",
            value=False,
            help="Enable verbose, debug-level logging for detailed output.",
        )

    # --- Main Application Area ---
    start_button = st.button("🚀 Start Processing", type="primary", use_container_width=True)

    # Placeholders for results
    log_placeholder = st.empty()
    results_placeholder = st.container()

    if start_button:
        # --- Setup Logging ---
        log_level = logging.DEBUG if debug_mode else logging.INFO

        # Remove all handlers associated with the root logger object.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Create our custom handler
        streamlit_handler = StreamlitLogHandler(log_placeholder)

        # Configure logging
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            handlers=[streamlit_handler, logging.StreamHandler(sys.stdout)],  # Also log to console
        )

        # Suppress noisy logs from underlying libraries
        for lib in ["openai", "httpx", "httpcore", "litellm"]:
            logging.getLogger(lib).setLevel(logging.WARNING)

        logger = logging.getLogger(__name__)

        # --- Instantiate and Run Processor ---
        try:
            # Convert paths from string to Path objects
            image_dir_path = Path(image_dir)
            output_dir_path = Path(output_dir)

            if not image_dir_path.is_dir():
                st.error(f"Image directory not found: {image_dir_path}")
                st.stop()

            processor = PhilatelyProcessor(
                image_dir=image_dir_path, output_dir=output_dir_path
            )

            run_all = not selected_phases

            with st.spinner("Processing... Please wait."):
                if run_all or "Image Analysis" in selected_phases:
                    processor.run_image_analysis_phase(
                        confidence_threshold,
                        max_images=max_images if max_images > 0 else None,
                        low_cost_model=low_cost_model,
                        high_cost_model=high_cost_model,
                    )

                if run_all or "Philatelic Enrichment" in selected_phases:
                    processor.run_philatelic_enrichment_phase(
                        narrative_model=narrative_model
                    )

                if run_all or "Clustering and Summaries" in selected_phases:
                    processor.run_clustering_and_summary_phase(
                        narrative_model=narrative_model,
                        collection_summary_model=collection_summary_model,
                        collection_only=False,
                    )
                elif "Collection-Wide Summary Only" in selected_phases:
                    processor.run_clustering_and_summary_phase(
                        narrative_model=narrative_model,
                        collection_summary_model=collection_summary_model,
                        collection_only=True,
                    )

                if run_all or "High-Value Report" in selected_phases:
                    processor.run_high_value_report_phase(
                        value_threshold=high_value_threshold
                    )

                if run_all or "False Positive Check" in selected_phases:
                    processor.run_false_positive_check_phase(
                        high_cost_model=high_cost_model,
                        value_threshold=high_value_threshold,
                        check_limit=false_positive_check_limit,
                    )

                if run_all or "Substack Export" in selected_phases:
                    processor.run_substack_export_phase(num_items=substack_items)

            st.success("✅ Processing finished successfully!")

            # --- Display Results ---
            with results_placeholder:
                st.header("📊 Results")

                master_inventory_path = output_dir_path / "master_inventory.csv"
                if master_inventory_path.exists():
                    st.subheader("Master Inventory")
                    df_master = pd.read_csv(master_inventory_path)
                    st.dataframe(df_master)
                    st.download_button(
                        "Download Master Inventory CSV",
                        df_master.to_csv(index=False).encode("utf-8"),
                        "master_inventory.csv",
                        "text/csv",
                    )
                else:
                    st.warning("Master inventory file was not generated.")

                fp_report_path = output_dir_path / "false_positive_check_report.csv"
                if fp_report_path.exists():
                    st.subheader("False Positive Check Report")
                    df_fp = pd.read_csv(fp_report_path)
                    st.dataframe(df_fp)
                    st.download_button(
                        "Download False Positive Report CSV",
                        df_fp.to_csv(index=False).encode("utf-8"),
                        "false_positive_check_report.csv",
                        "text/csv",
                    )

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            logger.error("An error occurred during Streamlit execution.", exc_info=True)

    # --- Sidebar Information ---
    st.sidebar.header("About")
    st.sidebar.info(
        "This application uses AI to analyze images of a stamp collection, "
        "extract metadata, and generate a comprehensive, queryable inventory."
    )
    st.sidebar.header("Instructions")
    st.sidebar.markdown(
        """
1.  **Configure** the directory paths and processing parameters.
2.  **Select** the specific processing phases you want to run, or leave empty to run all.
3.  **Click** 'Start Processing' to begin.
4.  **Monitor** the live log output for progress.
5.  **Review** and download the results when processing is complete.
"""
    )

if __name__ == "__main__":
    main()
