import streamlit as st
import pandas as pd
import argparse
import random
from app.utilities.utilities import statcounter

# Import the required dependencies
try:
    from trillionsofpeople import peopledf_columns, countries
    from classes.SyntheticPeople.ScenarioUtilities import create_scenario_personas
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    st.warning(f"Some dependencies are missing: {e}")
    DEPENDENCIES_AVAILABLE = False

if __name__ == "__main__":
    argparser = argparse.Parser

st.subheader('Explore Scenarios')

st.markdown(
    """ You can choose from a variety of scenarios to explore. The first set of [scenarios](https://www.dni.gov/index.php/gt2040-home/scenarios-for-2040) is drawn from the Office of the Director of National Intelligence's _Global Trends 2040_ (ODNI 2021), a planning and visioning exercise that the US Intelligence conducts every five years. The next set will be drawn from the IPCC's Representative Concentration Scenarios, which chart possible GHG futures for the year 2100.  In future, you will be able to submit scenarios to the project yourself.""")

with st.form("Scenario Explorer"):
    scenario_list = ['GlobalTrends2040RD', 'GlobalTrends2040AWA', 'GlobalTrends2040CC', 'GlobalTrends2040SS',
                     'GlobalTrends2040SSpb', 'GlobalTrends2040TM']
    scenario_dict = {}
    if scenario_list:
        st.write(scenario_list)
        scenario_dict = construct_preset_dict_for_UI_object(scenario_list)
    scenario_selected = st.selectbox('Choose a scenario', scenario_list, index=0,
                                     format_func=lambda x: scenario_dict.get(x))

    selected_presetdf = presets_parser(scenario_selected)[0]

    scenario_name = selected_presetdf['preset_name'].iloc[0]
    n = st.slider("Select number of personas to build", 1, 5, value=1,
                  help="To build larger numbers of personas, contact Fred Zimmerman.")
    submitted = st.form_submit_button('Create Scenario Personas')
    scenario_row_values, show_personas = [], []

    # Handle countries_list safely
    try:
        random_country = random.choice(countries_list)
    except NameError:
        # Fallback if countries_list is not defined
        try:
            random_country = random.choice(list(countries.keys()))
        except:
            random_country = "United States"  # Default fallback

    if submitted:
        infomessage = f"Creating {n} personas for {scenario_name}."
        st.info(infomessage)

        if not DEPENDENCIES_AVAILABLE:
            st.error("Required dependencies are not available. Please check your imports.")
        elif scenario_selected:
            try:
                # Updated function call with required parameters
                scenario_personas_df, card_df = create_scenario_personas(
                    scenario_selected,
                    n,  # Use the actual n value from the slider
                    2040,
                    random_country,
                    peopledf_columns,
                    countries
                )

                if not card_df.empty:
                    html = card_df.to_html(escape=False).replace("\\n", "<p>")
                    st.write(html, unsafe_allow_html=True)

                    # Only call html2jpg if the function is available
                    try:
                        html2jpg(html, "card.jpg")
                    except NameError:
                        st.warning("html2jpg function not available - image generation skipped")
                else:
                    st.warning("No personas were generated. Please try again.")

            except Exception as e:
                st.error(f"Error creating personas: {str(e)}")
                st.error("Backend problem creating personas, contact Fred Zimmerman for help.")
        else:
            st.error("Please select a scenario.")