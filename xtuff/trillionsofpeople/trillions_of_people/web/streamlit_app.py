"""Streamlit web interface for TrillionsOfPeople package."""

import streamlit as st
from ..core.config import ConfigManager
from ..core.generator import PeopleGenerator
from ..core.exceptions import TrillionsOfPeopleError


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="TrillionsOfPeople.info",
        page_icon="👥",
        layout="wide"
    )
    
    st.title('TrillionsOfPeople.info')
    st.markdown("""_One row for every person who ever lived, might have lived, or may live someday._

_**Create, edit, register, claim, share**_ stories about your fellow souls.

_A tool to explore the human story._""")
    
    # Configuration management
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # API Key management in sidebar
        with st.sidebar:
            st.header("Configuration")
            api_key = st.text_input(
                "OpenAI API Key", 
                value=config.openai_api_key or "",
                type="password",
                help="Enter your OpenAI API key for backstory generation"
            )
            if api_key:
                config.openai_api_key = api_key
        
        # Main interface
        st.header("Generate Synthetic People")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            count = st.number_input("Number of people", min_value=1, max_value=10, value=1)
        
        with col2:
            year = st.number_input("Birth year", min_value=-233000, max_value=100000, value=2100)
        
        with col3:
            country = st.selectbox("Country", ["Random", "United States", "China", "India", "Brazil"])
        
        if st.button("Generate People"):
            if not config.openai_api_key:
                st.error("Please enter your OpenAI API key in the sidebar.")
            else:
                try:
                    with st.spinner("Generating people..."):
                        generator = PeopleGenerator(config)
                        people = generator.generate_people(count, year, country)
                    
                    st.success(f"Generated {len(people)} people!")
                    
                    # Display results
                    for i, person in enumerate(people, 1):
                        with st.expander(f"Person {i}: {person.name}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Birth Year:** {person.birth_year}")
                                st.write(f"**Gender:** {person.gender}")
                                st.write(f"**Country:** {person.country}")
                                st.write(f"**Species:** {person.species}")
                            with col2:
                                st.write(f"**Timeline:** {person.timeline}")
                                st.write(f"**Realness:** {person.realness}")
                                if person.nearest_city:
                                    st.write(f"**Nearest City:** {person.nearest_city}")
                            if person.backstory:
                                st.write(f"**Backstory:** {person.backstory}")
                
                except TrillionsOfPeopleError as e:
                    st.error(f"Error generating people: {e}")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
    
    except Exception as e:
        st.error(f"Configuration error: {e}")


if __name__ == "__main__":
    main()