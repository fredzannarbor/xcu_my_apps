"""
DropdownManager - Handles dropdown dependencies and refresh logic without causing rerun loops
"""

import streamlit as st
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DropdownManager:
    """Manages dropdown dependencies and refresh logic without causing rerun loops"""
    
    def __init__(self):
        self.debounce_delay = 0.1  # 100ms debounce
        self.cache_ttl = 30.0  # 30 second cache TTL
        
        # Initialize session state if needed
        if 'dropdown_manager_state' not in st.session_state:
            st.session_state.dropdown_manager_state = {
                'publisher_imprints_cache': {},
                'imprint_tranches_cache': {},
                'last_cache_update': 0.0,
                'last_update_timestamp': 0.0,
                'update_pending': False,
                'debounce_key': ''
            }
    
    def handle_publisher_change(self, old_publisher: str, new_publisher: str) -> bool:
        """
        Handle publisher change without causing rerun loops
        
        Args:
            old_publisher: Previous publisher selection
            new_publisher: New publisher selection
            
        Returns:
            bool: True if dependent dropdowns need refresh
        """
        if old_publisher == new_publisher:
            return False
        
        current_time = time.time()
        state = st.session_state.dropdown_manager_state
        
        # Check debounce timing
        if current_time - state['last_update_timestamp'] < self.debounce_delay:
            logger.debug(f"Debouncing publisher change: {old_publisher} -> {new_publisher}")
            return False
        
        logger.info(f"Handling publisher change: {old_publisher} -> {new_publisher}")
        
        # Update timestamp
        state['last_update_timestamp'] = current_time
        
        # Clear dependent selections when publisher changes
        if 'config_ui_state' in st.session_state:
            config_state = st.session_state.config_ui_state
            
            # Only clear if the new publisher doesn't support current imprint
            current_imprint = config_state.get('selected_imprint', '')
            if current_imprint and not self._is_imprint_valid_for_publisher(new_publisher, current_imprint):
                config_state['selected_imprint'] = ''
                config_state['selected_tranche'] = ''
                logger.debug(f"Cleared invalid imprint selection: {current_imprint}")
        
        # Mark that dependent dropdowns need refresh
        state['update_pending'] = True
        state['debounce_key'] = f"{new_publisher}_{current_time}"
        
        return True
    
    def get_imprints_for_publisher(self, publisher: str) -> List[str]:
        """
        Get imprints for a publisher with caching
        
        Args:
            publisher: Publisher name
            
        Returns:
            List of imprint names
        """
        if not publisher:
            return []
        
        state = st.session_state.dropdown_manager_state
        current_time = time.time()
        
        # Check cache validity
        cache_key = f"imprints_{publisher}"
        if (cache_key in state['publisher_imprints_cache'] and 
            current_time - state['last_cache_update'] < self.cache_ttl):
            return state['publisher_imprints_cache'][cache_key]
        
        # Load imprints from filesystem
        imprints = self._scan_imprints_for_publisher(publisher)
        
        # Update cache
        state['publisher_imprints_cache'][cache_key] = imprints
        state['last_cache_update'] = current_time
        
        logger.debug(f"Loaded {len(imprints)} imprints for publisher {publisher}: {imprints}")
        return imprints
    
    def get_tranches_for_imprint(self, imprint: str) -> List[str]:
        """
        Get tranches for an imprint with caching
        
        Args:
            imprint: Imprint name
            
        Returns:
            List of tranche names
        """
        if not imprint:
            return []
        
        state = st.session_state.dropdown_manager_state
        current_time = time.time()
        
        # Check cache validity
        cache_key = f"tranches_{imprint}"
        if (cache_key in state['imprint_tranches_cache'] and 
            current_time - state['last_cache_update'] < self.cache_ttl):
            return state['imprint_tranches_cache'][cache_key]
        
        # Load tranches from filesystem
        tranches = self._scan_tranches_for_imprint(imprint)
        
        # Update cache
        state['imprint_tranches_cache'][cache_key] = tranches
        state['last_cache_update'] = current_time
        
        logger.debug(f"Loaded {len(tranches)} tranches for imprint {imprint}: {tranches}")
        return tranches
    
    def should_refresh_dropdowns(self) -> bool:
        """
        Check if dropdowns should be refreshed based on pending updates
        
        Returns:
            bool: True if refresh is needed
        """
        state = st.session_state.dropdown_manager_state
        return state.get('update_pending', False)
    
    def mark_refresh_complete(self):
        """Mark that dropdown refresh has been completed"""
        state = st.session_state.dropdown_manager_state
        state['update_pending'] = False
        logger.debug("Dropdown refresh marked as complete")
    
    def clear_cache(self):
        """Clear all cached data"""
        state = st.session_state.dropdown_manager_state
        state['publisher_imprints_cache'].clear()
        state['imprint_tranches_cache'].clear()
        state['last_cache_update'] = 0.0
        logger.info("Dropdown manager cache cleared")
    
    def _is_imprint_valid_for_publisher(self, publisher: str, imprint: str) -> bool:
        """Check if an imprint is valid for a given publisher"""
        if not publisher or not imprint:
            return False
        
        valid_imprints = self.get_imprints_for_publisher(publisher)
        return imprint in valid_imprints
    
    def _scan_imprints_for_publisher(self, publisher: str) -> List[str]:
        """Scan filesystem for imprints belonging to a publisher"""
        try:
            # Check configs/imprints directory for imprint configs
            imprints_dir = Path("configs/imprints")
            if not imprints_dir.exists():
                return []
            
            # Load the publisher config to get the full publisher name
            publisher_name = self._get_publisher_name(publisher)
            if not publisher_name:
                logger.warning(f"Could not find publisher config for: {publisher}")
                return []
            
            imprints = []
            for config_file in imprints_dir.glob("*.json"):
                if config_file.name.endswith('_template.json'):
                    continue
                
                try:
                    import json
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    
                    # Check if this imprint belongs to the publisher
                    # Compare against the full publisher name from the publisher config
                    if config.get('publisher') == publisher_name:
                        imprint_name = config_file.stem
                        imprints.append(imprint_name)
                        
                except Exception as e:
                    logger.warning(f"Error reading imprint config {config_file}: {e}")
                    continue
            
            return sorted(imprints)
            
        except Exception as e:
            logger.error(f"Error scanning imprints for publisher {publisher}: {e}")
            return []
    
    def _get_publisher_name(self, publisher_key: str) -> Optional[str]:
        """Get the full publisher name from the publisher config file"""
        try:
            publisher_config_path = Path(f"configs/publishers/{publisher_key}.json")
            if not publisher_config_path.exists():
                return None
            
            import json
            with open(publisher_config_path, 'r') as f:
                config = json.load(f)
            
            return config.get('publisher')
            
        except Exception as e:
            logger.error(f"Error loading publisher config for {publisher_key}: {e}")
            return None
    
    def _scan_tranches_for_imprint(self, imprint: str) -> List[str]:
        """Scan filesystem for tranches belonging to an imprint"""
        try:
            # Check configs/tranches directory for tranche configs
            tranches_dir = Path("configs/tranches")
            if not tranches_dir.exists():
                return []
            
            tranches = []
            for config_file in tranches_dir.glob("*.json"):
                try:
                    import json
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    
                    # Check if this tranche belongs to the imprint
                    if config.get('imprint') == imprint:
                        tranche_name = config_file.stem
                        tranches.append(tranche_name)
                        
                except Exception as e:
                    logger.warning(f"Error reading tranche config {config_file}: {e}")
                    continue
            
            return sorted(tranches)
            
        except Exception as e:
            logger.error(f"Error scanning tranches for imprint {imprint}: {e}")
            return []