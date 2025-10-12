"""
StateManager - Provides atomic session state management and consistency guarantees
"""

import streamlit as st
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from copy import deepcopy

logger = logging.getLogger(__name__)

class StateManager:
    """Provides atomic session state management and consistency guarantees"""
    
    def __init__(self):
        self.consistency_check_interval = 5.0  # Check consistency every 5 seconds
        
        # Initialize session state if needed
        if 'state_manager_state' not in st.session_state:
            st.session_state.state_manager_state = {
                'last_consistency_check': 0.0,
                'update_count': 0,
                'error_count': 0,
                'backup_states': []
            }
    
    def atomic_update(self, updates: Dict[str, Any], target_state: str = 'config_ui_state') -> bool:
        """
        Update multiple session state values atomically
        
        Args:
            updates: Dictionary of key-value pairs to update
            target_state: Target session state key to update
            
        Returns:
            bool: True if update was successful
        """
        if not updates:
            return True
        
        state_manager = st.session_state.state_manager_state
        
        try:
            # Ensure target state exists
            if target_state not in st.session_state:
                st.session_state[target_state] = {}
            
            target = st.session_state[target_state]
            
            # Create backup before update
            backup = deepcopy(target)
            
            # Apply all updates atomically
            for key, value in updates.items():
                target[key] = value
            
            # Store backup for potential rollback
            state_manager['backup_states'].append({
                'timestamp': time.time(),
                'target_state': target_state,
                'backup': backup
            })
            
            # Limit backup history
            if len(state_manager['backup_states']) > 5:
                state_manager['backup_states'].pop(0)
            
            state_manager['update_count'] += 1
            
            logger.debug(f"Atomic update applied to {target_state}: {list(updates.keys())}")
            return True
            
        except Exception as e:
            logger.error(f"Atomic update failed for {target_state}: {e}")
            state_manager['error_count'] += 1
            return False
    
    def preserve_valid_selections(self, old_state: Dict[str, Any], new_state: Dict[str, Any], 
                                 dependencies: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Preserve valid selections when state changes
        
        Args:
            old_state: Previous state
            new_state: New state
            dependencies: Dictionary mapping parent fields to dependent fields
            
        Returns:
            Updated new_state with preserved valid selections
        """
        try:
            preserved_state = deepcopy(new_state)
            
            for parent_field, dependent_fields in dependencies.items():
                old_parent_value = old_state.get(parent_field)
                new_parent_value = new_state.get(parent_field)
                
                # If parent field hasn't changed, preserve dependent selections
                if old_parent_value == new_parent_value:
                    for dependent_field in dependent_fields:
                        if dependent_field in old_state:
                            preserved_state[dependent_field] = old_state[dependent_field]
                            logger.debug(f"Preserved {dependent_field}: {old_state[dependent_field]}")
                
                # If parent field changed, validate dependent selections
                elif new_parent_value:
                    for dependent_field in dependent_fields:
                        old_dependent_value = old_state.get(dependent_field)
                        if old_dependent_value and self._is_selection_valid(
                            new_parent_value, old_dependent_value, parent_field, dependent_field):
                            preserved_state[dependent_field] = old_dependent_value
                            logger.debug(f"Preserved valid {dependent_field}: {old_dependent_value}")
                        else:
                            preserved_state[dependent_field] = ''
                            logger.debug(f"Cleared invalid {dependent_field}")
            
            return preserved_state
            
        except Exception as e:
            logger.error(f"Error preserving selections: {e}")
            return new_state
    
    def ensure_consistency(self, target_state: str = 'config_ui_state') -> bool:
        """
        Validate and correct session state inconsistencies
        
        Args:
            target_state: Target session state key to check
            
        Returns:
            bool: True if state is consistent or was corrected
        """
        current_time = time.time()
        state_manager = st.session_state.state_manager_state
        
        # Check if we need to run consistency check
        if (current_time - state_manager['last_consistency_check'] < 
            self.consistency_check_interval):
            return True
        
        state_manager['last_consistency_check'] = current_time
        
        try:
            if target_state not in st.session_state:
                logger.warning(f"Target state {target_state} not found, initializing")
                st.session_state[target_state] = {}
                return True
            
            state = st.session_state[target_state]
            corrections_made = False
            
            # Check required fields exist
            required_fields = {
                'selected_publisher': '',
                'selected_imprint': '',
                'selected_tranche': '',
                'display_mode': 'simple',
                'current_config': {},
                'validation_results': None,
                'expanded_groups': set()
            }
            
            for field, default_value in required_fields.items():
                if field not in state:
                    state[field] = default_value
                    corrections_made = True
                    logger.debug(f"Added missing field {field} with default value")
            
            # Validate field types
            type_checks = {
                'selected_publisher': str,
                'selected_imprint': str,
                'selected_tranche': str,
                'display_mode': str,
                'current_config': dict,
                'expanded_groups': set
            }
            
            for field, expected_type in type_checks.items():
                if field in state and not isinstance(state[field], expected_type):
                    if expected_type == set and isinstance(state[field], (list, tuple)):
                        state[field] = set(state[field])
                    else:
                        state[field] = expected_type()
                    corrections_made = True
                    logger.debug(f"Corrected type for field {field}")
            
            # Validate selection consistency
            publisher = state.get('selected_publisher', '')
            imprint = state.get('selected_imprint', '')
            tranche = state.get('selected_tranche', '')
            
            # Check if imprint is valid for publisher
            if publisher and imprint:
                if not self._is_selection_valid(publisher, imprint, 'publisher', 'imprint'):
                    state['selected_imprint'] = ''
                    state['selected_tranche'] = ''
                    corrections_made = True
                    logger.debug(f"Cleared invalid imprint {imprint} for publisher {publisher}")
            
            # Check if tranche is valid for imprint
            if imprint and tranche:
                if not self._is_selection_valid(imprint, tranche, 'imprint', 'tranche'):
                    state['selected_tranche'] = ''
                    corrections_made = True
                    logger.debug(f"Cleared invalid tranche {tranche} for imprint {imprint}")
            
            if corrections_made:
                logger.info(f"Made consistency corrections to {target_state}")
            
            return True
            
        except Exception as e:
            logger.error(f"Consistency check failed for {target_state}: {e}")
            state_manager['error_count'] += 1
            return False
    
    def rollback_last_update(self, target_state: str = 'config_ui_state') -> bool:
        """
        Rollback the last update to target state
        
        Args:
            target_state: Target session state key to rollback
            
        Returns:
            bool: True if rollback was successful
        """
        state_manager = st.session_state.state_manager_state
        
        try:
            # Find the most recent backup for this target state
            backup_entry = None
            for i in range(len(state_manager['backup_states']) - 1, -1, -1):
                entry = state_manager['backup_states'][i]
                if entry['target_state'] == target_state:
                    backup_entry = entry
                    break
            
            if not backup_entry:
                logger.warning(f"No backup found for {target_state}")
                return False
            
            # Restore the backup
            st.session_state[target_state] = deepcopy(backup_entry['backup'])
            
            # Remove the backup entry
            state_manager['backup_states'].remove(backup_entry)
            
            logger.info(f"Rolled back {target_state} to previous state")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed for {target_state}: {e}")
            return False
    
    def get_state_info(self, target_state: str = 'config_ui_state') -> Dict[str, Any]:
        """
        Get information about the current state
        
        Args:
            target_state: Target session state key
            
        Returns:
            Dictionary with state information
        """
        state_manager = st.session_state.state_manager_state
        
        info = {
            'update_count': state_manager['update_count'],
            'error_count': state_manager['error_count'],
            'backup_count': len(state_manager['backup_states']),
            'last_consistency_check': state_manager['last_consistency_check'],
            'state_exists': target_state in st.session_state
        }
        
        if target_state in st.session_state:
            state = st.session_state[target_state]
            info.update({
                'field_count': len(state) if isinstance(state, dict) else 0,
                'state_type': type(state).__name__
            })
        
        return info
    
    def clear_backups(self):
        """Clear all backup states"""
        state_manager = st.session_state.state_manager_state
        state_manager['backup_states'].clear()
        logger.info("Cleared all backup states")
    
    def _is_selection_valid(self, parent_value: str, dependent_value: str, 
                           parent_type: str, dependent_type: str) -> bool:
        """
        Check if a dependent selection is valid for a parent selection
        
        Args:
            parent_value: Value of the parent field
            dependent_value: Value of the dependent field
            parent_type: Type of parent field ('publisher', 'imprint')
            dependent_type: Type of dependent field ('imprint', 'tranche')
            
        Returns:
            bool: True if the selection is valid
        """
        try:
            if parent_type == 'publisher' and dependent_type == 'imprint':
                # Check if imprint belongs to publisher
                from .dropdown_manager import DropdownManager
                dropdown_manager = DropdownManager()
                valid_imprints = dropdown_manager.get_imprints_for_publisher(parent_value)
                return dependent_value in valid_imprints
            
            elif parent_type == 'imprint' and dependent_type == 'tranche':
                # Check if tranche belongs to imprint
                from .dropdown_manager import DropdownManager
                dropdown_manager = DropdownManager()
                valid_tranches = dropdown_manager.get_tranches_for_imprint(parent_value)
                return dependent_value in valid_tranches
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating selection {parent_value}->{dependent_value}: {e}")
            return False