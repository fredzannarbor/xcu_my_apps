
import streamlit as st
from utilities_daily_engine import get_creative_accomplishments, save_creative_accomplishments

def render_creative_ui(creative_areas):
    """Renders the creative pipeline UI."""
    st.header("🎨 Creative Pipeline")

    with st.expander("✨ Today's Creative Accomplishments", expanded=True):
        if creative_areas:
            # Load existing creative accomplishments
            existing_creative = get_creative_accomplishments()

            creative_accomplishments = {}
            areas_with_content = 0

            for area in creative_areas:
                accomplishment = st.text_area(
                    f"**{area}:**",
                    value=existing_creative.get(area, ""),
                    height=68,
                    key=f"creative_{area}",
                    placeholder="What did you accomplish in this area today?"
                )
                creative_accomplishments[area] = accomplishment
                if accomplishment.strip():
                    areas_with_content += 1

            # Save button and progress
            col_save, col_progress = st.columns([1, 2])
            with col_save:
                if st.button("💾 Save Creative Work", type="primary"):
                    save_creative_accomplishments(creative_accomplishments)
                    st.success("Saved!")

            with col_progress:
                if areas_with_content > 0:
                    creative_rate = areas_with_content / len(creative_areas) * 100
                    st.progress(creative_rate / 100)
                    st.write(f"Areas active: {areas_with_content}/{len(creative_areas)}")
        else:
            st.info("No creative areas configured")

    # Creative insights
    with st.expander("💡 Creative Insights", expanded=False):
        st.write("**This Week's Focus Areas:**")
        st.write("• Review and prioritize based on energy level")
        st.write("• Connect creative work to revenue opportunities")
        st.write("• Build on yesterday's accomplishments")
