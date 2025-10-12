import streamlit as st

data_dictionary = {
    "shortname": "Short names are programmatically created and intended to be as culture- and gender-agnostic as possible.",
    "image": "Currently provided via FakeFace API; it's understood that the images are not necessarily very consistent with the other biographical information for the persona. Future versions of this service will include a more robust image generation service.",
    "year_of_birth_in_CE": "Year of birth in the Common Era, negative values are BCE, positive values are CE.",
    "gender": "Gender is assigned programmatically as socially constructed during the individual's lifetime and consistent with self-chosen preferences. Child-bearing capacity, important for demographic models, will be addressed separately in future development.",
    "species": "At least four hominin species inhabited Earth during our time window of 233,000 BCE to 10,000 CE: 'sapiens', 'neanderthalensis', 'denisovan', 'floresiensis' (Vidal 2022). It is possible that there will be new species or species-like entities in the future, such as AIs or cyborgs.",
    "timeline": "The database allows for representing persons possibly found in alternate timelines.",
    "realness": "Types of realness include 'synthetic', 'historic', 'documented' and 'fictional.'",
    "latitude": "Self-explanatory.",
    "longitude": "Self-explanatory.",
    "nearest_city": "Nearest present-day city.",
    "backstory": "Created by a language model in response to a prompt written by Fred Zimmerman.",
    "thisperson4name": "Four words that provide a unique identifier for well in excess of a trillion persons.",
    "comments": "Free text; may be from any source including _Trillions_, data provider, or users.",
    "source": "The organization that provided the definition for the persona.",
    "status": "Registration allows users to add newly created persons to the permanent database. Editing enables users to recommend or request changes to personas. And claiming allows users to 'own' a historic, synthetic or (public domain) fictional persona connected to non-fungible tokens (NFTs), i.e. collectible cards authenticated via the blockchain."
}

st.markdown("## Data Dictionary")
st.write(data_dictionary)

