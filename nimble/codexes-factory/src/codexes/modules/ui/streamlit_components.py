"""
Enhanced Streamlit UI Components for Configuration Management
"""

import streamlit as st
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from .parameter_groups import ParameterGroupManager, ParameterType, ConfigurationParameter, ParameterGroup
from .configuration_manager import EnhancedConfigurationManager, ValidationResult
from .config_validator import ConfigurationValidator
from .dynamic_config_loader import DynamicConfigurationLoader
from .safety_patterns import (
    safe_getattr, safe_dict_get, safe_iteration, safe_len, safe_join,
    safe_string_format, validate_not_none, log_none_encounter
)
from .data_validators import UIDataValidator, StructureNormalizer


class ConfigurationUI:
    """Streamlit components for configuration management with complete parameter inspection"""
    
    def __init__(self):
        self.config_manager = EnhancedConfigurationManager()
        self.validator = ConfigurationValidator()
        self.param_manager = ParameterGroupManager()
        self.config_loader = DynamicConfigurationLoader()
        
        # Initialize safety components
        self.ui_validator = UIDataValidator()
        self.structure_normalizer = StructureNormalizer(self.ui_validator)
        
        # Configuration cache for performance
        self._config_cache = {}
        self._cache_max_size = 10  # Limit cache size
        
        # Initialize new managers for controlled state management
        try:
            from .dropdown_manager import DropdownManager
            from .validation_manager import ValidationManager
            from .state_manager import StateManager
            
            self.dropdown_manager = DropdownManager()
            self.validation_manager = ValidationManager()
            self.state_manager = StateManager()
        except ImportError as e:
            # Safe logging without crashing
            if hasattr(st, 'logger'):
                st.logger.warning(f"Could not import new managers: {e}")
            self.dropdown_manager = None
            self.validation_manager = None
            self.state_manager = None
        
        # Initialize session state with enhanced structure and safety patterns
        if 'config_ui_state' not in st.session_state:
            st.session_state.config_ui_state = {
                # Selection state - all initialized with safe defaults
                'display_mode': 'simple',
                'selected_publisher': '',
                'selected_imprint': '',
                'selected_tranche': '',
                'current_config': {},
                'validation_results': None,
                'expanded_groups': set(),
                
                # Loading state - all initialized with safe defaults
                'loading_state': False,
                'last_load_time': 0.0,
                'auto_load_enabled': True,
                
                # Control flags - all initialized with safe defaults
                'dropdown_update_pending': False,
                'validation_in_progress': False,
                'last_update_timestamp': 0.0,
                'update_debounce_key': '',
                
                # Cache - all initialized with safe defaults
                'publisher_imprints_cache': {},
                'imprint_tranches_cache': {},
                'last_cache_update': 0.0
            }
        
        # Ensure all required keys exist with safe defaults (autofix-resistant pattern)
        default_state = {
            'display_mode': 'simple',
            'selected_publisher': '',
            'selected_imprint': '',
            'selected_tranche': '',
            'current_config': {},
            'validation_results': None,
            'expanded_groups': set(),
            'loading_state': False,
            'last_load_time': 0.0,
            'auto_load_enabled': True,
            'dropdown_update_pending': False,
            'validation_in_progress': False,
            'last_update_timestamp': 0.0,
            'update_debounce_key': '',
            'publisher_imprints_cache': {},
            'imprint_tranches_cache': {},
            'last_cache_update': 0.0
        }
        
        # Safe state initialization - ensure no None values
        for key, default_value in default_state.items():
            if key not in st.session_state.config_ui_state or st.session_state.config_ui_state[key] is None:
                st.session_state.config_ui_state[key] = default_value
    
    def render_configuration_selector(self) -> Tuple[str, str, str]:
        """Render configuration selection dropdowns with button-based refresh"""
        st.subheader("📋 Configuration Selection")
        st.caption("Select your publisher, imprint, and tranche to load configuration defaults. This determines which configuration files are used for the pipeline.")
        
        # Import managers
        from .dropdown_manager import DropdownManager
        from .state_manager import StateManager
        
        dropdown_manager = DropdownManager()
        state_manager = StateManager()
        
        # Ensure state consistency
        state_manager.ensure_consistency()
        
        # Configuration selector without nested form
        col1, col2, col3, col4 = st.columns([3, 3, 3, 1])
        
        with col1:
            # Publisher selection with safe access patterns
            publishers = ['']
            try:
                scanned_publishers = self.config_loader.scan_publishers()
                publishers.extend(scanned_publishers or [])  # Safe extension
            except Exception as e:
                log_none_encounter('publisher_scan', 'scan_publishers')
                # Continue with empty list - graceful degradation
            
            # Safe access to session state with fallback
            current_publisher = safe_dict_get(
                st.session_state.config_ui_state, 
                'selected_publisher', 
                ''
            )
            
            # Safe index calculation
            publisher_index = 0
            if current_publisher and current_publisher in publishers:
                publisher_index = publishers.index(current_publisher)
            
            selected_publisher = st.selectbox(
                "Publisher",
                options=publishers,
                index=publisher_index,
                help="Select the publishing company (e.g., nimble_books)",
                key="publisher_selector"
            )
            
        with col2:
            # Imprint selection (filtered by publisher) with safe access patterns
            imprints = ['']
            if selected_publisher:
                try:
                    publisher_imprints = dropdown_manager.get_imprints_for_publisher(selected_publisher) if dropdown_manager else []
                    imprints.extend(publisher_imprints or [])  # Safe extension
                except Exception as e:
                    log_none_encounter('imprint_scan', f'get_imprints_for_publisher({selected_publisher})')
                    # Continue with empty list - graceful degradation
            
            # Safe access to current imprint with validation
            current_imprint = safe_dict_get(
                st.session_state.config_ui_state, 
                'selected_imprint', 
                ''
            )
            
            # Reset if not valid for selected publisher (safe check)
            if current_imprint not in imprints:
                current_imprint = ''
            
            # Safe index calculation
            imprint_index = 0
            if current_imprint and current_imprint in imprints:
                imprint_index = imprints.index(current_imprint)
            
            # Safe key generation
            safe_publisher = selected_publisher or 'none'
            safe_imprint_count = safe_len(imprints)
            
            selected_imprint = st.selectbox(
                "Imprint",
                options=imprints,
                index=imprint_index,
                help="Select the publishing imprint or brand (e.g., xynapse_traces)",
                key=f"imprint_selector_{safe_publisher}_{safe_imprint_count}"  # Dynamic key for refresh
            )
            
        with col3:
            # Tranche selection (filtered by imprint) with safe access patterns
            tranches = ['']
            if selected_imprint:
                try:
                    imprint_tranches = dropdown_manager.get_tranches_for_imprint(selected_imprint) if dropdown_manager else []
                    tranches.extend(imprint_tranches or [])  # Safe extension
                except Exception as e:
                    log_none_encounter('tranche_scan', f'get_tranches_for_imprint({selected_imprint})')
                    # Continue with empty list - graceful degradation
            
            # Safe access to current tranche with validation
            current_tranche = safe_dict_get(
                st.session_state.config_ui_state, 
                'selected_tranche', 
                ''
            )
            
            # Reset if not valid for selected imprint (safe check)
            if current_tranche not in tranches:
                current_tranche = ''
            
            # Safe index calculation
            tranche_index = 0
            if current_tranche and current_tranche in tranches:
                tranche_index = tranches.index(current_tranche)
            
            # Safe key generation
            safe_imprint = selected_imprint or 'none'
            safe_tranche_count = safe_len(tranches)
            
            selected_tranche = st.selectbox(
                "Tranche",
                options=tranches,
                index=tranche_index,
                help="Select the batch or tranche configuration (optional)",
                key=f"tranche_selector_{safe_imprint}_{safe_tranche_count}"  # Dynamic key for refresh
            )
        
        with col4:
            st.write("")  # Spacing
            refresh_config = st.button("🔄 Refresh", help="Click to refresh dropdown options when publisher changes")
        
        # Show helpful information about the selections with safe string operations
        if selected_publisher:
            imprint_count = safe_len(imprints)
            if imprint_count <= 1:  # Only empty option
                safe_publisher_name = selected_publisher or 'unknown'
                st.info(f"ℹ️ No imprints found for publisher '{safe_publisher_name}'. Check that imprint config files exist in `configs/imprints/` with `publisher: {safe_publisher_name}`")
            elif selected_imprint:
                # Safe string formatting for success message
                config_path = safe_join([selected_publisher, selected_imprint], ' → ')
                if selected_tranche:
                    config_path = safe_join([config_path, selected_tranche], ' → ')
                st.success(f"✅ Configuration loaded: {config_path}")
        
        # Handle refresh button or detect changes with safe access patterns
        current_state = st.session_state.config_ui_state or {}  # Safe access
        
        # Safe comparison with fallback to empty string
        current_publisher = safe_dict_get(current_state, 'selected_publisher', '')
        current_imprint = safe_dict_get(current_state, 'selected_imprint', '')
        current_tranche = safe_dict_get(current_state, 'selected_tranche', '')
        
        publisher_changed = current_publisher != (selected_publisher or '')
        imprint_changed = current_imprint != (selected_imprint or '')
        tranche_changed = current_tranche != (selected_tranche or '')
        
        # If refresh was clicked or selections changed, update and potentially rerun
        if refresh_config or publisher_changed or imprint_changed or tranche_changed:
            # Safe state updates with None protection
            updates = {
                'selected_publisher': selected_publisher or '',
                'selected_imprint': selected_imprint or '',
                'selected_tranche': selected_tranche or ''
            }
            
            # Update session state atomically with safety
            if self.state_manager:
                try:
                    self.state_manager.atomic_update(updates)
                except Exception as e:
                    log_none_encounter('state_manager', 'atomic_update')
                    # Fallback to direct update
                    if st.session_state.config_ui_state is not None:
                        st.session_state.config_ui_state.update(updates)
            else:
                # Safe fallback to direct update
                if st.session_state.config_ui_state is not None:
                    st.session_state.config_ui_state.update(updates)
                else:
                    st.session_state.config_ui_state = updates
            
            # If publisher changed or refresh was clicked, force a rerun to refresh dependent dropdowns
            if publisher_changed or refresh_config:
                st.rerun()
        
        # Check if selections have changed and trigger automatic loading
        if self._has_selection_changed(selected_publisher, selected_imprint, selected_tranche):
            # Use StateManager for atomic updates
            if self.state_manager:
                updates = {
                    'selected_publisher': selected_publisher,
                    'selected_imprint': selected_imprint,
                    'selected_tranche': selected_tranche
                }
                self.state_manager.atomic_update(updates)
            else:
                # Fallback to direct update
                st.session_state.config_ui_state.update({
                    'selected_publisher': selected_publisher,
                    'selected_imprint': selected_imprint,
                    'selected_tranche': selected_tranche
                })
            
            # Automatically load configuration if any selection is made
            if selected_publisher or selected_imprint or selected_tranche:
                # Preserve existing configuration before loading new one
                existing_config = st.session_state.config_ui_state.get('current_config', {}).copy()
                
                # Load new configuration
                if self._load_configuration(selected_publisher, selected_imprint, selected_tranche):
                    # Merge with preserved values where appropriate
                    self._preserve_manual_overrides(existing_config)
        else:
            # Update session state even if no change (for consistency)
            if self.state_manager:
                updates = {
                    'selected_publisher': selected_publisher,
                    'selected_imprint': selected_imprint,
                    'selected_tranche': selected_tranche
                }
                self.state_manager.atomic_update(updates)
            else:
                # Fallback to direct update
                st.session_state.config_ui_state.update({
                    'selected_publisher': selected_publisher,
                    'selected_imprint': selected_imprint,
                    'selected_tranche': selected_tranche
                })
        
        # Show configuration inheritance if any configs are selected
        if selected_publisher or selected_imprint or selected_tranche:
            self._render_configuration_inheritance(selected_publisher, selected_imprint, selected_tranche)
        
        # Show validation status if configuration is loaded
        self._render_validation_status()
        
        return selected_publisher, selected_imprint, selected_tranche
    
    def _has_selection_changed(self, publisher: str, imprint: str, tranche: str) -> bool:
        """Check if current selections differ from session state"""
        current_state = st.session_state.config_ui_state
        return (
            current_state['selected_publisher'] != publisher or
            current_state['selected_imprint'] != imprint or
            current_state['selected_tranche'] != tranche
        )
    
    def _show_loading_feedback(self, loading: bool, message: str = "") -> None:
        """Show loading indicators and status messages"""
        if loading:
            with st.spinner(message or "Loading configuration..."):
                pass
        elif message:
            st.info(message)
    
    def _preserve_manual_overrides(self, previous_config: Dict[str, Any]) -> None:
        """Preserve manual parameter overrides when loading new configuration"""
        if not previous_config:
            return
        
        current_config = st.session_state.config_ui_state.get('current_config', {})
        
        # List of parameters that should be preserved if manually set
        preserve_params = [
            'max_books', 'begin_with_book', 'end_with_book', 'quotes_per_book',
            'model', 'verifier_model', 'start_stage', 'end_stage',
            'verbose', 'terse_log', 'debug_cover'
        ]
        
        preserved_count = 0
        for param in preserve_params:
            if param in previous_config and previous_config[param] != current_config.get(param):
                # Check if the previous value was likely manually set (not default)
                param_def = self.param_manager.get_parameter_by_name(param)
                if param_def and previous_config[param] != param_def.default_value:
                    current_config[param] = previous_config[param]
                    preserved_count += 1
        
        if preserved_count > 0:
            st.session_state.config_ui_state['current_config'] = current_config
            st.info(f"🔄 Preserved {preserved_count} manual parameter override(s)")
    
    def _render_validation_status(self) -> None:
        """Render real-time validation status with safe access patterns"""
        # Safe access to session state
        config_ui_state = st.session_state.config_ui_state or {}
        validation_results = safe_dict_get(config_ui_state, 'validation_results', None)
        current_config = safe_dict_get(config_ui_state, 'current_config', {})
        
        # Validate inputs before proceeding
        if not validate_not_none(validation_results, 'validation_status', 'validation_results'):
            return
        if not current_config:
            return
        
        # Show compact validation status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Safe access to validation result attributes
            is_valid = safe_getattr(validation_results, 'is_valid', False)
            if is_valid:
                st.success("✅ Configuration Valid")
            else:
                # Safe access to errors list
                errors = safe_getattr(validation_results, 'errors', [])
                error_count = safe_len(errors)
                st.error(f"❌ {error_count} Error(s)")
        
        with col2:
            # Safe access to warnings list
            warnings = safe_getattr(validation_results, 'warnings', [])
            warning_count = safe_len(warnings)
            if warning_count > 0:
                st.warning(f"⚠️ {warning_count} Warning(s)")
            else:
                st.info("ℹ️ No Warnings")
        
        with col3:
            # Safe parameter counting with None value filtering
            param_count = 0
            try:
                param_count = len([v for v in (current_config or {}).values() 
                                 if v not in [None, "", [], {}]])
            except (TypeError, AttributeError):
                param_count = 0
            st.metric("Parameters", param_count)
    
    def _manage_cache_size(self) -> None:
        """Manage configuration cache size to prevent memory issues"""
        if len(self._config_cache) > self._cache_max_size:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self._config_cache.keys())[:-self._cache_max_size]
            for key in keys_to_remove:
                del self._config_cache[key]
    
    def _load_configuration(self, publisher: str, imprint: str, tranche: str) -> bool:
        """Load and merge configurations with enhanced feedback and safety patterns"""
        try:
            # Safe access to session state for debouncing
            config_ui_state = st.session_state.config_ui_state or {}
            current_time = time.time()
            last_load_time = safe_dict_get(config_ui_state, 'last_load_time', 0.0)
            
            # Safe string formatting for config key
            safe_publisher = publisher or ''
            safe_imprint = imprint or ''
            safe_tranche = tranche or ''
            config_key = f"{safe_publisher}|{safe_imprint}|{safe_tranche}"
            
            last_config_key = safe_dict_get(config_ui_state, 'last_config_key', '')
            
            # Skip loading if same configuration was loaded within last 2 seconds
            if (current_time - last_load_time < 2.0 and config_key == last_config_key):
                return True
            
            # Safe state updates
            if st.session_state.config_ui_state is not None:
                st.session_state.config_ui_state['loading_state'] = True
                st.session_state.config_ui_state['last_load_time'] = current_time
                st.session_state.config_ui_state['last_config_key'] = config_key
            
            # Build configuration description with safe string operations
            config_parts = []
            if safe_publisher:
                config_parts.append(f"Publisher: {safe_publisher}")
            if safe_imprint:
                config_parts.append(f"Imprint: {safe_imprint}")
            if safe_tranche:
                config_parts.append(f"Tranche: {safe_tranche}")
            
            config_description = safe_join(config_parts, " → ") or "Default configuration"
            
            # Check cache first with safe access
            cache_key = config_key  # Already safely formatted above
            cached_config = safe_dict_get(self._config_cache, cache_key, None)
            
            if cached_config is not None:
                merged_config = cached_config
            else:
                # Load and merge configurations with error handling
                try:
                    merged_config = self.config_manager.merge_configurations(
                        safe_publisher, safe_imprint, safe_tranche
                    )
                    # Validate merged config is not None
                    if merged_config is None:
                        merged_config = {}
                        log_none_encounter('config_loading', 'merge_configurations')
                except Exception as e:
                    log_none_encounter('config_loading', f'merge_configurations_error: {e}')
                    merged_config = {}
                
                # Safe cache operations
                if self._config_cache is not None:
                    self._config_cache[cache_key] = merged_config
                    self._manage_cache_size()
            
            # Safe state update
            if st.session_state.config_ui_state is not None:
                st.session_state.config_ui_state['current_config'] = merged_config or {}
            
            # Validate the merged configuration with safe access
            validation_results = None
            try:
                validation_results = self.validator.validate_configuration(merged_config or {})
            except Exception as e:
                log_none_encounter('config_validation', f'validate_configuration_error: {e}')
                # Create a basic validation result for graceful degradation
                validation_results = type('ValidationResult', (), {
                    'is_valid': False,
                    'errors': [f"Validation error: {e}"],
                    'warnings': []
                })()
            
            # Safe state update for validation results
            if st.session_state.config_ui_state is not None:
                st.session_state.config_ui_state['validation_results'] = validation_results
            
            # Show success feedback with safe parameter counting
            param_count = 0
            try:
                param_count = len([v for v in (merged_config or {}).values() 
                                 if v not in [None, "", [], {}]])
            except (TypeError, AttributeError):
                param_count = 0
            
            st.success(f"✅ Loaded {config_description} ({param_count} parameters configured)")
            
            # Show validation status with safe access
            if validation_results:
                is_valid = safe_getattr(validation_results, 'is_valid', False)
                if is_valid:
                    st.info("🔍 Configuration validated successfully")
                else:
                    errors = safe_getattr(validation_results, 'errors', [])
                    error_count = safe_len(errors)
                    st.warning(f"⚠️ Configuration has {error_count} validation issue(s)")
            
            # Clear loading state safely
            if st.session_state.config_ui_state is not None:
                st.session_state.config_ui_state['loading_state'] = False
            return True
            
        except FileNotFoundError as e:
            st.warning(f"⚠️ Configuration file not found: {e}. Using default values.")
            # Safe state cleanup
            if st.session_state.config_ui_state is not None:
                st.session_state.config_ui_state['loading_state'] = False
            return False
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid configuration file format: {e}")
            # Safe state cleanup
            if st.session_state.config_ui_state is not None:
                st.session_state.config_ui_state['loading_state'] = False
            return False
        except Exception as e:
            st.error(f"❌ Error loading configuration: {e}")
            # Safe state cleanup
            if st.session_state.config_ui_state is not None:
                st.session_state.config_ui_state['loading_state'] = False
            return False
    
    def _render_configuration_inheritance(self, publisher: str, imprint: str, tranche: str):
        """Show configuration inheritance chain"""
        with st.expander("Configuration Inheritance Chain", expanded=False):
            chain = self.config_manager.get_configuration_inheritance_chain(publisher, imprint, tranche)
            
            for i, level_info in enumerate(chain):
                level_name = level_info['name']
                level_config = level_info['config']
                
                st.write(f"**{i+1}. {level_name}**")
                
                if level_config:
                    # Show key configuration values
                    key_values = {}
                    for key in ['publisher', 'imprint', 'lightning_source_account', 'language_code']:
                        if key in level_config:
                            key_values[key] = level_config[key]
                    
                    if key_values:
                        st.json(key_values)
                else:
                    st.write("*No configuration found*")
                
                if i < len(chain) - 1:
                    st.write("⬇️")
    
    def render_display_mode_selector(self) -> str:
        """Render display mode selector"""
        col1, col2 = st.columns([2, 6])
        
        with col1:
            display_mode = st.selectbox(
                "Display Mode",
                options=['simple', 'advanced', 'expert'],
                index=['simple', 'advanced', 'expert'].index(st.session_state.config_ui_state['display_mode']),
                help="Choose parameter visibility level"
            )
            
        with col2:
            mode_descriptions = {
                'simple': "Basic settings for quick setup",
                'advanced': "Additional LSI and distribution parameters",
                'expert': "All parameters including debug and advanced features"
            }
            st.info(mode_descriptions[display_mode])
        
        st.session_state.config_ui_state['display_mode'] = display_mode
        return display_mode
    
    def render_parameter_group(self, group: ParameterGroup, display_mode: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render a parameter group with appropriate widgets"""
        group_data = {}
        
        # Check if group should be shown in current display mode
        if display_mode not in (group.display_modes or ['simple']):
            return group_data
        
        # Determine if group should be expanded
        is_expanded = (group.expanded_by_default or 
                      group.name in st.session_state.config_ui_state['expanded_groups'])
        
        with st.expander(f"{group.display_name}", expanded=is_expanded):
            if group.description:
                st.caption(group.description)
            
            # Track expansion state
            if is_expanded:
                st.session_state.config_ui_state['expanded_groups'].add(group.name)
            
            # Render parameters in columns for better layout
            if len(group.parameters) > 1:
                cols = st.columns(min(2, len(group.parameters)))
            else:
                cols = [st.container()]
            
            for i, param in enumerate(group.parameters):
                col = cols[i % len(cols)]
                
                with col:
                    param_value = self._render_parameter_widget(param, form_data)
                    if param_value is not None:
                        group_data[param.name] = param_value
        
        return group_data
    
    def _render_parameter_widget(self, param: ConfigurationParameter, form_data: Dict[str, Any]) -> Any:
        """Render appropriate widget for parameter type with synchronization indicators"""
        # Get current value from form data or default
        current_value = form_data.get(param.name, param.default_value)
        
        # Check if this field is synchronized with configuration
        sync_info = self._get_field_sync_info(param.name, current_value)
        
        # Create unique key for widget
        widget_key = f"param_{param.name}"
        
        try:
            if param.parameter_type == ParameterType.TEXT:
                # Enhanced help text with sync info
                enhanced_help = param.help_text
                enhanced_placeholder = param.placeholder
                
                if sync_info['is_synchronized']:
                    enhanced_help = f"{param.help_text}\n🔗 Auto-populated from configuration: {sync_info['config_value']}"
                    if not current_value:
                        enhanced_placeholder = f"From configuration: {sync_info['config_value']}"
                
                return st.text_input(
                    param.display_name,
                    value=str(current_value) if current_value is not None else "",
                    help=enhanced_help,
                    placeholder=enhanced_placeholder,
                    key=widget_key
                )
            
            elif param.parameter_type == ParameterType.NUMBER:
                # Ensure all numerical parameters are of the same type
                min_val = param.min_value
                max_val = param.max_value
                step_val = param.step or 1
                
                # Determine if we should use integers or floats based on step
                use_int = (isinstance(step_val, int) and step_val == int(step_val) and
                          (min_val is None or isinstance(min_val, int)) and
                          (max_val is None or isinstance(max_val, int)))
                
                if use_int:
                    # Use integer values
                    current_val = int(current_value) if current_value is not None else (min_val or 0)
                    return st.number_input(
                        param.display_name,
                        value=current_val,
                        min_value=min_val,
                        max_value=max_val,
                        step=step_val,
                        format="%d",
                        help=param.help_text,
                        key=widget_key
                    )
                else:
                    # Use float values
                    current_val = float(current_value) if current_value is not None else float(min_val or 0)
                    min_val = float(min_val) if min_val is not None else None
                    max_val = float(max_val) if max_val is not None else None
                    step_val = float(step_val)
                    return st.number_input(
                        param.display_name,
                        value=current_val,
                        min_value=min_val,
                        max_value=max_val,
                        step=step_val,
                        help=param.help_text,
                        key=widget_key
                    )
            
            elif param.parameter_type == ParameterType.SELECT:
                options = param.options or []
                if current_value not in options and current_value is not None:
                    options = [current_value] + options
                
                index = 0
                if current_value in options:
                    index = options.index(current_value)
                
                return st.selectbox(
                    param.display_name,
                    options=options,
                    index=index,
                    help=param.help_text,
                    key=widget_key
                )
            
            elif param.parameter_type == ParameterType.MULTISELECT:
                options = param.options or []
                default_selection = current_value if isinstance(current_value, list) else []
                
                return st.multiselect(
                    param.display_name,
                    options=options,
                    default=default_selection,
                    help=param.help_text,
                    key=widget_key
                )
            
            elif param.parameter_type == ParameterType.CHECKBOX:
                return st.checkbox(
                    param.display_name,
                    value=bool(current_value),
                    help=param.help_text,
                    key=widget_key
                )
            
            elif param.parameter_type == ParameterType.TEXTAREA:
                return st.text_area(
                    param.display_name,
                    value=str(current_value) if current_value is not None else "",
                    help=param.help_text,
                    key=widget_key
                )
            
            elif param.parameter_type == ParameterType.FILE:
                return st.file_uploader(
                    param.display_name,
                    help=param.help_text,
                    key=widget_key
                )
            
            elif param.parameter_type == ParameterType.JSON:
                json_str = json.dumps(current_value, indent=2) if current_value else "{}"
                return st.text_area(
                    param.display_name,
                    value=json_str,
                    help=param.help_text,
                    height=200,
                    key=widget_key
                )
            
            elif param.parameter_type == ParameterType.COLOR:
                return st.color_picker(
                    param.display_name,
                    value=str(current_value) if current_value else "#000000",
                    help=param.help_text,
                    key=widget_key
                )
            
            elif param.parameter_type == ParameterType.DATE:
                return st.date_input(
                    param.display_name,
                    help=param.help_text,
                    key=widget_key
                )
            
            else:
                # Fallback to text input
                return st.text_input(
                    param.display_name,
                    value=str(current_value) if current_value is not None else "",
                    help=param.help_text,
                    key=widget_key
                )
                
        except Exception as e:
            st.error(f"Error rendering parameter {param.name}: {e}")
            return current_value
    
    def render_complete_configuration_preview(self, config: Dict[str, Any]) -> None:
        """Render mandatory complete configuration preview before submission"""
        st.subheader("🔍 Complete Configuration Preview (MANDATORY)")
        st.info("Review all parameters before pipeline execution. This section shows exactly what will be passed to the pipeline.")
        
        # Configuration statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Parameters", len(config))
        
        with col2:
            non_empty_params = sum(1 for v in config.values() if v not in [None, "", [], {}])
            st.metric("Configured Parameters", non_empty_params)
        
        with col3:
            config_hash = hash(str(sorted(config.items())))
            st.metric("Configuration Hash", f"{config_hash:08x}")
        
        with col4:
            validation_results = st.session_state.config_ui_state.get('validation_results')
            if validation_results:
                status = "✅ Valid" if validation_results.is_valid else "❌ Invalid"
                st.metric("Validation Status", status)
        
        # Tabbed view of configuration
        tab1, tab2, tab3, tab4 = st.tabs(["Organized View", "JSON View", "Command Preview", "Validation"])
        
        with tab1:
            self._render_organized_config_view(config)
        
        with tab2:
            st.json(config)
        
        with tab3:
            self.render_command_line_preview(config)
        
        with tab4:
            self.render_validation_results(st.session_state.config_ui_state.get('validation_results'))
    
    def _render_organized_config_view(self, config: Dict[str, Any]):
        """Render configuration organized by parameter groups"""
        groups = self.param_manager.get_parameter_groups()
        
        for group_name, group in groups.items():
            group_params = {param.name: config.get(param.name) for param in group.parameters 
                          if param.name in config and config[param.name] not in [None, "", [], {}]}
            
            if group_params:
                st.write(f"**{group.display_name}**")
                
                # Create a clean display of parameters
                for param_name, param_value in group_params.items():
                    param_def = self.param_manager.get_parameter_by_name(param_name)
                    display_name = param_def.display_name if param_def else param_name
                    
                    # Format value for display
                    if isinstance(param_value, (dict, list)):
                        display_value = json.dumps(param_value, indent=2)
                        st.code(f"{display_name}: {display_value}", language="json")
                    else:
                        st.write(f"- **{display_name}**: {param_value}")
                
                st.write("")  # Add spacing
    
    def render_command_line_preview(self, config: Dict[str, Any]) -> None:
        """Render command-line preview showing exact parameters being passed"""
        st.write("**Command Line Preview**")
        st.caption("This shows the exact command that will be executed:")
        
        # Build command preview (simplified version)
        command_parts = ["python", "run_book_pipeline.py"]
        
        # Add key parameters
        key_params = [
            ('imprint', '--imprint'),
            ('schedule_file', '--schedule-file'),
            ('model', '--model'),
            ('verifier_model', '--verifier-model'),
            ('start_stage', '--start-stage'),
            ('end_stage', '--end-stage'),
            ('max_books', '--max-books'),
            ('tranche', '--tranche')
        ]
        
        for param_name, flag in key_params:
            value = config.get(param_name)
            if value not in [None, "", 0]:
                command_parts.extend([flag, str(value)])
        
        # Add boolean flags
        boolean_flags = [
            ('skip_lsi', '--skip-lsi'),
            ('enable_llm_completion', '--enable-llm-completion'),
            ('verbose', '--verbose'),
            ('terse_log', '--terse-log')
        ]
        
        for param_name, flag in boolean_flags:
            if config.get(param_name):
                command_parts.append(flag)
        
        # Display command
        command_str = " \\\n  ".join(command_parts)
        st.code(command_str, language="bash")
        
        # Show parameter count
        param_count = len([p for p in command_parts if p.startswith('--')])
        st.caption(f"Command includes {param_count} parameters")
    
    def render_validation_results(self, results: Optional[ValidationResult]) -> None:
        """Render validation results with status indicators"""
        if not results:
            st.info("No validation results available. Load a configuration to see validation status.")
            return
        
        # Safety check for results structure
        try:
            # Check if results has the expected attributes
            if not hasattr(results, 'is_valid'):
                st.warning("⚠️ Invalid validation results format")
                return
            
            # Overall status
            if results.is_valid:
                st.success("✅ Configuration is valid and ready for execution")
            else:
                error_count = len(results.errors) if hasattr(results, 'errors') and results.errors else 0
                st.error(f"❌ Configuration has {error_count} error(s) that must be fixed")
            
            # Errors
            if hasattr(results, 'errors') and results.errors:
                st.write("**Errors:**")
                for error in results.errors:
                    # Safety check for error object structure
                    if hasattr(error, 'field_name') and hasattr(error, 'error_message'):
                        st.error(f"**{error.field_name}**: {error.error_message}")
                        if hasattr(error, 'suggested_values') and error.suggested_values:
                            st.caption(f"Suggested values: {', '.join(error.suggested_values[:3])}")
                    elif isinstance(error, str):
                        # Handle case where error is just a string
                        st.error(f"**Error**: {error}")
                    else:
                        # Handle unexpected error format
                        st.error(f"**Error**: {str(error)}")
            
            # Warnings
            if hasattr(results, 'warnings') and results.warnings:
                st.write("**Warnings:**")
                for warning in results.warnings:
                    # Safety check for warning object structure
                    if hasattr(warning, 'field_name') and hasattr(warning, 'warning_message'):
                        st.warning(f"**{warning.field_name}**: {warning.warning_message}")
                    elif isinstance(warning, str):
                        # Handle case where warning is just a string
                        st.warning(f"**Warning**: {warning}")
                    else:
                        # Handle unexpected warning format
                        st.warning(f"**Warning**: {str(warning)}")
                        
        except Exception as e:
            st.error(f"❌ Error rendering validation results: {e}")
            st.info("This is likely due to a validation results format mismatch.")
        
        # Parameter status grid
        if results.parameter_status:
            st.write("**Parameter Status:**")
            
            # Group by status
            status_groups = {}
            for param, status in results.parameter_status.items():
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(param)
            
            # Display in columns
            cols = st.columns(3)
            
            if 'valid' in status_groups:
                with cols[0]:
                    st.success(f"✅ Valid ({len(status_groups['valid'])})")
                    for param in status_groups['valid'][:5]:  # Show first 5
                        st.write(f"- {param}")
                    if len(status_groups['valid']) > 5:
                        st.caption(f"... and {len(status_groups['valid']) - 5} more")
            
            if 'warning' in status_groups:
                with cols[1]:
                    st.warning(f"⚠️ Warnings ({len(status_groups['warning'])})")
                    for param in status_groups['warning']:
                        st.write(f"- {param}")
            
            if 'error' in status_groups:
                with cols[2]:
                    st.error(f"❌ Errors ({len(status_groups['error'])})")
                    for param in status_groups['error']:
                        st.write(f"- {param}")
    
    def render_parameter_inspector(self, config: Dict[str, Any]) -> None:
        """Render detailed parameter inspector"""
        st.subheader("Parameter Inspector")
        
        # Search functionality
        search_term = st.text_input("Search parameters", placeholder="Type to search...")
        
        # Filter parameters
        filtered_params = {}
        for key, value in config.items():
            if not search_term or search_term.lower() in key.lower():
                filtered_params[key] = value
        
        # Display filtered parameters
        for param_name, param_value in filtered_params.items():
            with st.expander(f"{param_name}: {param_value}"):
                param_def = self.param_manager.get_parameter_by_name(param_name)
                
                if param_def:
                    st.write(f"**Type**: {param_def.parameter_type.value}")
                    st.write(f"**Group**: {param_def.group}")
                    st.write(f"**Help**: {param_def.help_text}")
                    st.write(f"**Required**: {param_def.required}")
                
                st.write(f"**Current Value**: {param_value}")
                st.write(f"**Value Type**: {type(param_value).__name__}")
                
                if isinstance(param_value, (dict, list)):
                    st.json(param_value)
    
    def render_configuration_diff(self, config1: Dict, config2: Dict) -> None:
        """Render configuration comparison and diff"""
        st.subheader("Configuration Comparison")
        
        # Find differences
        all_keys = set(config1.keys()) | set(config2.keys())
        differences = []
        
        for key in all_keys:
            val1 = config1.get(key)
            val2 = config2.get(key)
            
            if val1 != val2:
                differences.append({
                    'parameter': key,
                    'config1': val1,
                    'config2': val2
                })
        
        if not differences:
            st.success("Configurations are identical")
            return
        
        st.write(f"Found {len(differences)} difference(s):")
        
        for diff in differences:
            with st.expander(f"Parameter: {diff['parameter']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Configuration 1:**")
                    if isinstance(diff['config1'], (dict, list)):
                        st.json(diff['config1'])
                    else:
                        st.code(str(diff['config1']))
                
                with col2:
                    st.write("**Configuration 2:**")
                    if isinstance(diff['config2'], (dict, list)):
                        st.json(diff['config2'])
                    else:
                        st.code(str(diff['config2']))
    
    def _get_field_sync_info(self, field_name: str, current_value: Any) -> Dict[str, Any]:
        """Get synchronization information for a field"""
        try:
            from .config_synchronizer import ConfigurationSynchronizer
            config_sync = ConfigurationSynchronizer()
            
            # Get configuration values
            config_values = config_sync.get_configuration_values()
            config_value = config_values.get(field_name, '')
            
            # Check if field is synchronized
            is_synchronized = config_sync.is_field_synchronized(field_name)
            
            return {
                'is_synchronized': is_synchronized and bool(config_value),
                'config_value': config_value,
                'current_value': current_value,
                'is_overridden': not is_synchronized and bool(current_value)
            }
            
        except ImportError:
            # Fallback if synchronizer not available
            return {
                'is_synchronized': False,
                'config_value': '',
                'current_value': current_value,
                'is_overridden': False
            }