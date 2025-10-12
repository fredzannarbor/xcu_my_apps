import json
import logging
import os
import sys
import traceback

import pandas as pd
import streamlit as st

st.set_page_config(layout="wide", page_title="FROs")
# Setup paths - MUST come before FRO imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.extend([parent_dir, grandparent_dir])

# FRO imports - only after paths are set up

import src.classes.FinancialReportingObjects.FRO_utilities as FRO_utilities

from src.classes.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects


# Initialize FRO
FRO = FinancialReportingObjects("/Users/fred/initiatives/nimble/repos/codexes-leo-bloom")
level = 2
st.spinner("Loading Financial Reporting Objects from files")
infobox = st.empty()
# Dictionary of file attributes and their display titles
file_paths = {

    "this_month_unit_sales_file_path": "This Month's Unit Sales",
    "LSI_LTD_paid_file_path": "LSI Lifetime To Date Paid Data",
    "LSI_unpaid_file_path": "LSI Unpaid Data",
    "LSI_year_data_file_path": "LSI Year Data",
    "kdp_lifetime_orders_file_path": "KDP Lifetime Orders",
    "rights_revenue_file_path": "Rights Revenue Data",
    "full_metadata_ingest_file_path": "Full Metadata Ingest Data",
    "full_metadata_enhanced_file_path": "Full Metadata Enhanced Data",
    "add2fme_file_path": "Additional FME Data",
    "actual_payment_history_file_path": "Payment History",
    "resolve_author_names_file_path": "Author Names Resolution Data",
    "direct_sales_file_path": "Direct Sales",
    "ecommerce_sales_file_path": "Ecommerce Sales",
    "apple_digital_agency_file_path" : "Apple Digital Agency", "lsi_royalties_due_file_path": "LSI Royalties Due"}
# Create status tracking dictionary
status_data = {"File": [], "Status": [], "Details": []}

# Loop through each file path
for attr, title in file_paths.items():
    infobox.info(f"loading {title}...")
    if hasattr(FRO, attr):
        file_path = getattr(FRO, attr)
        try:
            # Check if file is JSON
            if file_path.endswith(".json"):
                with open(file_path, "r") as f:
                    data = json.load(f)
                # Check if "authors" is a key at the specified level in the JSON file
                details = f"Authors: {FRO_utilities.count_authors(data):,}"

            else:
                data = FRO_utilities.load_spreadsheet(file_path)
                details = f"{data.shape[0]:,}×{data.shape[1]:,}"

            status_data["File"].append(title)
            status_data["Status"].append("✅")
            status_data["Details"].append(details)

        except Exception as e:
            status_data["File"].append(title)
            status_data["Status"].append("❌")
            status_data["Details"].append(str(e))
            logging.error(traceback.format_exc())
            infobox.info(f"Problem loading {title}: {e}")

# Display summary table at the top
st.write("## Summary of File Loading Status")
status_df = pd.DataFrame(status_data)
st.table(status_df)

# Display individual file contents
for attr, title in file_paths.items():
    if hasattr(FRO, attr):
        st.write(f"## {title}")
        file_path = getattr(FRO, attr)
        st.caption(f"File path: {file_path}")

        try:
            if file_path.endswith(".json"):
                with open(file_path, "r") as f:
                    data = json.load(f)
                st.write("JSON file contents (collapsed):")
                st.json(data)
            else:
                data = FRO_utilities.load_spreadsheet(file_path)
                st.write(data)
        except Exception as e:
            st.error(
                f"Could not load {title} file at {file_path}. "
                f"Please check that the file exists and is in the correct location."
            )
