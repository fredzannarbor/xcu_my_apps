

import streamlit as st
from utilities_daily_engine import get_revenue_activities_text, save_revenue_activities

def render_revenue_ui(micro_tasks):
    """Renders the action focus UI (micro-tasks only)."""
    st.header("💰 Action Focus")

    with st.expander("📋 Today's Micro-Tasks", expanded=True):
        if micro_tasks:
            completed_tasks = []
            for i, task in enumerate(micro_tasks):
                if st.checkbox(task, key=f"revenue_task_{i}"):
                    completed_tasks.append(task)

            # Show completion summary
            if completed_tasks:
                completion_rate = len(completed_tasks) / len(micro_tasks) * 100
                st.progress(completion_rate / 100)
                st.write(f"✅ Completed: {len(completed_tasks)}/{len(micro_tasks)} ({completion_rate:.0f}%)")
        else:
            st.info("No micro-tasks configured")


def render_revenue_activities_only():
    """Renders only the revenue activities section."""
    st.header("💵 Revenue Activities")
    
    # Revenue focused activities input
    existing_revenue_activities = get_revenue_activities_text()
    revenue_activities_text = st.text_area(
        "Describe your revenue-generating activities today:",
        value=existing_revenue_activities,
        height=100,
        key="revenue_activities_input",
        placeholder="e.g., Pitched new client, Sent invoices, Optimized ad campaign"
    )

    if st.button("💾 Save Revenue Activities", key="save_revenue_activities"):
        save_revenue_activities(revenue_activities_text)
        st.success("Revenue activities saved!")

    # Revenue summary for today
    with st.expander("📊 Today's Revenue Summary", expanded=False):
        st.metric("Total Revenue", "$0.00", help="Sum of all project revenues today")
        st.metric("Revenue Goal Progress", "0%", help="Progress toward daily revenue goal")
        if existing_revenue_activities:
            st.write("**Activities:**")
            st.markdown(f"- {existing_revenue_activities.replace(';', ';\n- ')}")
        else:
            st.info("No revenue activities logged yet.")

