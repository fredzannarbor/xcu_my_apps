"""
Streamlit UI components for the Trillions of People web interface.
"""

import csv
import random
import datetime
from typing import Dict, Callable, Optional

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import fitz

from ..core.logging_config import get_logger
from ..modules.people_utilities import PeopleManager
from .utils import create_api_key_manager, show_current_version

logger = get_logger(__name__)


def render_sidebar(people_manager: PeopleManager):
    """Render the application sidebar."""
    with st.sidebar:
        # API Key Management
        api_key_manager = create_api_key_manager()
        st.session_state.openai_key = api_key_manager.enter_api_key("openai")

        # Contact and version info
        st.sidebar.write(
            "This project needs beta users, demographers, futurists, historians, "
            "anthropologists, coders, GIS specialists, designers, data providers, "
            "sponsors, and investors! Please contact me at "
            "[fredz@trillionsofpeople.info](mailto:fredz@trillionsofpeople.info). "
            "--Fred Zimmerman, Founder"
        )

        st.sidebar.markdown("**Version Information**")
        version_info = show_current_version()
        st.sidebar.write(version_info)

        # Social sharing
        two_column = st.sidebar.columns([1, 1])
        two_column[0].write("Spread the word!")
        with two_column[1]:
            components.html("""
                <a href="https://twitter.com/share?ref_src=twsrc%5Etfw" class="twitter-share-button"
                data-text="Share TrillionsOfPeople.info🎈"
                data-url="https://trillionsofpeople.info"
                data-show-count="false"
                data-size="Large"
                data-hashtags="streamlit,python">
                Tweet
                </a>
                <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
            """)


def render_about_section():
    """Render the about section."""
    with st.expander("About", expanded=False):
        st.write("""
The best available estimate is that about 117 billion unique humans have ever lived on Earth.
[(Population Reference Bureau, 2021).](https://www.prb.org/articles/how-many-people-have-ever-lived-on-earth/)
With new people being born at rate of about 133 million/year, this number is expected to rise to 121 billion by 2050,
about 129 billion by 2100, and, trends continuing, 250 billion by the year 3000 CE and one trillion by the year 9000 CE.
An optimist may hope that eventually there will be trillions of human lives. The numbers become even larger when you
add mythic and fictional characters, who have been born and died thousands of times, and have some of the most
interesting stories.

Sadly, the details of most of those lives are lost in the shadows of past and future. Many millenia of human history
are shrouded in near-complete mystery. (Graeber 2021). WikiBio dataset derived from Wikipedia's "biographical persons"
category has about 784,000 records; but only 200 of those are deemed "core biographies" by the WikiBio team and given
top-tier treatment. (WikiBio 2021)

This focus on a small percentage of all lives has important practical implications. Our understanding of lives in the
past is mostly limited to those few persons for whom we have written records or concrete artifacts; most are mysteries
--names, skeletons, or less. Similarly, one of the major difficulties in implementing far-sighted energy and climate
policies is that future people are abstractions.

_Trillions_ is a tool to make both past and futures feel more real, using state-of-the-art scientific, historical,
and artificial intelligence techniques. You, as an individual, can explore the lives of real-seeming people--past,
present, or future--in small numbers or large--and connect them with your personal story. You, as an organizational
leader, can quickly create and iterate through and personas that will give new energy and focus to your organization's
forward-looking vision.
        """)


def render_browse_section(people_manager: PeopleManager):
    """Render the browse people section."""
    with st.expander("Browse People", expanded=True):
        st.subheader("Browse People")
        st.write('This section contains historical, fictional, and synthetic personas.')

        try:
            people_df = people_manager.browse_people()

            if not people_df.empty:
                # Remove sensitive/internal columns for display
                display_columns = [col for col in people_df.columns if col != 'invisible_comments']
                display_df = people_df[display_columns]

                # Configure date columns
                column_config = {}
                if 'born' in display_df.columns:
                    column_config['born'] = st.column_config.DateColumn(
                        "Born",
                        format="YYYY",
                        step=1,
                    )

                st.dataframe(display_df, column_config=column_config)
                st.caption(
                    "Note this is a work in progress. There are some weird characters in the string data, "
                    "sorting by year doesn't work right, and there are some other issues. I am working on them. "
                    "For more information, see the [Data Dictionary](/Data_Dictionary)."
                )
            else:
                st.info("No people data found. Generate some personas using the form below!")

        except Exception as e:
            logger.error(f"Error in browse section: {e}")
            st.error(f"Error loading people data: {e}")


def render_cards_section(people_manager: PeopleManager):
    """Render the people cards section."""
    with st.expander("People Cards", expanded=True):
        st.write("""
A moment's thought will reveal that there could be an almost infinitely complex data object
to describe each of the 117 billion people who have ever lived, not to mention all the other
relevant things that could be modeled as part of a complete simulation--their history, the
relationships among people, geography, climate, and on and on. So my approach of 'one row for
every person' is a drastic simplification and a major compromise. But it is a start.
        """)

        try:
            people_df = people_manager.browse_people()

            if not people_df.empty:
                # Select random person for display
                random_person = people_df.sample(n=1).iloc[0]

                # Create display card
                card_container = st.container()
                with card_container:
                    display_fields = [
                        ("Name", "name"),
                        ("Age", "age"),
                        ("Gender", "gender"),
                        ("Born", "born"),
                        ("Country", "country"),
                        ("Occupation", "occupation"),
                        ("Family", "family_situation"),
                        ("Education", "education"),
                        ("Economic Status", "economic_status"),
                        ("Personality", "personality_traits"),
                        ("Life Challenges", "life_challenges"),
                        ("Cultural Background", "cultural_background"),
                    ]

                    card_data = []
                    for label, field in display_fields:
                        value = random_person.get(field, "Unknown")
                        card_data.append({"Attribute": label, "Value": str(value)})

                    card_df = pd.DataFrame(card_data)
                    st.write(card_df.to_html(escape=False, index=False), unsafe_allow_html=True)

                st.caption(
                    "Note this is a work in progress. Some cards have data issues. I am working on them. "
                    "For more information, see the [Data Dictionary](/Data_Dictionary)."
                )
            else:
                st.info("No people data available for cards.")

        except Exception as e:
            logger.error(f"Error in cards section: {e}")
            st.error(f"Error creating people card: {e}")


def render_generation_section(
    people_manager: PeopleManager,
    countries: Dict[str, str],
    submit_guard: Callable[[], str]
):
    """Render the people generation section."""
    with st.expander("Create People From Any Era", expanded=True):
        with st.form("persona_generation_form"):
            # Year input
            year = st.number_input(
                'Specify birth year as a positive value in the Common Era or a negative value in the period Before Common Era.',
                min_value=-233000,
                max_value=100000,
                value=2100,
                step=100,
                help='The year 700 BCE is -700, the year 2100 CE is 2100.'
            )

            # Get era description
            target_year, info_message = _get_target_year_info(year)
            st.info(info_message)

            # Country selection
            selected_country = st.selectbox(
                'Select a country.',
                list(countries.keys()),
                index=0,
                help="Select a country from the list or choose Random to generate a random country."
            )

            selected_country_code = countries[selected_country]
            display_country = selected_country

            if selected_country == 'Random':
                actual_country = random.choice([k for k in countries.keys() if k != 'Random'])
                info_message += f' Randomly chosen location: what is today {actual_country}.'
                selected_country_code = countries[actual_country]
                display_country = actual_country
            else:
                info_message += f' Country is {selected_country}.'

            # Number of people
            count = int(st.number_input(
                'How many people do you want to generate?',
                value=1,
                min_value=1,
                max_value=5,
                step=1,
                help='Processing time is linear with the number of people generated.'
            ))

            submitted = st.form_submit_button("Generate Personas")

            if submitted:
                try:
                    # Validate API key
                    api_key = submit_guard()

                    st.info(info_message)

                    # Generate personas
                    with st.spinner("Generating personas..."):
                        people_df, card_df = people_manager.create_new_people(
                            country=display_country,
                            country_code=selected_country_code,
                            count=count,
                            target_year=target_year,
                            latitude=0.0,  # Could be enhanced with geo-coding
                            longitude=0.0,
                            nearest_city="Unknown",
                            birth_year=year,
                            api_key=api_key
                        )

                    if not people_df.empty:
                        # Save to backup
                        people_manager.save_people(people_df, backup=True)

                        # Display results
                        if not card_df.empty:
                            st.success(f"Successfully generated {len(people_df)} persona(s)!")
                            st.write(card_df.to_html(escape=False, index=False), unsafe_allow_html=True)

                            # Generate PDF card (optional feature)
                            _generate_pdf_card(card_df)
                        else:
                            st.error("Backend problem, no people created.")
                    else:
                        st.error("Failed to generate personas. Please check your API key and try again.")

                except Exception as e:
                    logger.error(f"Error in generation: {e}")
                    st.error(f"Error generating personas: {e}")


def render_upload_section(people_manager: PeopleManager):
    """Render the file upload section."""
    with st.expander("Submit People for Inclusion"):
        st.download_button(
            "Download Sample File",
            "resources/sample_upload_file.csv",
            "Persona creation template."
        )

        st.markdown("""
Download this template if you want to upload your own personas for creation or direct ingestion.
The template does not use all the fields in the data dictionary. Ingestion is human-mediated and
requires admin approval. Missing fields will be generated automatically. For more information about
the file format, see the [Data Dictionary](/Data_Dictionary) page.
        """)

        st.divider()

        uploaded_file = st.file_uploader(
            "Upload a CSV file with data to add to the database.",
            type=["csv"]
        )

        if uploaded_file is not None:
            try:
                st.success(f"File {uploaded_file.name} uploaded.")
                submit_df = pd.read_csv(uploaded_file)
                revised_df = st.data_editor(submit_df)

                if st.button("Submit for Review"):
                    # Save uploaded data
                    people_manager.save_people(revised_df, backup=True)
                    st.success("Data submitted for admin review.")

                    # Log submission
                    api_key = st.session_state.get('openai_key', 'unknown')
                    logger.info(f"New data submitted by user with API key: {api_key[:10]}...")

            except Exception as e:
                logger.error(f"Error processing upload: {e}")
                st.error(f"Error processing uploaded file: {e}")


def _get_target_year_info(year: int) -> tuple[int, str]:
    """Get target year and informational message."""
    if year < 0:
        target_year = abs(year)
        info_message = f'Year of birth is {target_year} BCE.'
    elif year == 0:
        target_year = 1
        info_message = 'Year of birth is 1 CE.'
    else:
        target_year = year
        info_message = f'Year of birth is {year} CE.'

    return target_year, info_message


def _generate_pdf_card(card_df: pd.DataFrame):
    """Generate PDF version of persona card (optional feature)."""
    try:
        # Convert to HTML
        html_content = card_df.to_html(escape=False, index=False)

        # Create temporary HTML file
        html_file = "temp_card.html"
        with open(html_file, 'w') as f:
            f.write(html_content)

        # Convert to PDF using PyMuPDF
        html_doc = fitz.open(html_file)
        pdf_bytes = html_doc.convert_to_pdf()
        pdf_doc = fitz.open("pdf", pdf_bytes)

        # Save PDF
        pdf_file = "persona_card.pdf"
        pdf_doc.save(pdf_file)

        # Cleanup
        html_doc.close()
        pdf_doc.close()

        # Provide download button
        with open(pdf_file, 'rb') as f:
            st.download_button(
                "Download PDF Card",
                f.read(),
                file_name="persona_card.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        logger.warning(f"PDF generation failed: {e}")
        # PDF generation is optional, so we don't show error to user