import streamlit as st

st.subheader('Explore Scenarios')

st.markdown("""You can choose from a variety of scenarios to explore. The first set of scenarios is drawn from the Office of the Director of National Intelligence's Global Trends 2040 (ODNI 2021), a planning and visioning exercise that the US Intelligence conducts every five years. The next set will be drawn from the IPCC's Representative Concentration Scenarios, which chart possible GHG futures for the year 2100. In future, you will be able to submit scenarios to the project yourself.""")

st.info("⚠️ Scenario generation is currently disabled in static mode. This feature requires API integration.")

with st.expander("Available Scenarios", expanded=True):
    scenarios = {
        "GlobalTrends2040RD": "Renaissance of Democracies",
        "GlobalTrends2040AWA": "A World Adrift",
        "GlobalTrends2040CC": "Competitive Coexistence",
        "GlobalTrends2040SS": "Separate Silos",
        "GlobalTrends2040SSpb": "Separate Silos - Pushback",
        "GlobalTrends2040TM": "Tragedy and Mobilization"
    }

    for code, description in scenarios.items():
        st.write(f"**{code}**: {description}")

st.markdown("**Coming Soon**: Interactive scenario persona generation with full API integration.")
