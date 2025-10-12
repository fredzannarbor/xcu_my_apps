# src/codexes/pages/12_Bibliography_Shopping.py
import streamlit as st
from pathlib import Path
import json
import os
import sys

sys.path.insert(0, '/Users/fred/xcu_my_apps')

st.set_page_config(page_title="Bibliography Shopping", layout="wide")

st.title("📚 Shop for Works Mentioned")
st.markdown("Find and purchase books referenced in the quotations.")

# Check if shopping list exists
shopping_dir = Path("data/bibliography_shopping_lists")
shopping_file = shopping_dir / "bibliography_shopping_list.html"

if not shopping_file.exists():
    st.warning("No bibliography shopping list has been generated yet. Run the Book Pipeline or Backmatter Manager first.")
    st.stop()

# Read the HTML content
with open(shopping_file, "r", encoding="utf-8") as f:
    html_content = f.read()

# Display the HTML content
st.components.v1.html(html_content, height=800, scrolling=True)

# Add a link to the catalog
st.markdown("---")
st.markdown("Return to the [catalog](/catalog) to explore more books.")