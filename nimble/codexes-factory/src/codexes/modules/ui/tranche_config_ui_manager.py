"""
Tranche configuration UI manager for Book Pipeline interface.
"""

import os
import json
import glob
from typing import Dict, List, Any, Optional
import logging
import streamlit as st
from src.codexes.modules.distribution.multi_level_config import MultiLevelConfiguration

logger = logging.getLogger(__name__)


class TrancheConfigUIManager:
    """Manage tranche configuration display and selection in Book Pipeline UI"""
    
    def __init__(self, config_loader: Optional[MultiLevelConfiguration] = None):
        self.config_loader = config_loader or MultiLevelConfiguration()
        self.available_tranches: List[Dict[str, Any]] = []
        self.tranches_dir = "configs/tranches"
        self._load_available_tranches()
    
    def _load_available_tranches(self) -> None:
        """Load all available tranche configurations"""
        try:
            self.available_tranches = []

            # Check if tranches directory exists
            if not os.path.exists(self.tranches_dir):
                logger.warning(f"Tranches directory not found: {self.tranches_dir}")
                return

            # Find all JSON files in tranches directory
            tranche_files = glob.glob(os.path.join(self.tranches_dir, "*.json"))

            for tranche_file in tranche_files:
                try:
                    with open(tranche_file, 'r', encoding='utf-8') as f:
                        tranche_config = json.load(f)

                    # Extract tranche name from filename
                    tranche_name = os.path.splitext(os.path.basename(tranche_file))[0]

                    tranche_info = {
                        'name': tranche_name,
                        'display_name': tranche_config.get('display_name', tranche_name),
                        'description': tranche_config.get('description', ''),
                        'config_path': tranche_file,
                        'config': tranche_config
                    }

                    self.available_tranches.append(tranche_info)
                    logger.debug(f"Loaded tranche configuration: {tranche_name}")

                except Exception as e:
                    logger.error(f"Error loading tranche config {tranche_file}: {e}")

            # Add default configurations for imprints without specific tranche files
            self._add_default_imprint_tranches()

            # Sort by display name for consistent UI
            self.available_tranches.sort(key=lambda x: x['display_name'])
            logger.info(f"Loaded {len(self.available_tranches)} tranche configurations")

        except Exception as e:
            logger.error(f"Error loading available tranches: {e}")
            self.available_tranches = []

    def _add_default_imprint_tranches(self) -> None:
        """Add default tranche configurations for imprints without specific tranche files"""
        try:
            # Get all existing tranche imprints to avoid duplicates
            existing_imprints = set()
            for tranche in self.available_tranches:
                imprint_name = tranche['config'].get('imprint', '')
                if imprint_name:
                    existing_imprints.add(imprint_name)

            # Check imprints directory for available imprints
            imprints_dir = "imprints"
            if not os.path.exists(imprints_dir):
                return

            for imprint_path in os.listdir(imprints_dir):
                imprint_full_path = os.path.join(imprints_dir, imprint_path)
                if os.path.isdir(imprint_full_path) and imprint_path not in existing_imprints:
                    # Skip system directories
                    if imprint_path.startswith('.'):
                        continue

                    # Create default tranche configuration
                    default_config = self._create_default_tranche_config(imprint_path)

                    tranche_info = {
                        'name': f"{imprint_path}_default",
                        'display_name': f"{imprint_path.replace('_', ' ').title()} (Default)",
                        'description': f"Default configuration for {imprint_path} imprint",
                        'config_path': None,  # No physical file, generated dynamically
                        'config': default_config,
                        'is_default': True
                    }

                    self.available_tranches.append(tranche_info)
                    logger.debug(f"Added default tranche for imprint: {imprint_path}")

        except Exception as e:
            logger.error(f"Error adding default imprint tranches: {e}")

    def _create_default_tranche_config(self, imprint_name: str) -> Dict[str, Any]:
        """Create a default tranche configuration for an imprint"""
        return {
            "_config_info": {
                "description": f"Auto-generated default configuration for {imprint_name} imprint",
                "version": "1.0",
                "last_updated": "auto-generated",
                "config_type": "default_tranche"
            },
            "display_name": f"{imprint_name.replace('_', ' ').title()} (Default)",
            "description": f"Default configuration for {imprint_name} imprint",
            "tranche_info": {
                "tranche_id": f"{imprint_name}-default",
                "tranche_name": f"{imprint_name.replace('_', ' ').title()} Default",
                "tranche_description": f"Default tranche for {imprint_name} imprint",
                "book_count": 10,
                "target_month": "TBD",
                "target_year": "TBD"
            },
            "publisher": "Nimble Books LLC",
            "imprint": imprint_name,
            "lightning_source_account": "6024045",
            "cover_submission_method": "FTP",
            "text_block_submission_method": "FTP",
            "rendition_booktype": "POD: 6 x 9 in or 229 x 152 mm Perfect Bound WHITE",
            "carton_pack_quantity": "",
            "order_type_eligibility": "POD",
            "language_code": "eng",
            "country_of_origin": "US",
            "territorial_rights": "World",
            "returnability": "Yes",
            "binding_type": "paperback",
            "interior_color": "BW",
            "interior_paper": "Standard 70 perfect",
            "trim_size": "6x9",
            "cover_type": "matte",
            "default_price": "24.99",
            "currency": "USD",
            "us_wholesale_discount": "40",
            "uk_wholesale_discount": "40",
            "eu_wholesale_discount": "40",
            "ca_wholesale_discount": "40",
            "au_wholesale_discount": "40"
        }

    def load_available_tranches(self) -> List[Dict[str, Any]]:
        """Load all available tranche configurations for dropdown display"""
        self._load_available_tranches()
        return self.available_tranches.copy()
    
    def refresh_tranche_dropdown(self) -> List[str]:
        """Refresh tranche dropdown options in UI"""
        try:
            self._load_available_tranches()
            
            if not self.available_tranches:
                return ["No tranche configurations found"]
            
            # Return list of display names for dropdown
            return [tranche['display_name'] for tranche in self.available_tranches]
            
        except Exception as e:
            logger.error(f"Error refreshing tranche dropdown: {e}")
            return ["Error loading tranches"]
    
    def get_tranche_names(self) -> List[str]:
        """Get list of tranche names for dropdown"""
        try:
            if not self.available_tranches:
                self._load_available_tranches()

            return [tranche['name'] for tranche in self.available_tranches]

        except Exception as e:
            logger.error(f"Error getting tranche names: {e}")
            return []

    def get_available_publishers(self) -> List[str]:
        """Get list of unique publishers from tranche configurations."""
        try:
            if not self.available_tranches:
                self._load_available_tranches()

            publishers = set()
            for tranche in self.available_tranches:
                publisher = tranche['config'].get('publisher', '')
                if publisher:
                    publishers.add(publisher)

            return sorted(list(publishers))

        except Exception as e:
            logger.error(f"Error getting publishers: {e}")
            return []

    def get_imprints_for_publisher(self, publisher: str) -> List[str]:
        """Get list of imprints for a specific publisher."""
        try:
            if not self.available_tranches:
                self._load_available_tranches()

            imprints = set()
            for tranche in self.available_tranches:
                if tranche['config'].get('publisher', '') == publisher:
                    imprint = tranche['config'].get('imprint', '')
                    if imprint:
                        imprints.add(imprint)

            return sorted(list(imprints))

        except Exception as e:
            logger.error(f"Error getting imprints for publisher {publisher}: {e}")
            return []

    def get_tranches_for_imprint(self, publisher: str, imprint: str) -> List[Dict[str, Any]]:
        """Get list of tranches for a specific publisher/imprint combination."""
        try:
            if not self.available_tranches:
                self._load_available_tranches()

            matching_tranches = []
            for tranche in self.available_tranches:
                config = tranche['config']
                if (config.get('publisher', '') == publisher and
                    config.get('imprint', '') == imprint):
                    matching_tranches.append(tranche)

            return matching_tranches

        except Exception as e:
            logger.error(f"Error getting tranches for {publisher}/{imprint}: {e}")
            return []
    
    def validate_tranche_selection(self, tranche_name: str) -> bool:
        """Validate that selected tranche configuration exists and is valid"""
        try:
            if not tranche_name:
                return False
            
            # Find tranche by name or display name
            tranche_info = self.get_tranche_info(tranche_name)
            if not tranche_info:
                return False
            
            # Validate configuration structure
            config = tranche_info['config']
            
            # Check for required fields
            required_fields = ['imprint', 'publisher']
            for field in required_fields:
                if field not in config:
                    logger.warning(f"Tranche {tranche_name} missing required field: {field}")
                    return False
            
            # Validate file exists and is readable
            config_path = tranche_info['config_path']
            if not os.path.exists(config_path):
                logger.error(f"Tranche config file not found: {config_path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating tranche selection {tranche_name}: {e}")
            return False
    
    def get_tranche_config(self, tranche_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve configuration for selected tranche"""
        try:
            tranche_info = self.get_tranche_info(tranche_name)
            if tranche_info:
                return tranche_info['config'].copy()
            return None
            
        except Exception as e:
            logger.error(f"Error getting tranche config for {tranche_name}: {e}")
            return None
    
    def get_tranche_info(self, tranche_identifier: str) -> Optional[Dict[str, Any]]:
        """Get tranche info by name or display name"""
        try:
            for tranche in self.available_tranches:
                if (tranche['name'] == tranche_identifier or 
                    tranche['display_name'] == tranche_identifier):
                    return tranche
            return None
            
        except Exception as e:
            logger.error(f"Error getting tranche info for {tranche_identifier}: {e}")
            return None
    
    def render_hierarchical_selector(self, key: str = "hierarchical_selector") -> Dict[str, str]:
        """Render hierarchical Publisher → Imprint → Tranche selector."""
        try:
            # Initialize return values
            selection = {
                'publisher': '',
                'imprint': '',
                'tranche': '',
                'tranche_config': None
            }

            # Get available publishers
            publishers = self.get_available_publishers()

            if not publishers:
                st.error("No publishers found in tranche configurations.")
                return selection

            # Publisher selection (required)
            selected_publisher = st.selectbox(
                "1️⃣ Select Publisher (Required)",
                options=[""] + publishers,
                key=f"{key}_publisher",
                help="Choose the publisher organization"
            )

            if not selected_publisher:
                st.info("👆 Please select a publisher to continue")
                return selection

            selection['publisher'] = selected_publisher

            # Imprint selection (optional)
            imprints = self.get_imprints_for_publisher(selected_publisher)

            if imprints:
                selected_imprint = st.selectbox(
                    "2️⃣ Select Imprint (Optional)",
                    options=["[Use Publisher Identity]"] + imprints,
                    key=f"{key}_imprint",
                    help="Choose an imprint, or use publisher identity as default"
                )

                if selected_imprint and selected_imprint != "[Use Publisher Identity]":
                    selection['imprint'] = selected_imprint
                else:
                    selection['imprint'] = ''  # Will use publisher identity
            else:
                st.info("No specific imprints found - using publisher identity")
                selection['imprint'] = ''

            # Tranche selection (optional)
            if selection['imprint']:
                tranches = self.get_tranches_for_imprint(selected_publisher, selection['imprint'])
            else:
                # Get tranches that match publisher but have no specific imprint or empty imprint
                tranches = []
                for tranche in self.available_tranches:
                    config = tranche['config']
                    if (config.get('publisher', '') == selected_publisher and
                        not config.get('imprint', '')):
                        tranches.append(tranche)

            if tranches:
                tranche_options = ["[No Tranche - Ad Hoc Rows]"] + [t['display_name'] for t in tranches]
                selected_tranche_display = st.selectbox(
                    "3️⃣ Select Tranche (Optional)",
                    options=tranche_options,
                    key=f"{key}_tranche",
                    help="Choose a tranche for shared metadata, or use ad hoc individual book settings"
                )

                if selected_tranche_display and selected_tranche_display != "[No Tranche - Ad Hoc Rows]":
                    # Find the tranche by display name
                    for tranche in tranches:
                        if tranche['display_name'] == selected_tranche_display:
                            selection['tranche'] = tranche['name']
                            selection['tranche_config'] = tranche['config']
                            break
            else:
                st.info("No specific tranches found - will use ad hoc individual book settings")

            # Show hierarchy summary
            if selection['publisher']:
                with st.expander("📋 Selection Summary", expanded=True):
                    st.markdown(f"**Publisher:** {selection['publisher']}")
                    if selection['imprint']:
                        st.markdown(f"**Imprint:** {selection['imprint']}")
                    else:
                        st.markdown(f"**Imprint:** *Using publisher identity*")

                    if selection['tranche']:
                        st.markdown(f"**Tranche:** {selection['tranche']}")
                        st.markdown("📊 *Books will share common metadata from tranche configuration*")
                    else:
                        st.markdown(f"**Tranche:** *Ad hoc individual settings*")
                        st.markdown("📝 *Each book row will have individual metadata settings*")

            return selection

        except Exception as e:
            logger.error(f"Error rendering hierarchical selector: {e}")
            st.error(f"Error rendering hierarchical selector: {e}")
            return {
                'publisher': '',
                'imprint': '',
                'tranche': '',
                'tranche_config': None
            }

    def render_tranche_selector(self, key: str = "tranche_selector") -> Optional[str]:
        """Render Streamlit tranche selector widget"""
        try:
            tranche_options = self.refresh_tranche_dropdown()
            
            if not tranche_options or tranche_options == ["No tranche configurations found"]:
                st.error("No tranche configurations found. Please add tranche configurations to the configs/tranches directory.")
                return None
            
            if tranche_options == ["Error loading tranches"]:
                st.error("Error loading tranche configurations. Please check the logs for details.")
                return None
            
            # Create selectbox with tranche options
            selected_display_name = st.selectbox(
                "Select Tranche Configuration",
                options=tranche_options,
                key=key,
                help="Choose the tranche configuration for this book processing run"
            )
            
            if selected_display_name:
                # Find the actual tranche name from display name
                tranche_info = self.get_tranche_info(selected_display_name)
                if tranche_info:
                    # Show tranche details
                    if tranche_info['description']:
                        st.info(f"Description: {tranche_info['description']}")
                    
                    # Validate selection
                    if self.validate_tranche_selection(tranche_info['name']):
                        return tranche_info['name']
                    else:
                        st.error(f"Invalid tranche configuration: {tranche_info['name']}")
                        return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error rendering tranche selector: {e}")
            st.error(f"Error rendering tranche selector: {e}")
            return None
    
    def render_tranche_details(self, tranche_name: str) -> None:
        """Render detailed information about selected tranche"""
        try:
            if not tranche_name:
                return
            
            tranche_config = self.get_tranche_config(tranche_name)
            if not tranche_config:
                st.error(f"Could not load configuration for tranche: {tranche_name}")
                return
            
            with st.expander("Tranche Configuration Details"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Basic Information:**")
                    st.write(f"- **Name:** {tranche_name}")
                    st.write(f"- **Imprint:** {tranche_config.get('imprint', 'Not specified')}")
                    st.write(f"- **Publisher:** {tranche_config.get('publisher', 'Not specified')}")
                
                with col2:
                    st.write("**Configuration:**")
                    if 'contributor_one' in tranche_config:
                        st.write(f"- **Author:** {tranche_config['contributor_one']}")
                    if 'language' in tranche_config:
                        st.write(f"- **Language:** {tranche_config['language']}")
                    if 'market' in tranche_config:
                        st.write(f"- **Market:** {tranche_config['market']}")
                
                # Show full config in JSON format
                st.write("**Full Configuration:**")
                st.json(tranche_config)
                
        except Exception as e:
            logger.error(f"Error rendering tranche details: {e}")
            st.error(f"Error displaying tranche details: {e}")
    
    def create_new_tranche_form(self) -> None:
        """Render form for creating new tranche configuration"""
        try:
            st.subheader("Create New Tranche Configuration")
            
            with st.form("new_tranche_form"):
                tranche_name = st.text_input("Tranche Name", help="Unique identifier for this tranche")
                display_name = st.text_input("Display Name", help="Human-readable name for UI")
                description = st.text_area("Description", help="Optional description of this tranche")
                
                col1, col2 = st.columns(2)
                with col1:
                    imprint = st.text_input("Imprint", help="Associated imprint name")
                    publisher = st.text_input("Publisher", help="Publisher name")
                
                with col2:
                    contributor_one = st.text_input("Primary Author", help="Main author/contributor")
                    language = st.selectbox("Language", ["en", "ko", "es", "fr", "de"], help="Primary language")
                
                submitted = st.form_submit_button("Create Tranche Configuration")
                
                if submitted:
                    if tranche_name and imprint and publisher:
                        success = self._create_tranche_config(
                            tranche_name, display_name, description,
                            imprint, publisher, contributor_one, language
                        )
                        if success:
                            st.success(f"Tranche configuration '{tranche_name}' created successfully!")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to create tranche configuration. Check logs for details.")
                    else:
                        st.error("Please fill in all required fields (Tranche Name, Imprint, Publisher)")
                        
        except Exception as e:
            logger.error(f"Error creating new tranche form: {e}")
            st.error(f"Error creating form: {e}")
    
    def _create_tranche_config(self, name: str, display_name: str, description: str,
                              imprint: str, publisher: str, contributor_one: str, language: str) -> bool:
        """Create new tranche configuration file"""
        try:
            # Ensure tranches directory exists
            os.makedirs(self.tranches_dir, exist_ok=True)
            
            # Create configuration
            config = {
                "display_name": display_name or name,
                "description": description,
                "imprint": imprint,
                "publisher": publisher,
                "language": language,
                "created_date": "2025-01-01",  # Would use actual date
                "version": "1.0"
            }
            
            if contributor_one:
                config["contributor_one"] = contributor_one
            
            # Write to file
            config_path = os.path.join(self.tranches_dir, f"{name}.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created tranche configuration: {config_path}")
            
            # Refresh available tranches
            self._load_available_tranches()
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating tranche config: {e}")
            return False