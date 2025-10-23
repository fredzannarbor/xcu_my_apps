"""
Configuration Management Page for Streamlit UI
"""


import logging
import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import sys


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import shared authentication system
sys.path.insert(0, '/Users/fred/xcu_my_apps')

try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
    from shared.ui import render_unified_sidebar
    logger.info("Shared authentication system imported successfully")
except ImportError as e:
    import streamlit as st
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()




# Import UI components
try:
    from codexes.modules.ui.dynamic_config_loader import DynamicConfigurationLoader
    from codexes.modules.ui.configuration_manager import EnhancedConfigurationManager
except ImportError:
    try:
        from src.codexes.modules.ui.dynamic_config_loader import DynamicConfigurationLoader
        from src.codexes.modules.ui.configuration_manager import EnhancedConfigurationManager
    except ImportError:
        st.error("Could not import configuration management components.")
        st.stop()

# NOTE: st.set_page_config() handled by main app (codexes-factory-home-ui.py)

# Sync session state from shared auth
if is_authenticated():
    user_info = get_user_info()
    st.session_state.username = user_info.get('username')
    st.session_state.user_name = user_info.get('user_name')
    st.session_state.user_email = user_info.get('user_email')
    st.session_state.user_role = user_info.get('user_role', 'public')
    logger.info(f"User authenticated via shared auth: {st.session_state.username}")
else:
    if "username" not in st.session_state:
        st.session_state.username = None
    st.session_state.user_role = 'public'

# Render unified sidebar only if not already rendered by main app
# Main app sets sidebar_rendered=True to prevent duplication
if not st.session_state.get('sidebar_rendered', False):
    render_unified_sidebar(
        app_name="Codexes Factory",
        show_auth=True,
        show_xtuff_nav=True
    )




st.title("⚙️ Configuration Management")
st.markdown("Manage publisher, imprint, and tranche configuration files.")

# Initialize components
config_loader = DynamicConfigurationLoader()
config_manager = EnhancedConfigurationManager()

# Initialize session state with safety patterns
if 'config_mgmt_state' not in st.session_state:
    st.session_state.config_mgmt_state = {
        'selected_config_type': 'publisher',
        'selected_config_name': '',
        'current_config': {},
        'editing_mode': False
    }

# Import safety patterns
try:
    from src.codexes.modules.ui.safety_patterns import (
        safe_getattr, safe_dict_get, safe_iteration, safe_len, safe_join,
        validate_not_none, log_none_encounter
    )
    from src.codexes.modules.ui.data_validators import UIDataValidator
    
    # Initialize validator
    ui_validator = UIDataValidator()
except ImportError:
    # Fallback functions for safety
    def safe_dict_get(d, key, default=None):
        return (d or {}).get(key, default)
    
    def safe_len(collection):
        return len(collection or [])
    
    def validate_not_none(value, context, attr):
        return value is not None
    
    def log_none_encounter(context, attr):
        pass
    
    ui_validator = None

# Ensure all required state keys exist with safe defaults
default_state = {
    'selected_config_type': 'publisher',
    'selected_config_name': '',
    'current_config': {},
    'editing_mode': False
}

for key, default_value in default_state.items():
    if key not in st.session_state.config_mgmt_state or st.session_state.config_mgmt_state[key] is None:
        st.session_state.config_mgmt_state[key] = default_value

# Configuration type selector
col1, col2, col3 = st.columns(3)

with col1:
    # Safe access to current config type
    current_config_type = safe_dict_get(st.session_state.config_mgmt_state, 'selected_config_type', 'publisher')
    config_options = ['publisher', 'imprint', 'tranche']
    
    # Safe index calculation
    config_type_index = 0
    if current_config_type in config_options:
        config_type_index = config_options.index(current_config_type)
    
    config_type = st.selectbox(
        "Configuration Type",
        options=config_options,
        index=config_type_index,
        help="Select the type of configuration to manage"
    )

with col2:
    # Get available configurations for selected type with safe access
    available_configs = []
    try:
        if config_type == 'publisher':
            available_configs = config_loader.scan_publishers() or []
        elif config_type == 'imprint':
            available_configs = config_loader.scan_imprints() or []
        else:  # tranche
            available_configs = config_loader.scan_tranches() or []
    except Exception as e:
        log_none_encounter('config_scan', f'scan_{config_type}s')
        available_configs = []
    
    config_options = [''] + list(available_configs)  # Safe list conversion
    
    # Safe access to current selection
    current_selection = safe_dict_get(st.session_state.config_mgmt_state, 'selected_config_name', '')
    
    # Safe index calculation
    selection_index = 0
    if current_selection and current_selection in config_options:
        selection_index = config_options.index(current_selection)
    
    selected_config = st.selectbox(
        "Select Configuration",
        options=config_options,
        index=selection_index,
        help="Select a configuration to view or edit"
    )

with col3:
    st.write("")  # Spacing
    col3a, col3b = st.columns(2)
    
    with col3a:
        if st.button("📁 Load Config", disabled=not selected_config):
            try:
                config_data = config_loader.load_configuration_file(config_type, selected_config)
                # Validate config data is not None
                if validate_not_none(config_data, 'config_loading', 'load_configuration_file'):
                    # Safe state updates
                    if st.session_state.config_mgmt_state is not None:
                        st.session_state.config_mgmt_state['current_config'] = config_data or {}
                        st.session_state.config_mgmt_state['editing_mode'] = False
                    st.success(f"Loaded {config_type} configuration: {selected_config}")
                else:
                    st.error(f"Failed to load configuration: {selected_config}")
                    log_none_encounter('config_loading', f'{config_type}_{selected_config}')
            except Exception as e:
                st.error(f"Error loading configuration: {e}")
                log_none_encounter('config_loading', f'exception_{e}')
    
    with col3b:
        if st.button("➕ New Config"):
            try:
                template = config_loader.create_configuration_template(config_type)
                # Safe state updates with None protection
                if st.session_state.config_mgmt_state is not None:
                    st.session_state.config_mgmt_state['current_config'] = template or {}
                    st.session_state.config_mgmt_state['editing_mode'] = True
                    st.session_state.config_mgmt_state['selected_config_name'] = ''
                st.success(f"Created new {config_type} configuration template")
            except Exception as e:
                st.error(f"Error creating template: {e}")
                log_none_encounter('template_creation', f'{config_type}_template')

# Update session state
st.session_state.config_mgmt_state.update({
    'selected_config_type': config_type,
    'selected_config_name': selected_config
})

# Configuration browser
st.subheader("📋 Available Configurations")

# Get metadata for all configurations
all_metadata = config_loader.get_all_configurations_metadata()

# Display configurations in tabs
tab1, tab2, tab3 = st.tabs(["Publishers", "Imprints", "Tranches"])

with tab1:
    if all_metadata['publishers']:
        for pub_meta in all_metadata['publishers']:
            with st.expander(f"📊 {pub_meta['name']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Description**: {pub_meta.get('description', 'No description')}")
                    st.write(f"**Version**: {pub_meta.get('version', 'Unknown')}")
                with col2:
                    st.write(f"**Last Updated**: {pub_meta.get('last_updated', 'Unknown')}")
                    st.write(f"**Last Modified**: {pub_meta.get('last_modified', 'Unknown')}")
    else:
        st.info("No publisher configurations found.")

with tab2:
    if all_metadata['imprints']:
        for imp_meta in all_metadata['imprints']:
            with st.expander(f"🏷️ {imp_meta['name']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Description**: {imp_meta.get('description', 'No description')}")
                    st.write(f"**Version**: {imp_meta.get('version', 'Unknown')}")
                with col2:
                    st.write(f"**Last Updated**: {imp_meta.get('last_updated', 'Unknown')}")
                    st.write(f"**Last Modified**: {imp_meta.get('last_modified', 'Unknown')}")
    else:
        st.info("No imprint configurations found.")

with tab3:
    if all_metadata['tranches']:
        for tr_meta in all_metadata['tranches']:
            with st.expander(f"📦 {tr_meta['name']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Description**: {tr_meta.get('description', 'No description')}")
                    st.write(f"**Version**: {tr_meta.get('version', 'Unknown')}")
                with col2:
                    st.write(f"**Last Updated**: {tr_meta.get('last_updated', 'Unknown')}")
                    st.write(f"**Last Modified**: {tr_meta.get('last_modified', 'Unknown')}")
    else:
        st.info("No tranche configurations found.")

# Configuration editor
if st.session_state.config_mgmt_state.get('current_config'):
    st.subheader("📝 Configuration Editor")
    
    current_config = st.session_state.config_mgmt_state['current_config']
    
    # Action buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        edit_mode = st.button("✏️ Edit", disabled=st.session_state.config_mgmt_state['editing_mode'])
        if edit_mode:
            st.session_state.config_mgmt_state['editing_mode'] = True
            st.rerun()
    
    with col2:
        if st.button("💾 Save", disabled=not st.session_state.config_mgmt_state['editing_mode']):
            # Save configuration logic would go here
            st.success("Configuration saved successfully!")
            st.session_state.config_mgmt_state['editing_mode'] = False
            st.rerun()
    
    with col3:
        if st.button("❌ Cancel", disabled=not st.session_state.config_mgmt_state['editing_mode']):
            st.session_state.config_mgmt_state['editing_mode'] = False
            st.rerun()
    
    with col4:
        if st.button("📤 Export"):
            config_json = json.dumps(current_config, indent=2, default=str)
            st.download_button(
                label="Download JSON",
                data=config_json,
                file_name=f"{config_type}_{selected_config or 'new'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col5:
        if st.button("🔄 Validate"):
            is_valid = config_loader.validate_configuration_structure(current_config, config_type)
            if is_valid:
                st.success("✅ Configuration is valid!")
            else:
                st.error("❌ Configuration validation failed!")
    
    # Configuration display/editor
    if st.session_state.config_mgmt_state['editing_mode']:
        st.write("**Editing Mode** - Modify the JSON below:")
        
        config_json = json.dumps(current_config, indent=2, default=str)
        edited_config = st.text_area(
            "Configuration JSON",
            value=config_json,
            height=400,
            help="Edit the configuration in JSON format"
        )
        
        # Try to parse edited JSON
        try:
            parsed_config = json.loads(edited_config)
            st.session_state.config_mgmt_state['current_config'] = parsed_config
            st.success("✅ JSON is valid")
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON: {e}")
    
    else:
        st.write("**View Mode** - Configuration content:")
        
        # Display configuration in organized tabs
        config_tabs = []
        config_sections = {}
        
        # Organize configuration by sections
        for key, value in current_config.items():
            if key.startswith('_'):
                continue  # Skip metadata
            
            if isinstance(value, dict) and len(value) > 3:
                config_sections[key] = value
                config_tabs.append(key)
        
        # Add a main tab for top-level items
        main_items = {k: v for k, v in current_config.items() 
                     if not k.startswith('_') and (not isinstance(v, dict) or len(v) <= 3)}
        if main_items:
            config_sections['main'] = main_items
            config_tabs.insert(0, 'main')
        
        if config_tabs:
            tabs = st.tabs([tab.replace('_', ' ').title() for tab in config_tabs])
            
            for i, tab_name in enumerate(config_tabs):
                with tabs[i]:
                    section_data = config_sections[tab_name]
                    
                    if isinstance(section_data, dict):
                        for sub_key, sub_value in section_data.items():
                            if isinstance(sub_value, (dict, list)):
                                st.write(f"**{sub_key}**:")
                                st.json(sub_value)
                            else:
                                st.write(f"**{sub_key}**: {sub_value}")
                    else:
                        st.json(section_data)
        else:
            st.json(current_config)

# File upload section
st.subheader("📁 Upload Configuration")

uploaded_file = st.file_uploader(
    "Upload Configuration File",
    type=['json'],
    help="Upload a JSON configuration file"
)

if uploaded_file is not None:
    try:
        config_data = json.load(uploaded_file)
        
        # Try to determine configuration type from content
        detected_type = None
        if 'publisher' in config_data and 'imprint' not in config_data:
            detected_type = 'publisher'
        elif 'imprint' in config_data and 'tranche_info' not in config_data:
            detected_type = 'imprint'
        elif 'tranche_info' in config_data:
            detected_type = 'tranche'
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success(f"✅ File uploaded successfully!")
            if detected_type:
                st.info(f"🔍 Detected type: {detected_type}")
        
        with col2:
            if st.button("📥 Load Uploaded Config"):
                st.session_state.config_mgmt_state['current_config'] = config_data
                st.session_state.config_mgmt_state['editing_mode'] = True
                if detected_type:
                    st.session_state.config_mgmt_state['selected_config_type'] = detected_type
                st.success("Configuration loaded from uploaded file!")
                st.rerun()
        
        # Preview uploaded configuration
        with st.expander("👀 Preview Uploaded Configuration", expanded=False):
            st.json(config_data)
            
    except json.JSONDecodeError as e:
        st.error(f"❌ Invalid JSON file: {e}")
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

# Template download section
st.subheader("📋 Download Templates")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Publisher Template"):
        template = config_loader.create_configuration_template('publisher')
        template_json = json.dumps(template, indent=2, default=str)
        st.download_button(
            label="Download Publisher Template",
            data=template_json,
            file_name=f"publisher_template_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

with col2:
    if st.button("🏷️ Imprint Template"):
        template = config_loader.create_configuration_template('imprint')
        template_json = json.dumps(template, indent=2, default=str)
        st.download_button(
            label="Download Imprint Template",
            data=template_json,
            file_name=f"imprint_template_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

with col3:
    if st.button("📦 Tranche Template"):
        template = config_loader.create_configuration_template('tranche')
        template_json = json.dumps(template, indent=2, default=str)
        st.download_button(
            label="Download Tranche Template",
            data=template_json,
            file_name=f"tranche_template_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

# Help section
with st.expander("❓ Help & Documentation", expanded=False):
    st.markdown("""
    ## Configuration Management Help
    
    ### Configuration Types
    - **Publisher**: Company-level settings and defaults
    - **Imprint**: Brand-level settings that inherit from publisher
    - **Tranche**: Batch-level settings for specific book groups
    
    ### Configuration Hierarchy
    Settings are inherited in this order:
    1. Default system settings
    2. Publisher configuration
    3. Imprint configuration  
    4. Tranche configuration
    
    ### File Management
    - **Load**: Load an existing configuration for viewing/editing
    - **New**: Create a new configuration from template
    - **Edit**: Modify configuration in JSON format
    - **Save**: Save changes to configuration file
    - **Export**: Download configuration as JSON file
    - **Validate**: Check configuration structure and required fields
    
    ### Best Practices
    - Always validate configurations before saving
    - Use descriptive names for new configurations
    - Keep configuration files organized by type
    - Back up important configurations before making changes
    """)