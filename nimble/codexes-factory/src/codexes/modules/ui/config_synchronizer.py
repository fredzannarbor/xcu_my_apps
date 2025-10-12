"""
Configuration Synchronizer - Manages synchronization between configuration selection and core settings
"""

import streamlit as st
import time
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ConfigSyncState:
    """State tracking for configuration synchronization"""
    publisher: str
    imprint: str
    tranche: str
    user_overrides: Dict[str, Any]
    last_sync_timestamp: float
    sync_status: Dict[str, str]  # field_name -> 'config' | 'user' | 'mixed'

@dataclass
class SyncStatus:
    """Status of field synchronization"""
    field_name: str
    source: str  # 'configuration' | 'user_input' | 'default'
    value: Any
    is_overridden: bool
    config_value: Any
    user_value: Any

class ConfigurationSynchronizer:
    """Manages synchronization between configuration selection and core settings"""
    
    def __init__(self):
        self.session_key = 'config_sync_state'
        self.debounce_delay = 0.1  # 100ms debounce for rapid changes
        
        # Initialize session state if needed
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = ConfigSyncState(
                publisher='',
                imprint='',
                tranche='',
                user_overrides={},
                last_sync_timestamp=0.0,
                sync_status={}
            )
    
    def sync_config_to_form(self, publisher: str, imprint: str, tranche: str) -> Dict[str, Any]:
        """Synchronize configuration selection to form defaults"""
        try:
            current_time = time.time()
            sync_state = st.session_state[self.session_key]
            
            # Check if values have actually changed to avoid unnecessary updates
            config_changed = (
                sync_state.publisher != publisher or
                sync_state.imprint != imprint or
                sync_state.tranche != tranche
            )
            
            if not config_changed and current_time - sync_state.last_sync_timestamp < self.debounce_delay:
                # Return existing form data if no changes and within debounce period
                return self._get_current_form_data()
            
            # Update sync state
            sync_state.publisher = publisher
            sync_state.imprint = imprint
            sync_state.tranche = tranche
            sync_state.last_sync_timestamp = current_time
            
            # Build form data with configuration defaults
            form_data = {
                'publisher': publisher,
                'imprint': imprint,
                'tranche': tranche
            }
            
            # Apply user overrides if they exist
            for field, override_value in sync_state.user_overrides.items():
                if override_value is not None:
                    form_data[field] = override_value
            
            # Update sync status
            sync_state.sync_status = self._calculate_sync_status(form_data, {
                'publisher': publisher,
                'imprint': imprint,
                'tranche': tranche
            })
            
            logger.debug(f"Configuration synchronized: {publisher} -> {imprint} -> {tranche}")
            return form_data
            
        except Exception as e:
            logger.error(f"Configuration sync failed: {e}")
            return self._get_safe_defaults(publisher, imprint, tranche)
    
    def track_user_override(self, field_name: str, value: Any) -> None:
        """Track when user manually overrides a configuration-derived value"""
        try:
            sync_state = st.session_state[self.session_key]
            
            # Get the current configuration value for this field
            config_value = getattr(sync_state, field_name, None)
            
            # Only track as override if different from configuration value
            if value != config_value:
                sync_state.user_overrides[field_name] = value
                logger.debug(f"User override tracked for {field_name}: {value}")
            else:
                # Remove override if user set it back to config value
                sync_state.user_overrides.pop(field_name, None)
                logger.debug(f"User override removed for {field_name}")
            
            # Update sync status
            sync_state.sync_status[field_name] = 'user' if value != config_value else 'config'
            
        except Exception as e:
            logger.error(f"Error tracking user override for {field_name}: {e}")
    
    def get_effective_value(self, field_name: str, form_value: Any, config_value: Any) -> Any:
        """Get the effective value considering overrides and configuration"""
        try:
            sync_state = st.session_state[self.session_key]
            
            # Check if user has overridden this field
            if field_name in sync_state.user_overrides:
                override_value = sync_state.user_overrides[field_name]
                if override_value is not None:
                    return override_value
            
            # Use form value if provided, otherwise use config value
            return form_value if form_value else config_value
            
        except Exception as e:
            logger.error(f"Error getting effective value for {field_name}: {e}")
            return form_value or config_value or ''
    
    def get_sync_status(self) -> Dict[str, SyncStatus]:
        """Get synchronization status for UI indicators"""
        try:
            sync_state = st.session_state[self.session_key]
            status_dict = {}
            
            # Create status objects for tracked fields
            for field_name in ['publisher', 'imprint', 'tranche']:
                config_value = getattr(sync_state, field_name, '')
                user_value = sync_state.user_overrides.get(field_name)
                
                # Determine effective value and source
                if user_value is not None:
                    effective_value = user_value
                    source = 'user_input'
                    is_overridden = True
                elif config_value:
                    effective_value = config_value
                    source = 'configuration'
                    is_overridden = False
                else:
                    effective_value = ''
                    source = 'default'
                    is_overridden = False
                
                status_dict[field_name] = SyncStatus(
                    field_name=field_name,
                    source=source,
                    value=effective_value,
                    is_overridden=is_overridden,
                    config_value=config_value,
                    user_value=user_value
                )
            
            return status_dict
            
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {}
    
    def clear_user_overrides(self, field_names: Optional[list] = None) -> None:
        """Clear user overrides for specified fields or all fields"""
        try:
            sync_state = st.session_state[self.session_key]
            
            if field_names is None:
                # Clear all overrides
                sync_state.user_overrides.clear()
                logger.debug("All user overrides cleared")
            else:
                # Clear specific field overrides
                for field_name in field_names:
                    sync_state.user_overrides.pop(field_name, None)
                logger.debug(f"User overrides cleared for fields: {field_names}")
            
            # Update sync status
            sync_state.sync_status = self._calculate_sync_status(
                self._get_current_form_data(),
                {
                    'publisher': sync_state.publisher,
                    'imprint': sync_state.imprint,
                    'tranche': sync_state.tranche
                }
            )
            
        except Exception as e:
            logger.error(f"Error clearing user overrides: {e}")
    
    def is_field_synchronized(self, field_name: str) -> bool:
        """Check if a field is currently synchronized with configuration"""
        try:
            sync_state = st.session_state[self.session_key]
            return field_name not in sync_state.user_overrides
        except Exception as e:
            logger.error(f"Error checking field synchronization for {field_name}: {e}")
            return False
    
    def get_configuration_values(self) -> Dict[str, str]:
        """Get current configuration values"""
        try:
            sync_state = st.session_state[self.session_key]
            return {
                'publisher': sync_state.publisher,
                'imprint': sync_state.imprint,
                'tranche': sync_state.tranche
            }
        except Exception as e:
            logger.error(f"Error getting configuration values: {e}")
            return {'publisher': '', 'imprint': '', 'tranche': ''}
    
    def _get_current_form_data(self) -> Dict[str, Any]:
        """Get current form data from session state"""
        try:
            sync_state = st.session_state[self.session_key]
            form_data = {
                'publisher': sync_state.publisher,
                'imprint': sync_state.imprint,
                'tranche': sync_state.tranche
            }
            
            # Apply user overrides
            for field, override_value in sync_state.user_overrides.items():
                if override_value is not None:
                    form_data[field] = override_value
            
            return form_data
        except Exception as e:
            logger.error(f"Error getting current form data: {e}")
            return {}
    
    def _get_safe_defaults(self, publisher: str, imprint: str, tranche: str) -> Dict[str, Any]:
        """Get safe default values when sync fails"""
        return {
            'publisher': publisher or '',
            'imprint': imprint or '',
            'tranche': tranche or ''
        }
    
    def _calculate_sync_status(self, form_data: Dict[str, Any], config_data: Dict[str, Any]) -> Dict[str, str]:
        """Calculate synchronization status for each field"""
        status = {}
        
        for field_name in ['publisher', 'imprint', 'tranche']:
            form_value = form_data.get(field_name, '')
            config_value = config_data.get(field_name, '')
            
            if form_value == config_value:
                status[field_name] = 'config'
            elif form_value and form_value != config_value:
                status[field_name] = 'user'
            else:
                status[field_name] = 'default'
        
        return status

class ConfigSyncError(Exception):
    """Base exception for configuration synchronization errors"""
    pass