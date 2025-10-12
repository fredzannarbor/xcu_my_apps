
import streamlit as st
from utilities_daily_engine import run_project_command

def render_projects_ui(projects):
    """Renders the project status and interaction UI."""
    st.header("🚀 Projects")

    if projects:
        for project_id, project_config in projects.items():
            project_name = project_config.get('name', project_id)
            project_path = project_config.get('path', '')

            with st.expander(f"📁 {project_name}", expanded=False):
                st.write(f"**Path:** `{project_path}`")

                # Compact command interface
                col_status, col_revenue = st.columns(2)
                with col_status:
                    if st.button("📊 Status", key=f"status_{project_id}", help="Check project status"):
                        with st.spinner("Checking..."):
                            result = run_project_command(project_id, "ls -la", projects)
                            st.code(result[:200] + "..." if len(result) > 200 else result)

                with col_revenue:
                    revenue = st.number_input(
                        "Revenue ($)",
                        min_value=0.0,
                        key=f"revenue_{project_id}",
                        help=f"Today's revenue from {project_name}"
                    )

                # Custom command input (collapsed by default)
                with st.expander("🔧 Custom Command", expanded=False):
                    command = st.text_input(f"Command:", key=f"cmd_{project_id}")
                    if st.button("▶️ Run", key=f"run_{project_id}") and command:
                        with st.spinner("Running..."):
                            result = run_project_command(project_id, command, projects)
                            st.code(result[:300] + "..." if len(result) > 300 else result)
    else:
        st.info("No projects configured")
