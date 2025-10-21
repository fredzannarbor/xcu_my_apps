import streamlit as st
import os
import sys
import logging
import json
import pandas as pd
from datetime import datetime
import traceback
from io import StringIO
from pathlib import Path
from typing import Dict, Any, List



logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)



# --- Path Setup ---
sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
    from shared.ui import render_unified_sidebar
except ImportError as e:
    import streamlit as st
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()


project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from codexes.core.config import MODELS_CHOICE, PROMPT_FILE_NAME
from codexes.core import file_handler, llm_caller, prompt_manager
from codexes.core.translations import get_translation
from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.metadata.metadata_generator import generate_metadata_from_prompts
from codexes.modules.distribution.lsi_acs_generator import LsiAcsGenerator
from codexes.modules.distribution.storefront_generator import StorefrontGenerator


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize shared authentication system
try:
    shared_auth = get_shared_auth()
    logger.info("Shared authentication system initialized")
except Exception as e:
    logger.error(f"Failed to initialize shared auth: {e}")
    st.error("Authentication system unavailable.")


# --- Configuration for Distribution Formats ---
DISTRIBUTION_FORMATS = {
    "lsi_acs": {
        "label": "LSI ACS (CSV)",
        "generator_class": LsiAcsGenerator,
        "template_name": "templates/LSI_ACS_header.csv"
    },
    "bookstore_catalog": {
                "label": "Bookstore Catalog (CSV)",
        "generator_class": StorefrontGenerator,
        "template_name": None  # This generator doesn't require a template
    },
}

def load_all_prompts_from_directory(prompt_dir_path: str) -> Dict[str, Any]:
    '''
    Loads all prompts from JSON files in a directory for UI selection.

    Args:
        prompt_dir_path (str): The path to the directory containing prompt files.

    Returns:
        Dict[str, Any]: A dictionary of all available prompts.
    '''
    all_prompts = {}
    if not os.path.exists(prompt_dir_path):
        logging.error(f"Prompt directory not found at: {prompt_dir_path}")
        return all_prompts

    for filename in os.listdir(prompt_dir_path):
        if filename.endswith('.json'):
            file_path = os.path.join(prompt_dir_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    prompts = json.load(f)
                    all_prompts.update(prompts)
            except (IOError, json.JSONDecodeError) as e:
                logging.warning(f"Could not load or parse prompt file {filename}: {e}")

    return all_prompts

# --- Initialize Session State ---
if 'metadata_result' not in st.session_state:
    st.session_state.metadata_result = None
if 'distribution_outputs' not in st.session_state:
    st.session_state.distribution_outputs = {}
if 'language' not in st.session_state:
    st.session_state.language = 'en' # Default language

T = lambda key, **kwargs: get_translation(st.session_state.language, key, **kwargs)

# NOTE: st.set_page_config() and render_unified_sidebar() handled by main app

# NOTE: st.set_page_config() and render_unified_sidebar() handled by main app
# DO NOT render sidebar here - it's already rendered by codexes-factory-home-ui.py

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




st.title("📊 Metadata & Distribution")
st.markdown("Generate comprehensive metadata and distribution files from your manuscript.")

# --- Main Configuration Form ---
with st.form("metadata_form"):
    st.header("Workflow Configuration")
    uploaded_file = st.file_uploader("1. Upload Manuscript", type=['pdf', 'txt', 'docx'])

    model_choice = st.selectbox(
        "2. Select AI Model",
        options=MODELS_CHOICE,
        index=0
    )

    prompt_dir_path = os.path.join(project_root, "prompts")
    all_prompts_dict = load_all_prompts_from_directory(prompt_dir_path)

    if not all_prompts_dict:
        st.error(f"Prompt directory '{prompt_dir_path}' not found or is empty.")
        prompt_keys = []
    else:
        suggested_prompts = [
            "gemini_get_basic_info",
            "bibliographic_key_phrases",
            "storefront_get_en_metadata",
            "storefront_get_ko_metadata",
            "storefront_get_en_motivation",
            "storefront_get_ko_motivation"
        ]
        prompt_keys = st.multiselect(
            "3. Select Metadata Tasks",
            options=sorted(list(all_prompts_dict.keys())),
            default=[p for p in suggested_prompts if p in all_prompts_dict],
            help="Choose one or more prompts to run. The results will be combined."
        )

    format_options = {key: data["label"] for key, data in DISTRIBUTION_FORMATS.items()}
    selected_formats = st.multiselect(
        "4. Select Distribution Formats",
        options=list(format_options.keys()),
        format_func=lambda key: format_options[key],
        default=list(format_options.keys()),
        help="Select one or more output formats."
    )

    generate_button = st.form_submit_button(
        "Generate Metadata & Distribution Files",
        type="primary",
        disabled=(not uploaded_file or not prompt_keys or not selected_formats)
    )

# --- Main Processing Logic ---
if generate_button:
    with st.spinner("Processing... This may take several minutes."):
        st.session_state.metadata_result = None
        st.session_state.distribution_outputs = {}

        temp_dir = os.path.join(project_root, 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, uploaded_file.name)

        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            logging.info(f"UI: Temp file saved to {file_path}")

            prompt_file_path = os.path.join(prompt_dir_path, PROMPT_FILE_NAME)
            
            # --- Generate the central CodexMetadata object ---
            codex_metadata = generate_metadata_from_prompts(
                file_path=str(file_path),
                model_name=model_choice,
                prompt_file_path=prompt_file_path,
                prompt_keys=prompt_keys
            )

            if not codex_metadata:
                st.error("Metadata generation failed. Check logs for details.")
                st.stop()
            
            st.session_state.metadata_result = codex_metadata.to_dict() # Store for viewing
            st.success(f"Successfully generated metadata for {uploaded_file.name}.")
            
            # --- Generate Distribution Files ---
            output_dir = os.path.join(project_root, "output")
            os.makedirs(output_dir, exist_ok=True)
            input_basename = os.path.splitext(uploaded_file.name)[0]
            timestamp = datetime.now().strftime('%Y%m%d%H%M')

            for format_key in selected_formats:
                format_info = DISTRIBUTION_FORMATS.get(format_key)
                if not format_info:
                    continue

                try:
                    GeneratorClass = format_info["generator_class"]
                    output_filename = f"{input_basename}_{format_key.upper()}_{timestamp}.csv"
                    output_path = os.path.join(output_dir, output_filename)

                    # Instantiate generator
                    kwargs = {}
                    if format_info.get("template_name"):
                        template_path = os.path.join(project_root, format_info["template_name"])
                        if not os.path.exists(template_path):
                            st.error(f"Template for {format_info['label']} not found: {template_path}")
                            continue
                        kwargs['template_path'] = template_path
                    
                    generator = GeneratorClass(**kwargs)
                    
                    # Generate the file using the CodexMetadata object
                    generator.generate(codex_metadata, output_path)

                    # Store results for display
                    with open(output_path, 'r', encoding='utf-8-sig') as f:
                        file_data = f.read()

                    st.session_state.distribution_outputs[format_key] = {
                        "label": format_info["label"],
                        "path": output_path,
                        "data": file_data
                    }
                    logging.info(f"UI: Successfully generated file for {format_info['label']}")

                except Exception as e:
                    logging.error(f"Failed to generate file for {format_info['label']}: {e}", exc_info=True)
                    st.error(f"Failed to generate file for {format_info['label']}: {e}")

        except Exception as e:
            logging.error(f"UI Error: {e}", exc_info=True)
            st.error(f"An unexpected error occurred: {e}")
            st.code(traceback.format_exc())
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

# --- Display Results ---
if st.session_state.get('distribution_outputs'):
    st.subheader("✅ Generation Complete!")
    
    outputs = st.session_state.distribution_outputs
    
    # Create tabs for each generated file
    tab_titles = [output['label'] for output in outputs.values()]
    tabs = st.tabs(tab_titles)
    
    for i, (format_key, output_data) in enumerate(outputs.items()):
        with tabs[i]:
            st.markdown(f"#### {output_data['label']}")
            st.download_button(
                label=f"Download {os.path.basename(output_data['path'])}",
                data=output_data['data'].encode('utf-8-sig'),
                file_name=os.path.basename(output_data['path']),
                mime='text/csv',
                key=f"download_{format_key}"
            )

            try:
                # Use StringIO to read the CSV data string into a DataFrame
                df_preview = pd.read_csv(StringIO(output_data['data']))
                
                # Transpose for better readability if it's a single row of data
                if len(df_preview) == 1:
                    st.dataframe(df_preview.T.reset_index().rename(columns={'index': 'Field', 0: 'Value'}), use_container_width=True, hide_index=True)
                else:
                    st.dataframe(df_preview, use_container_width=True)

            except Exception as e:
                st.error(f"Could not display a preview for the generated file: {e}")
                st.text_area("Raw Content", output_data['data'], height=300, key=f"preview_raw_{format_key}")

if st.session_state.get('metadata_result'):
    with st.expander("View Full Generated Metadata Object (JSON)"):
        st.json(st.session_state.metadata_result)
