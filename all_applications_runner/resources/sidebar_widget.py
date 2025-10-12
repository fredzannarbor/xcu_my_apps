#!/usr/bin/env python3
"""
Reusable sidebar widget for returning to xtuff.ai dashboard

Copy this file or this code into your individual apps to add a consistent
"Return to xtuff.ai" button at the top of every sidebar.
"""

import streamlit as st


def add_return_to_dashboard_button(
    dashboard_url: str = "http://xtuff.ai",
    button_text: str = "← Return to xtuff.ai Dashboard",
    show_divider: bool = True
):
    """
    Add a return button at the top of the sidebar.

    Args:
        dashboard_url: URL to return to (default: http://xtuff.ai)
        button_text: Text to display on the button
        show_divider: Whether to show a divider line after the button

    Usage:
        import streamlit as st
        from sidebar_widget import add_return_to_dashboard_button

        # At the top of your app, before other sidebar content
        add_return_to_dashboard_button()
    """
    # Create button that opens link in same tab
    if st.sidebar.button(button_text, type="secondary", use_container_width=True):
        st.markdown(f'<meta http-equiv="refresh" content="0; url={dashboard_url}">', unsafe_allow_html=True)

    # Alternative: Use markdown link (opens in same tab)
    # st.sidebar.markdown(f'<a href="{dashboard_url}" style="text-decoration: none;"><button style="width: 100%; padding: 0.5rem; background-color: #f0f2f6; border: 1px solid #ddd; border-radius: 0.25rem; cursor: pointer;">← Return to xtuff.ai Dashboard</button></a>', unsafe_allow_html=True)

    if show_divider:
        st.sidebar.markdown("---")


def add_return_link(
    dashboard_url: str = "http://xtuff.ai",
    link_text: str = "← Back to Dashboard"
):
    """
    Add a simple text link to return to dashboard (lighter weight alternative).

    Args:
        dashboard_url: URL to return to
        link_text: Text for the link
    """
    st.sidebar.markdown(f"[{link_text}]({dashboard_url})")
    st.sidebar.markdown("---")


# Example usage in an app
if __name__ == "__main__":
    st.set_page_config(page_title="Example App", layout="wide")

    # Add return button at the very top of sidebar
    add_return_to_dashboard_button()

    # Rest of your sidebar content
    st.sidebar.title("My App Sidebar")
    st.sidebar.write("Other sidebar content here...")

    # Main content
    st.title("Example Application")
    st.write("This app has a return to dashboard button in the sidebar.")
