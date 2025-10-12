import streamlit as st
import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, '/Users/fred/xcu_my_apps')
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from codexes.modules.imprint_builder.streamlit_ui import render_imprint_builder_page

# Page configuration
st.set_page_config(
    page_title="Streamlined Imprint Builder",
    page_icon="🏢",
    layout="wide"
)

# Render the new streamlined imprint builder interface
render_imprint_builder_page()