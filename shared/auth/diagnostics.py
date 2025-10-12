"""
SSO Diagnostics Tool

This module provides diagnostic utilities for troubleshooting SSO issues.
"""

import streamlit as st
import sqlite3
from pathlib import Path
from datetime import datetime
import json

SHARED_AUTH_DB = Path("/Users/fred/xcu_my_apps/shared/auth/auth_sessions.db")


def show_sso_diagnostics():
    """Display SSO diagnostic information in Streamlit."""

    st.title("🔍 SSO Diagnostics")

    # 1. Session State
    st.header("1. Current Session State")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Authentication Status")
        st.write(f"**Authenticated:** {st.session_state.get('authenticated', False)}")
        st.write(f"**Username:** {st.session_state.get('username', 'None')}")
        st.write(f"**User Name:** {st.session_state.get('user_name', 'None')}")
        st.write(f"**User Role:** {st.session_state.get('user_role', 'None')}")

    with col2:
        st.subheader("Session Info")
        st.write(f"**Shared Session ID:** {st.session_state.get('shared_session_id', 'None')}")
        st.write(f"**Subscription Tier:** {st.session_state.get('subscription_tier', 'None')}")
        st.write(f"**Auth Checked:** {st.session_state.get('auth_checked', False)}")

    # 2. Query Parameters
    st.header("2. Query Parameters")
    query_params = st.query_params
    if query_params:
        st.json(dict(query_params))
    else:
        st.info("No query parameters in URL")

    # 3. Cookies
    st.header("3. Cookies")
    try:
        import extra_streamlit_components as stx
        cookie_manager = stx.CookieManager()
        cookies = cookie_manager.get_all()

        if cookies:
            st.json(cookies)
            if 'xtuff_session_id' in cookies:
                st.success(f"✅ SSO Cookie found: {cookies['xtuff_session_id'][:20]}...")
            else:
                st.warning("⚠️ SSO Cookie 'xtuff_session_id' not found")
        else:
            st.warning("⚠️ No cookies available (async loading or none set)")
    except Exception as e:
        st.error(f"Cookie manager error: {e}")

    # 4. Database Sessions
    st.header("4. Active Sessions in Database")

    try:
        conn = sqlite3.connect(SHARED_AUTH_DB)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_id, username, user_name, user_role,
                   created_at, last_accessed, expires_at
            FROM active_sessions
            ORDER BY created_at DESC
            LIMIT 5
        """)

        sessions = cursor.fetchall()
        conn.close()

        if sessions:
            for session in sessions:
                session_id, username, user_name, user_role, created, accessed, expires = session

                # Check if expired
                is_expired = datetime.fromisoformat(expires) < datetime.now()
                is_current = session_id == st.session_state.get('shared_session_id')

                status = "🟢 CURRENT" if is_current else ("🔴 EXPIRED" if is_expired else "🟡 ACTIVE")

                with st.expander(f"{status} {username} ({user_name}) - {session_id[:20]}..."):
                    st.write(f"**Session ID:** `{session_id}`")
                    st.write(f"**Username:** {username}")
                    st.write(f"**User Name:** {user_name}")
                    st.write(f"**Role:** {user_role}")
                    st.write(f"**Created:** {created}")
                    st.write(f"**Last Accessed:** {accessed}")
                    st.write(f"**Expires:** {expires}")
                    st.write(f"**Status:** {'Expired' if is_expired else 'Valid'}")

                    # Test button
                    if st.button(f"Test this session", key=f"test_{session_id[:8]}"):
                        st.query_params['session_id'] = session_id
                        st.rerun()
        else:
            st.info("No active sessions in database")

    except Exception as e:
        st.error(f"Database error: {e}")

    # 5. URL Test
    st.header("5. Manual Session Test")

    st.write("Copy this URL to test SSO with the most recent session:")

    if sessions and len(sessions) > 0:
        latest_session_id = sessions[0][0]
        test_url = f"http://localhost:{st.get_option('server.port')}?session_id={latest_session_id}"
        st.code(test_url)

        if st.button("Load this session"):
            st.query_params['session_id'] = latest_session_id
            st.rerun()

    # 6. All Session State Keys
    st.header("6. All Session State Keys")
    with st.expander("View all session state"):
        session_dict = {}
        for key in st.session_state.keys():
            try:
                value = st.session_state[key]
                # Convert to string if not JSON serializable
                try:
                    json.dumps(value)
                    session_dict[key] = value
                except:
                    session_dict[key] = str(value)
            except:
                session_dict[key] = "<unable to access>"

        st.json(session_dict)

    # 7. Session State Persistence Test
    st.header("7. Session State Persistence Test")

    st.write("**How SSO should work:**")
    st.write("1. ✅ Initial navigation with `?session_id=...` loads session into `st.session_state`")
    st.write("2. ✅ Session persists in `st.session_state` across page reloads in same browser tab")
    st.write("3. ❌ Cookies are NOT reliable in Streamlit (async loading issues)")
    st.write("")

    if 'page_load_count' not in st.session_state:
        st.session_state.page_load_count = 1
    else:
        st.session_state.page_load_count += 1

    st.write(f"**Page loads this session:** {st.session_state.page_load_count}")

    if st.session_state.get('shared_session_id'):
        if st.session_state.page_load_count > 1:
            st.success(f"✅ Session persisted across {st.session_state.page_load_count} page loads!")
        else:
            st.info("🔄 Reload this page to test session persistence")

    # 8. Recommended Actions
    st.header("8. Diagnostic Summary & Recommendations")

    issues = []

    if not st.session_state.get('authenticated'):
        issues.append("❌ Not authenticated")

    if not st.session_state.get('shared_session_id'):
        issues.append("❌ No shared_session_id in session state")

    if not query_params and not st.session_state.get('shared_session_id'):
        issues.append("⚠️ No query params and no session in state - need initial session_id URL")

    if issues:
        st.error("**Issues Found:**")
        for issue in issues:
            st.write(issue)

        st.write("**Possible causes:**")
        st.write("1. User is not logged in at All Applications Runner")
        st.write("2. Session expired or was cleared")
        st.write("3. Query params not being passed in initial URL")
        st.write("4. Session not persisting in st.session_state (check logs)")
    else:
        st.success("✅ SSO appears to be working correctly")


if __name__ == "__main__":
    show_sso_diagnostics()
