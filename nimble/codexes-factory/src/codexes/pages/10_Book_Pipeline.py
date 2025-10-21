# src/codexes/pages/10_Book_Pipeline.py
import streamlit as st
from pathlib import Path
import subprocess
import os
import sys
import json
import time
import logging
from datetime import datetime

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

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import enhanced UI components
try:
    from codexes.modules.ui.streamlit_components import ConfigurationUI
    from codexes.modules.ui.command_builder import CommandBuilder
    from codexes.modules.ui.parameter_groups import ParameterGroupManager
    from codexes.modules.ui.tranche_config_ui_manager import TrancheConfigUIManager
    ENHANCED_UI_AVAILABLE = True
except ImportError:
    try:
        from src.codexes.modules.ui.streamlit_components import ConfigurationUI
        from src.codexes.modules.ui.command_builder import CommandBuilder
        from src.codexes.modules.ui.parameter_groups import ParameterGroupManager
        from src.codexes.modules.ui.tranche_config_ui_manager import TrancheConfigUIManager
        ENHANCED_UI_AVAILABLE = True
    except ImportError as e:
        st.warning(f"Enhanced UI components not available: {e}")
        st.info("Falling back to basic UI mode.")
        ENHANCED_UI_AVAILABLE = False
        ConfigurationUI = None
        CommandBuilder = None
        ParameterGroupManager = None
        TrancheConfigUIManager = None

# Try to import from the correct module path
try:
    from codexes.core.enhanced_llm_caller import call_llm_json_with_exponential_backoff
except ImportError:
    try:
        from src.codexes.core.enhanced_llm_caller import call_llm_json_with_exponential_backoff
    except ImportError:
        # If module not found, we'll handle this gracefully later
        pass

# Import enhanced prompts UI
try:
    from codexes.modules.prompts.enhanced_prompts_ui import EnhancedPromptsUI
    ENHANCED_PROMPTS_AVAILABLE = True
except ImportError:
    try:
        from src.codexes.modules.prompts.enhanced_prompts_ui import EnhancedPromptsUI
        ENHANCED_PROMPTS_AVAILABLE = True
    except ImportError:
        ENHANCED_PROMPTS_AVAILABLE = False
        EnhancedPromptsUI = None

# NOTE: st.set_page_config() and render_unified_sidebar() handled by main app

# Import and use page utilities for consistent sidebar and auth
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

# Initialize session state for UI components
if 'config_ui_state' not in st.session_state:
    st.session_state.config_ui_state = {
        'display_mode': 'simple',
        'selected_publisher': '',
        'selected_imprint': '',
        'selected_tranche': '',
        'current_config': {},
        'validation_results': None,
        'expanded_groups': set()
    }

st.title("🚀 Book Production Pipeline")

# Add ISBN Management integration
st.sidebar.markdown("---")
st.sidebar.markdown("### 📖 ISBN Management")
if st.sidebar.button("📖 Open ISBN Manager"):
    st.switch_page("pages/24_ISBN_Management.py")

# Quick ISBN status
try:
    from src.codexes.modules.distribution.isbn_integration import get_isbn_integration
    isbn_integration = get_isbn_integration()
    stats = isbn_integration.get_database_stats()
    st.sidebar.metric("Available ISBNs", f"{stats['available_count']:,}")
    st.sidebar.metric("Total ISBNs", f"{stats['total_isbns']:,}")
except Exception as e:
    st.sidebar.warning("ISBN database not available")

if ENHANCED_UI_AVAILABLE:
    st.markdown("Enhanced interface with complete configuration management and parameter inspection.")
    # Initialize enhanced UI components
    config_ui = ConfigurationUI()
    command_builder = CommandBuilder()
    param_manager = ParameterGroupManager()
    tranche_ui_manager = TrancheConfigUIManager()
else:
    st.markdown("Basic interface for book pipeline execution.")
    st.warning("Enhanced UI features are not available. Using fallback mode.")
    config_ui = None
    command_builder = None
    param_manager = None
    tranche_ui_manager = None

# --- Helper functions ---
def get_available_imprints():
    imprint_dir = Path("imprints")
    if not imprint_dir.is_dir():
        return []
    return [d.name for d in imprint_dir.iterdir() if d.is_dir()]

def get_available_models():
    return [
        "gemini/gemini-2.5-flash",
        "gemini/gemini-2.5-pro",
        "anthropic/claude-sonnet-4-5-20250929",
        "xai/grok-3-latest"
    ]

def get_available_schedule_files():
    schedules = []
    
    # Check in imprints directories
    imprint_dir = Path("imprints")
    if imprint_dir.is_dir():
        for imprint in imprint_dir.iterdir():
            if imprint.is_dir():
                for file in imprint.glob("*schedule*.json"):
                    schedules.append(str(file))
    
    # Check in resources directory
    resources_dir = Path("resources/json")
    if resources_dir.is_dir():
        for file in resources_dir.glob("*schedule*.json"):
            schedules.append(str(file))
    
    # Add sample schedules
    for file in Path(".").glob("*schedule*.json"):
        schedules.append(str(file))
    
    return schedules

# --- Configuration Selection (Outside Form) ---
if ENHANCED_UI_AVAILABLE:
    st.header("📚 Enhanced Pipeline Configuration")
    
    # Explanation of the two main sections
    with st.expander("ℹ️ Understanding Configuration vs Core Settings", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **📋 Configuration Selection**
            - Follow the **Publisher → Imprint → Tranche** hierarchy
            - **Publisher** (required): Sets organization identity
            - **Imprint** (optional): Specialized brand under publisher
            - **Tranche** (optional): Shared metadata for batch processing
            - Sets up LSI account, pricing, metadata defaults
            """
)
        with col2:
            st.markdown("""
            **⚙️ Core Settings** 
            - **Runtime parameters** for this specific run
            - Model selection, book limits, stages to run
            - Overrides config file defaults
            - Example: Change model from config default
            - Controls what happens during pipeline execution
            """)
    
    # Configuration Selection and Display Mode (Outside the form)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Use hierarchical Publisher → Imprint → Tranche selector
        st.subheader("📋 Configuration Selection")
        st.markdown("*Follow the hierarchy: Publisher (required) → Imprint (optional) → Tranche (optional)*")

        hierarchy_selection = tranche_ui_manager.render_hierarchical_selector(key="main_hierarchy_selector")

        # Extract values from hierarchical selection
        publisher = hierarchy_selection.get('publisher', '')
        imprint = hierarchy_selection.get('imprint', '')
        tranche = hierarchy_selection.get('tranche', '')
        tranche_config = hierarchy_selection.get('tranche_config')

        # Show tranche details if a tranche is selected
        if tranche and tranche_config:
            with st.expander("📊 Tranche Configuration Details", expanded=False):
                st.json(tranche_config)
    
    with col2:
        display_mode = config_ui.render_display_mode_selector()
        
        # Add refresh button for tranche configurations
        if st.button("🔄 Refresh Tranches", help="Reload tranche configurations from disk"):
            tranche_ui_manager.refresh_tranche_dropdown()
            st.success("Tranche configurations refreshed!")
            st.rerun()
else:
    publisher, imprint, tranche = '', '', ''
    display_mode = 'simple'

# --- UI Form ---
with st.form("pipeline_form"):
    if ENHANCED_UI_AVAILABLE:
        # Import and initialize configuration synchronizer
        try:
            from codexes.modules.ui.config_synchronizer import ConfigurationSynchronizer
            config_sync = ConfigurationSynchronizer()
            
            # Synchronize configuration selection to form defaults
            sync_data = config_sync.sync_config_to_form(publisher, imprint, tranche)
            
        except ImportError:
            # Fallback if synchronizer not available
            sync_data = {
                'publisher': publisher,
                'imprint': imprint,
                'tranche': tranche
            }
        
        # Initialize form data from current configuration and sync data
        current_config = st.session_state.config_ui_state.get('current_config', {})
        form_data = current_config.copy()
        
        # Apply synchronized configuration values as defaults
        for key, value in sync_data.items():
            if key not in form_data or not form_data[key]:
                form_data[key] = value
        
        # Get parameter groups for current display mode
        parameter_groups = param_manager.get_parameters_for_display_mode(display_mode)
        
        # Render parameter groups
        all_form_data = {}
        
        for group_name, group in param_manager.get_parameter_groups().items():
            if group_name in parameter_groups:
                group_data = config_ui.render_parameter_group(group, display_mode, form_data)
                all_form_data.update(group_data)
        
        # Ensure synchronized values are included in final form data
        for key, value in sync_data.items():
            if key not in all_form_data or not all_form_data[key]:
                all_form_data[key] = value
    else:
        st.header("Basic Pipeline Configuration")
        
        # Use hierarchical configuration values as defaults for basic mode
        default_imprint = imprint if imprint else ''
        default_publisher = publisher if publisher else ''
        
        # Basic form elements
        col1, col2 = st.columns(2)
        with col1:
            # Use configuration selection as default, but allow override
            available_imprints = get_available_imprints()
            imprint_index = available_imprints.index(default_imprint) if default_imprint in available_imprints else 0
            selected_imprint = st.selectbox(
                "Select Imprint", 
                options=available_imprints, 
                index=imprint_index,
                help="The publishing imprint to use. Auto-populated from configuration selection above."
            )
            
            model = st.selectbox("Primary LLM Model", options=get_available_models(), help="The main model for content generation.")
        with col2:
            verifier_model = st.selectbox("Verifier LLM Model", options=get_available_models(), help="A high-quality model for quote verification.")
            max_books = st.number_input("Max Books", min_value=1, step=1, value=1, format="%d", help="Maximum number of books to process.")
        
        all_form_data = {
            'publisher': default_publisher,
            'imprint': selected_imprint,
            'tranche': tranche,
            'model': model,
            'verifier_model': verifier_model,
            'max_books': max_books
        }
    
    # Handle schedule file specially (backward compatibility)
    schedule_options = get_available_schedule_files()
    schedule_options.insert(0, "null")  # Add null option at the beginning

    if 'schedule_file' not in all_form_data:
        with st.expander("📅 Schedule File Selection", expanded=True):
            st.info("💡 Select 'null' to generate title, metadata, and content from analyzing body text or model runs instead of using a predefined schedule.")

            col1, col2 = st.columns(2)
            with col1:
                schedule_file_path = st.selectbox(
                    "Select Schedule File",
                    options=schedule_options,
                    help="The JSON file containing the book schedule. Select 'null' to analyze content dynamically."
                )
                use_uploaded_schedule = st.checkbox("Upload custom schedule file instead", value=False)
            with col2:
                if use_uploaded_schedule and schedule_file_path != "null":
                    schedule_file = st.file_uploader("Upload Schedule File", type=['json'], help="The JSON file containing the book schedule.")
                    all_form_data['schedule_file'] = schedule_file
                else:
                    all_form_data['schedule_file'] = schedule_file_path if schedule_file_path != "null" else None

    # Handle stage selection for backward compatibility
    if 'start_stage' in all_form_data and 'end_stage' in all_form_data:
        start_stage = all_form_data['start_stage']
        end_stage = all_form_data['end_stage']
    else:
        # Fallback to original stage selection
        with st.expander("Pipeline Stages", expanded=True):
            stage_options = {
                1: "1: LLM Content Generation",
                2: "2: Quote Verification", 
                3: "3: Prepress (PDF Generation)",
                4: "4: LSI Spreadsheet Generation"
            }
            
            st.info("ℹ️ Pipeline runs in 4 stages. Quote processing happens in Stage 1, verification in Stage 2.")
            
            col1, col2 = st.columns(2)
            with col1:
                start_stage_str = st.selectbox(
                    "Start Stage",
                    options=stage_options.values(),
                    index=0,
                    help="Select the first stage to run."
                )
            with col2:
                end_stage_str = st.selectbox(
                    "End Stage",
                    options=stage_options.values(),
                    index=len(stage_options) - 1,
                    help="Select the last stage to run."
                )
            
            start_stage = int(start_stage_str.split(':')[0])
            end_stage = int(end_stage_str.split(':')[0])
            all_form_data['start_stage'] = start_stage
            all_form_data['end_stage'] = end_stage

    # Add any missing parameters with defaults for backward compatibility
    default_values = {
        'max_books': 1,
        'begin_with_book': 1,
        'end_with_book': 0,
        'only_run_prompts': '',
        'quotes_per_book': 0,
        'skip_lsi': False,
        'enable_llm_completion': True,
        'enable_isbn_assignment': True,
        'lightning_source_account': '6024045',
        'language_code': 'eng',
        'lsi_config': '',
        'lsi_template': 'templates/LSI_ACS_header.csv',
        'report_formats': ['html'],
        'legacy_reports': False,
        'model_params_file': 'resources/json/model_params.json',
        'catalog_file': 'data/books.csv',
        'base_dir': '',
        'debug_cover': False,
        'leave_build_dirs': True,
        'catalog_only': False,
        'skip_catalog': False,
        'terse_log': False,
        'no_litellm_log': True,
        'show_prompt_logs': False,
        'verbose': False,
        'overwrite': True,
        'enable_metadata_discovery': False
    }
    
    for key, default_value in default_values.items():
        if key not in all_form_data:
            all_form_data[key] = default_value

    # --- Enhanced Prompts Configuration ---
    enhanced_prompts_data = {}
    if ENHANCED_PROMPTS_AVAILABLE:
        st.markdown("---")

        # Initialize enhanced prompts UI
        enhanced_prompts_ui = EnhancedPromptsUI()

        try:
            # Always render enhanced prompts configuration (enabled by default)
            publisher_files, imprint_files, book_structure = enhanced_prompts_ui.render_prompts_configuration_section()

            # Store enhanced prompts data
            enhanced_prompts_data = {
                'enhanced_prompts_enabled': True,
                'publisher_files': publisher_files,
                'imprint_files': imprint_files,
                'book_structure': book_structure.to_dict() if book_structure else {}
            }

            # Render command preview
            if publisher_files or imprint_files:
                enhanced_args = enhanced_prompts_ui.render_command_preview(
                    publisher_files, imprint_files, book_structure
                )
                enhanced_prompts_data['enhanced_args'] = enhanced_args

            # Render save/load section
            enhanced_prompts_ui.render_save_load_section(book_structure)

        except Exception as e:
            st.error(f"❌ Enhanced prompts error: {e}")
            st.exception(e)
            # Fallback to disabled state on error
            enhanced_prompts_data = {'enhanced_prompts_enabled': False}
    else:
        # Enhanced prompts not available, use traditional mode
        enhanced_prompts_data = {'enhanced_prompts_enabled': False}

    # Merge enhanced prompts data into form data
    all_form_data.update(enhanced_prompts_data)

    # Configuration Preview
    st.markdown("---")
    if ENHANCED_UI_AVAILABLE and config_ui:
        config_ui.render_complete_configuration_preview(all_form_data)
    else:
        st.subheader("Configuration Summary")
        st.json(all_form_data)
    
    # Submit Button
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        submitted = st.form_submit_button("🚀 Run Pipeline", type="primary", use_container_width=True)
    
    with col2:
        save_config = st.form_submit_button("💾 Save Configuration", use_container_width=True)
    
    with col3:
        export_config = st.form_submit_button("📤 Export Configuration", use_container_width=True)
    
    with col4:
        validate_config = st.form_submit_button("✅ Validate Only", use_container_width=True)

# --- Handle Form Submissions ---
if save_config:
    try:
        if ENHANCED_UI_AVAILABLE and command_builder:
            config_path = command_builder.export_configuration(all_form_data)
            st.success(f"Configuration saved to: {config_path}")
        else:
            st.info("Configuration saving requires enhanced UI components.")
    except Exception as e:
        st.error(f"Error saving configuration: {e}")

if export_config:
    try:
        export_data = json.dumps(all_form_data, indent=2, default=str)
        st.download_button(
            label="Download Configuration",
            data=export_data,
            file_name=f"pipeline_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    except Exception as e:
        st.error(f"Error exporting configuration: {e}")

if validate_config:
    if ENHANCED_UI_AVAILABLE and config_ui:
        # Use configuration-aware validation
        try:
            from codexes.modules.ui.config_aware_validator import ConfigurationAwareValidator
            config_aware_validator = ConfigurationAwareValidator()
            
            # Get configuration selection context
            config_selection = {
                'publisher': publisher,
                'imprint': imprint,
                'tranche': tranche
            }
            
            # Perform configuration-aware validation
            validation_results = config_aware_validator.validate_with_config_context(
                all_form_data, config_selection
            )
            
            # Store and display results
            st.session_state.config_ui_state['validation_results'] = validation_results
            config_ui.render_validation_results(validation_results)
            
        except ImportError:
            # Fallback to validation manager if config-aware validator not available
            try:
                from codexes.modules.ui.validation_manager import ValidationManager
                validation_manager = ValidationManager()
                
                if validation_manager.can_validate():
                    validation_results = validation_manager.validate_configuration_safe(all_form_data)
                    if validation_results:
                        st.session_state.config_ui_state['validation_results'] = validation_results
                        validation_manager.display_validation_results_stable(validation_results)
                    else:
                        st.warning("Validation is currently in progress or blocked to prevent loops")
                else:
                    st.info("Validation is temporarily disabled to prevent loops. Please wait a moment.")
            except ImportError:
                # Final fallback to original validation
                validation_results = config_ui.validator.validate_configuration(all_form_data)
                st.session_state.config_ui_state['validation_results'] = validation_results
                config_ui.render_validation_results(validation_results)
    else:
        st.info("Configuration validation requires enhanced UI components.")

# --- Pipeline Execution Logic ---
if submitted:
    # Validate configuration before execution using configuration-aware validation
    validation_passed = True
    if ENHANCED_UI_AVAILABLE and config_ui:
        try:
            config_aware_validator = ConfigurationAwareValidator()
            
            # Get configuration selection context
            config_selection = {
                'publisher': publisher,
                'imprint': imprint,
                'tranche': tranche
            }
            
            # Perform configuration-aware validation
            validation_results = config_aware_validator.validate_with_config_context(
                all_form_data, config_selection
            )
            
            if not validation_results.is_valid:
                st.error("❌ Configuration validation failed. Please fix the errors before running the pipeline.")
                config_ui.render_validation_results(validation_results)
                validation_passed = False
                
        except ImportError:
            # Fallback to original validation
            validation_results = config_ui.validator.validate_configuration(all_form_data)
            if not validation_results.is_valid:
                st.error("❌ Configuration validation failed. Please fix the errors before running the pipeline.")
                config_ui.render_validation_results(validation_results)
                validation_passed = False
    else:
        # Basic validation for required fields with configuration context
        required_fields = ['publisher', 'imprint']
        for field in required_fields:
            # Check both form data and configuration selection
            form_value = all_form_data.get(field)
            config_value = locals().get(field, '')  # Get publisher/imprint from configuration selection
            
            if not form_value and not config_value:
                st.error(f"❌ {field.title()} is required. Please select one in the Configuration Selection section above.")
                validation_passed = False
    
    if validation_passed:
        st.header("✅ Pipeline Execution")
        st.success("Configuration validated successfully!")
        
        # Build command
        try:
            if ENHANCED_UI_AVAILABLE and command_builder:
                # Use enhanced command builder
                command = command_builder.build_pipeline_command(all_form_data)
                
                # Validate command
                command_validation = command_builder.validate_command_parameters(command)
                
                if not command_validation['is_valid']:
                    st.error("❌ Command validation failed:")
                    for error in command_validation['errors']:
                        st.error(f"- {error}")
                    st.stop()
                
                # Show command summary
                with st.expander("Command Summary", expanded=True):
                    command_summary = command_builder.get_command_summary(command)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Arguments", command_summary['total_args'])
                    with col2:
                        st.metric("Parameters", len(command_summary['parameters']))
                    with col3:
                        st.metric("Flags", len(command_summary['flags']))
                    
                    # Show command preview
                    st.code(" \\\n  ".join(command), language="bash")
                
                # Generate audit log
                audit_log_path = command_builder.generate_command_audit_log(command, all_form_data)
                if audit_log_path:
                    st.info(f"📋 Command audit log: {audit_log_path}")
            else:
                # Basic command building
                command = [
                    sys.executable,
                    "run_book_pipeline.py",
                    "--imprint", all_form_data.get('imprint', ''),
                    "--model", all_form_data.get('model', 'gemini/gemini-2.5-flash')
                ]
                
                if all_form_data.get('verifier_model'):
                    command.extend(["--verifier-model", all_form_data['verifier_model']])
                if all_form_data.get('max_books', 0) > 0:
                    command.extend(["--max-books", str(all_form_data['max_books'])])
                
                st.code(" ".join(command), language="bash")
            
        except Exception as e:
            st.error(f"Error building command: {e}")
            st.stop()
        
        log_container = st.empty()
        log_container.info("🚀 Starting pipeline execution... Logs will appear below.")

        # Run the pipeline as a subprocess
        log_content = ""
        start_time = time.time()
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                bufsize=1
            )

            # Stream the output to the UI
            for line in iter(process.stdout.readline, ''):
                log_content += line
                log_container.markdown(f"```log\n{log_content}\n```")
            
            process.stdout.close()
            return_code = process.wait()

            end_time = time.time()
            duration = end_time - start_time
            
            if return_code == 0:
                st.success(f"🎉 Pipeline completed successfully in {duration:.2f} seconds!")
                
                # Show output directory
                output_dir = all_form_data.get('base_dir') or f"output/{all_form_data.get('imprint', 'unknown')}_build"
                if Path(output_dir).exists():
                    st.info(f"📁 Output files are available in: {output_dir}")
                    
                    # Show generated files if available
                    interior_pdf_dir = Path(output_dir) / "interior"
                    cover_pdf_dir = Path(output_dir) / "covers"
                    lsi_csv_dir = Path(output_dir) / "lsi_csv"
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if interior_pdf_dir.exists() and list(interior_pdf_dir.glob("*.pdf")):
                            st.success("✅ Interior PDFs generated")
                            for pdf in interior_pdf_dir.glob("*.pdf"):
                                st.download_button(
                                    f"📄 Download {pdf.name}",
                                    data=open(pdf, "rb").read(),
                                    file_name=pdf.name,
                                    mime="application/pdf",
                                    key=f"interior_{pdf.name}"
                                )
                    
                    with col2:
                        if cover_pdf_dir.exists() and list(cover_pdf_dir.glob("*.pdf")):
                            st.success("✅ Cover PDFs generated")
                            for pdf in cover_pdf_dir.glob("*.pdf"):
                                st.download_button(
                                    f"🎨 Download {pdf.name}",
                                    data=open(pdf, "rb").read(),
                                    file_name=pdf.name,
                                    mime="application/pdf",
                                    key=f"cover_{pdf.name}"
                                )
                    
                    with col3:
                        if lsi_csv_dir.exists() and list(lsi_csv_dir.glob("*.csv")):
                            st.success("✅ LSI CSV files generated")
                            for csv in lsi_csv_dir.glob("*.csv"):
                                st.download_button(
                                    f"📊 Download {csv.name}",
                                    data=open(csv, "rb").read(),
                                    file_name=csv.name,
                                    mime="text/csv",
                                    key=f"lsi_{csv.name}"
                                )
            else:
                st.error(f"❌ Pipeline failed with exit code: {return_code}")
                st.warning("⚠️ Check the logs for details on what went wrong.")

        except Exception as e:
            st.error(f"💥 An error occurred while running the pipeline: {e}")
            log_container.markdown(f"```log\n{log_content}\n\nEXCEPTION: {e}\n```")
        finally:
            # Clean up temporary files
            if ENHANCED_UI_AVAILABLE and command_builder:
                command_builder.cleanup_temp_files()
                
            # Save execution log
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"enhanced_pipeline_run_{timestamp}.log"
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"Enhanced Pipeline execution log - {datetime.now().isoformat()}\n")
                f.write(f"Command: {' '.join(command)}\n")
                f.write(f"Configuration: {json.dumps(all_form_data, indent=2, default=str)}\n\n")
                f.write(log_content)
            
            st.info(f"📋 Execution log saved to {log_file}")

# --- Additional UI Features ---
if ENHANCED_UI_AVAILABLE and config_ui and st.session_state.config_ui_state.get('current_config'):
    with st.expander("🔍 Parameter Inspector", expanded=False):
        config_ui.render_parameter_inspector(st.session_state.config_ui_state['current_config'])