"""
Imprint Administration Page

Comprehensive imprint management interface using the enhanced imprint
management architecture for administrators to manage existing imprints.
"""


import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
import json
import logging



logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)



# Add paths for imports
sys.path.insert(0, '/Users/fred/my-apps')

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
    from shared.ui import render_unified_sidebar
except ImportError as e:
    import streamlit as st
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()


sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import with fallback pattern
try:
    from codexes.core.auth import get_allowed_pages, get_user_role
except ImportError:
    from src.codexes.core.auth import get_allowed_pages, get_user_role

# Import the enhanced imprint management system
try:
    from codexes.modules.imprints.services.imprint_manager import ImprintManager
    from codexes.modules.imprints.models.imprint_core import ImprintStatus, ImprintType
    from codexes.modules.imprints.models.publisher_persona import PublisherPersona
except ImportError:
    try:
        from src.codexes.modules.imprints.services.imprint_manager import ImprintManager
        from src.codexes.modules.imprints.models.imprint_core import ImprintStatus, ImprintType
        from src.codexes.modules.imprints.models.publisher_persona import PublisherPersona
    except ImportError:
        # Fallback for development
        st.error("Enhanced imprint management system not available")
        st.stop()



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



logger = logging.getLogger(__name__)


def main():
    """Main imprint administration interface."""
    # NOTE: st.set_page_config() and render_unified_sidebar() handled by main app

    # Import and use page utilities for consistent sidebar and auth
    try:
        from codexes.core.page_utils import render_page_sidebar, ensure_auth_checked

        # Ensure auth has been checked for this session
        ensure_auth_checked()

        # Render the full sidebar with all sections
        render_page_sidebar()
    except ImportError as e:
        logger.warning(f"Could not import page_utils: {e}")
        # Fallback continues with existing code

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

    st.title("🏢 Imprint Administration")
    st.markdown("Comprehensive management interface for all publishing imprints")
    
    # Initialize the imprint manager
    @st.cache_resource
    def get_imprint_manager():
        return ImprintManager()
    
    manager = get_imprint_manager()
    
    # Create tabs for different admin functions
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Imprint Overview", "⚙️ Configure Imprint", "👤 Publisher Personas", "📊 Analytics"])
    
    with tab1:
        render_imprint_overview(manager)
    
    with tab2:
        render_imprint_configuration(manager)
    
    with tab3:
        render_publisher_personas(manager)
    
    with tab4:
        render_imprint_analytics(manager)


def render_imprint_overview(manager: ImprintManager):
    """Render overview of all imprints."""
    st.subheader("📋 Imprint Registry Overview")
    
    # Get all imprints
    all_imprints = manager.get_all_imprints()
    
    if not all_imprints:
        st.warning("No imprints found. Use the Imprint Builder to create new imprints.")
        return
    
    # Display registry statistics
    stats = manager.get_registry_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Imprints", stats["total_imprints"])
    with col2:
        st.metric("Active Imprints", stats["status_distribution"].get("active", 0))
    with col3:
        st.metric("Publishers", stats["publishers"])
    with col4:
        if stats["last_scan_time"]:
            st.metric("Last Scan", datetime.fromisoformat(stats["last_scan_time"]).strftime("%H:%M"))
    
    # Display imprints table
    st.subheader("Imprint Details")
    
    imprint_data = []
    for imprint in all_imprints:
        imprint_data.append({
            "Name": imprint.name,
            "Status": imprint.status.value,
            "Publisher": imprint.publisher,
            "Type": imprint.imprint_type.value,
            "Total Books": imprint.metrics.total_books,
            "Has Config": "✅" if imprint.configuration else "❌",
            "Has Assets": "✅" if imprint.assets else "❌",
            "Has Persona": "✅" if imprint.publisher_persona else "❌",
            "Created": imprint.created_at.strftime("%Y-%m-%d"),
            "Path Exists": "✅" if imprint.path and imprint.path.exists() else "❌"
        })
    
    df = pd.DataFrame(imprint_data)
    st.dataframe(df, use_container_width=True)
    
    # Quick actions
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Registry", help="Rescan for imprints"):
            manager.scan_imprints(force_rescan=True)
            st.success("Registry refreshed!")
            st.rerun()
    
    with col2:
        if st.button("📊 Generate Report", help="Generate imprint status report"):
            generate_imprint_report(manager)
    
    with col3:
        if st.button("🧹 Validate All", help="Validate all imprint configurations"):
            validate_all_imprints(manager)


def render_imprint_configuration(manager: ImprintManager):
    """Render imprint configuration interface."""
    st.subheader("⚙️ Imprint Configuration Management")
    
    # Select imprint to configure
    all_imprints = manager.get_all_imprints()
    if not all_imprints:
        st.warning("No imprints available for configuration.")
        return
    
    imprint_names = [imp.name for imp in all_imprints]
    selected_name = st.selectbox("Select Imprint to Configure", imprint_names)
    
    if selected_name:
        imprint = manager.get_imprint(selected_name)
        
        # Display current configuration
        st.markdown(f"### Configuration for {imprint.name}")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if imprint.configuration:
                config_data = imprint.configuration.get_resolved_config()
                st.json(config_data, expanded=False)
            else:
                st.warning("No configuration found for this imprint")
        
        with col2:
            st.markdown("**Imprint Details**")
            st.write(f"**Status**: {imprint.status.value}")
            st.write(f"**Type**: {imprint.imprint_type.value}")
            st.write(f"**Publisher**: {imprint.publisher}")
            st.write(f"**Created**: {imprint.created_at.strftime('%Y-%m-%d')}")
            
            if imprint.assets:
                st.write(f"**Assets**: {len(imprint.assets.assets)} found")
                interior_template = imprint.assets.get_interior_template_path()
                cover_template = imprint.assets.get_cover_template_path()
                st.write(f"**Interior Template**: {'✅' if interior_template else '❌'}")
                st.write(f"**Cover Template**: {'✅' if cover_template else '❌'}")
        
        # Configuration actions
        st.markdown("### Configuration Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"🔍 Validate {selected_name}", help="Validate imprint configuration"):
                validation = manager.validate_imprint(selected_name)
                display_validation_results(validation)
        
        with col2:
            if st.button(f"📄 Export Config", help="Export configuration to file"):
                if imprint.configuration:
                    export_path = manager.export_imprint_data(selected_name)
                    st.success(f"Configuration exported to: {export_path}")
                else:
                    st.error("No configuration to export")
        
        with col3:
            if st.button(f"🎨 Generate Templates", help="Generate templates for imprint"):
                if imprint.assets:
                    try:
                        generated = manager.template_service.generate_imprint_templates(imprint)
                        st.success(f"Generated {len(generated)} templates")
                        for template_type, path in generated.items():
                            st.write(f"- {template_type}: {path}")
                    except Exception as e:
                        st.error(f"Template generation failed: {e}")
                else:
                    st.error("No assets configuration found")


def render_publisher_personas(manager: ImprintManager):
    """Render publisher persona management interface."""
    st.subheader("👤 Publisher Persona Management")
    
    # Select imprint
    all_imprints = manager.get_all_imprints()
    if not all_imprints:
        st.warning("No imprints available.")
        return
    
    imprint_names = [imp.name for imp in all_imprints]
    selected_name = st.selectbox("Select Imprint", imprint_names, key="persona_imprint_select")
    
    if selected_name:
        imprint = manager.get_imprint(selected_name)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if imprint.publisher_persona:
                st.markdown(f"### Current Persona: {imprint.publisher_persona.name}")
                
                # Display persona details
                persona = imprint.publisher_persona
                st.write(f"**Bio**: {persona.bio}")
                st.write(f"**Risk Tolerance**: {persona.risk_tolerance.value}")
                st.write(f"**Decision Style**: {persona.decision_style.value}")
                
                if persona.personality_traits:
                    st.markdown("**Personality Traits**:")
                    for trait in persona.personality_traits:
                        st.write(f"- {trait.name}: {trait.strength:.2f} - {trait.description}")
                
                if persona.vulnerability_factors:
                    st.markdown("**Vulnerabilities**:")
                    for vuln in persona.vulnerability_factors:
                        st.write(f"🚨 {vuln.name} (severity: {vuln.severity:.2f})")
                        st.write(f"   {vuln.description}")
            else:
                st.info("No publisher persona configured for this imprint")
        
        with col2:
            st.markdown("**Persona Actions**")
            
            # Test content evaluation
            if imprint.publisher_persona:
                st.markdown("**Test Content Evaluation**")
                
                with st.form("content_evaluation_form"):
                    test_title = st.text_input("Content Title", "Sample Book Title")
                    controversy_level = st.slider("Controversy Level", 0.0, 1.0, 0.5)
                    target_audience = st.text_input("Target Audience", "General readers")
                    estimated_cost = st.number_input("Estimated Cost", 0, 500000, 75000)
                    
                    if st.form_submit_button("Evaluate Content"):
                        test_content = {
                            "title": test_title,
                            "controversy_level": controversy_level,
                            "target_audience": target_audience,
                            "estimated_cost": estimated_cost
                        }
                        
                        evaluation = imprint.publisher_persona.evaluate_acquisition_decision(test_content)
                        
                        st.markdown("**Evaluation Results**")
                        st.metric("Overall Score", f"{evaluation['overall_score']:.2f}")
                        st.write(f"**Recommendation**: {evaluation['recommendation']}")
                        
                        if evaluation.get("excitement_factors"):
                            st.markdown("**Excitement Factors**:")
                            for factor in evaluation["excitement_factors"]:
                                st.write(f"✨ {factor}")
                        
                        if evaluation.get("concerns"):
                            st.markdown("**Concerns**:")
                            for concern in evaluation["concerns"]:
                                st.write(f"⚠️ {concern}")
            
            # Persona management actions
            if st.button("➕ Add Max Bialystok Persona", help="Add the sample Max Bialystok persona"):
                try:
                    persona = PublisherPersona.create_max_bialystok_persona()
                    success = manager.set_publisher_persona(selected_name, persona)
                    if success:
                        st.success("Max Bialystok persona added!")
                        st.rerun()
                    else:
                        st.error("Failed to add persona")
                except Exception as e:
                    st.error(f"Error adding persona: {e}")
            
            if imprint.publisher_persona:
                if st.button("🗑️ Remove Persona", help="Remove current persona"):
                    imprint.publisher_persona = None
                    st.success("Persona removed!")
                    st.rerun()


def render_imprint_analytics(manager: ImprintManager):
    """Render imprint analytics and metrics."""
    st.subheader("📊 Imprint Analytics")
    
    # Registry statistics
    stats = manager.get_registry_stats()
    
    st.markdown("### Registry Statistics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Status Distribution**")
        status_data = stats["status_distribution"]
        if status_data:
            status_df = pd.DataFrame(list(status_data.items()), columns=["Status", "Count"])
            st.bar_chart(status_df.set_index("Status"))
    
    with col2:
        st.markdown("**Type Distribution**") 
        type_data = stats["type_distribution"]
        if type_data:
            type_df = pd.DataFrame(list(type_data.items()), columns=["Type", "Count"])
            st.bar_chart(type_df.set_index("Type"))
    
    # Individual imprint metrics
    st.markdown("### Imprint Metrics")
    
    all_imprints = manager.get_all_imprints()
    metrics_data = []
    
    for imprint in all_imprints:
        metrics_data.append({
            "Imprint": imprint.name,
            "Total Books": imprint.metrics.total_books,
            "Published Books": imprint.metrics.published_books,
            "Success Rate": f"{imprint.metrics.success_rate:.1%}",
            "Avg Production Days": imprint.metrics.avg_production_time_days,
            "Has Persona": "✅" if imprint.publisher_persona else "❌",
            "Ideation Active": "✅" if imprint.ideation_session_id else "❌"
        })
    
    if metrics_data:
        metrics_df = pd.DataFrame(metrics_data)
        st.dataframe(metrics_df, use_container_width=True)
    
    # Performance insights
    st.markdown("### Performance Insights")
    
    active_imprints = [imp for imp in all_imprints if imp.is_active()]
    persona_imprints = [imp for imp in all_imprints if imp.publisher_persona]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Active Imprints", len(active_imprints))
    
    with col2:
        st.metric("With Personas", len(persona_imprints))
    
    with col3:
        avg_books = sum(imp.metrics.total_books for imp in all_imprints) / len(all_imprints) if all_imprints else 0
        st.metric("Avg Books/Imprint", f"{avg_books:.1f}")


def display_validation_results(validation: dict):
    """Display validation results in a user-friendly format."""
    if validation["overall_valid"]:
        st.success("✅ Imprint configuration is valid")
    else:
        st.error("❌ Imprint configuration has issues")
    
    if validation.get("errors"):
        st.markdown("**Errors:**")
        for error in validation["errors"]:
            st.error(f"❌ {error}")
    
    if validation.get("warnings"):
        st.markdown("**Warnings:**")
        for warning in validation["warnings"]:
            st.warning(f"⚠️ {warning}")
    
    if validation.get("suggestions"):
        st.markdown("**Suggestions:**")
        for suggestion in validation["suggestions"]:
            st.info(f"💡 {suggestion}")


def generate_imprint_report(manager: ImprintManager):
    """Generate comprehensive imprint status report."""
    try:
        all_imprints = manager.get_all_imprints()
        
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "total_imprints": len(all_imprints),
            "registry_stats": manager.get_registry_stats(),
            "imprint_details": []
        }
        
        for imprint in all_imprints:
            validation = manager.validate_imprint(imprint.name)
            
            report_data["imprint_details"].append({
                "name": imprint.name,
                "status": imprint.status.value,
                "publisher": imprint.publisher,
                "validation_valid": validation["overall_valid"],
                "errors_count": len(validation.get("errors", [])),
                "warnings_count": len(validation.get("warnings", [])),
                "has_persona": imprint.publisher_persona is not None,
                "total_books": imprint.metrics.total_books
            })
        
        # Save report
        report_path = Path("reports") / f"imprint_status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        st.success(f"Report generated: {report_path}")
        st.download_button(
            "Download Report",
            data=json.dumps(report_data, indent=2),
            file_name=f"imprint_report_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
        
    except Exception as e:
        st.error(f"Failed to generate report: {e}")


def validate_all_imprints(manager: ImprintManager):
    """Validate all imprints and display results."""
    all_imprints = manager.get_all_imprints()
    
    st.markdown("### Validation Results")
    
    validation_results = []
    for imprint in all_imprints:
        validation = manager.validate_imprint(imprint.name)
        validation_results.append({
            "Imprint": imprint.name,
            "Valid": "✅" if validation["overall_valid"] else "❌",
            "Errors": len(validation.get("errors", [])),
            "Warnings": len(validation.get("warnings", [])),
            "Status": imprint.status.value
        })
    
    df = pd.DataFrame(validation_results)
    st.dataframe(df, use_container_width=True)
    
    # Summary
    valid_count = sum(1 for result in validation_results if result["Valid"] == "✅")
    total_count = len(validation_results)
    
    st.metric("Validation Rate", f"{valid_count}/{total_count} ({valid_count/total_count:.1%})")


if __name__ == "__main__":
    main()