# src/codexes/core/ui.py
from pathlib import Path

import streamlit as st
from typing import List, Dict, Any
from .simple_auth import get_auth

def build_sidebar(
    allowed_pages: List[st.Page],
    version_info: Dict[str, Any],
    auth_status: bool,
    username: str | None,
    user_role: str | None
):
    """
    Builds the standard sidebar for all pages.

    Args:
        allowed_pages (List[st.Page]): The list of pages the current user can see.
        version_info (Dict[str, Any]): The project's version information.
        auth_status (bool): The authentication status of the user.
        username (str | None): The user's username if logged in.
        user_role (str | None): The user's role if logged in.
    """
    with st.sidebar:
        st.title("Codexes Factory")


        # 1. Navigation (hidden - use custom sidebar instead)

        if allowed_pages:
            pg = st.navigation(allowed_pages, position="hidden")
        else:
            st.warning("No pages available for your role.")
            st.stop()

        # 2. Language Picker
        st.selectbox(
            "Language",
            options=['en', 'ko'],
            key='language'
        )

        # 3. Authentication Status
        auth = get_auth()
        if auth_status:
            st.success(f"Logged in as: **{username}**")
            st.caption(f"Role: {user_role.capitalize()}")
            
            # Check if persistent credentials exist
            persistent_file = Path(".claude/persistent_auth.json")
            has_saved_creds = persistent_file.exists()
            
            if has_saved_creds:
                st.caption("🔑 Auto-login enabled")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Logout", key="sidebar_logout"):
                    auth.logout()
                    st.rerun()
            
            with col2:
                if has_saved_creds:
                    if st.button("🗑️", key="clear_saved", help="Clear saved login"):
                        auth.logout(clear_persistent=True)
                        st.rerun()
        else:
            st.info("Not logged in.")
        # --- Imprint Selector (Admin Only) ---
        if user_role == 'admin':
            imprints = [d.name for d in Path("imprints").iterdir() if d.is_dir()]
            if "imprint" not in st.session_state:
                st.session_state.imprint = imprints[0] if imprints else None

            if imprints:
                selected_imprint = st.selectbox(
                    "Select Imprint",
                    imprints,
                    index=imprints.index(st.session_state.imprint) if st.session_state.imprint in imprints else 0
                )
                st.session_state.imprint = selected_imprint
            else:
                st.warning("No imprints found.")
                st.session_state.imprint = None
        else:
            st.session_state['imprint'] = 'xynapse_traces'

        # 4. PDF Harvest Monitor (Admin only)
        if user_role == 'admin':
            try:
                from codexes.core.pdf_monitor import get_monitor
                monitor = get_monitor()

                # Get notification status
                has_new_docs, new_docs_count, last_check = monitor.get_notification_status()

                # Monitor section header with notification badge
                if has_new_docs:
                    st.markdown("### 📥 PDF Monitor 🔴")
                    st.success(f"🆕 {new_docs_count} new documents found!")
                    if st.button("Clear Notifications", key="clear_notifications"):
                        monitor.clear_notifications()
                        st.rerun()
                else:
                    st.markdown("### 📥 PDF Monitor")

                # Monitor controls
                is_monitoring = monitor.is_monitoring_enabled()

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("▶️ Start" if not is_monitoring else "⏹️ Stop", key="toggle_monitor"):
                        if is_monitoring:
                            monitor.stop_monitoring()
                            st.success("Monitoring stopped")
                        else:
                            monitor.start_monitoring(interval_hours=6)
                            st.success("Monitoring started (6h intervals)")
                        st.rerun()

                with col2:
                    if st.button("🔄 Check Now", key="manual_check"):
                        with st.spinner("Checking for new documents..."):
                            result = monitor.run_single_check()
                            if "error" in result:
                                st.error(f"Check failed: {result['error']}")
                            else:
                                st.info(f"Found {result['total_new_docs']} new documents")
                        st.rerun()

                # Monitor status
                if last_check:
                    try:
                        from datetime import datetime
                        last_check_dt = datetime.fromisoformat(last_check.replace('Z', '+00:00') if last_check.endswith('Z') else last_check)
                        st.caption(f"Last check: {last_check_dt.strftime('%m/%d %H:%M')}")
                    except:
                        st.caption(f"Last check: {last_check}")

                if is_monitoring:
                    st.caption("🟢 Monitoring active (6h intervals)")
                else:
                    st.caption("⚪ Monitoring inactive")

            except ImportError:
                st.caption("PDF Monitor unavailable")

        # 5. Version Info Expander
        with st.expander("Version Information"):
            st.json(version_info, expanded=False)

    # Run the selected page
    pg.run()