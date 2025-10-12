'''
create class to manage user API keys in streamlit
1. User can securely enter their existing API key
2. API key persists in user's browser session.
3. User has option to persist API key across browser sessions.
4. User can securely change their API key if desired.
5. System administrator cannot view user's API key, which is encrypted.
6.  System allows the user to enter API Keys for the following services:
    - OpenAI
'''
import streamlit as st


class ManageUserAPIKeys:

    def __init__(self):
        self.openai_key = None
        self.service_name = "openai"

    def enter_api_key(self, service_name):
        # initialize streamlit session state
        if "openai_key" not in st.session_state:
            st.session_state.openai_key = None
        api_key = st.sidebar.text_input(
            "API-Key",
            placeholder="**************************",
            type="password"
        )
        if api_key:
            openai_key = api_key
            st.session_state.openai_key = openai_key
            st.info(st.session_state.openai_key)
        if not api_key and not st.session_state.openai_key:
            st.sidebar.warning(
                "Enter your OpenAI api key. You can find it [here](https://platform.openai.com/account/api-keys).\n")
        return api_key
    