import json
from uuid import uuid4

import classes.Codexes.Tools.DanielDefoe
import pandas as pd
import streamlit as st

import app.ManageUserAPIKeys as appmgr
from app.utilities.utilities import read_markdown_file, get_version_as_dict, save_uploaded_file

api_key_manager = appmgr.ManageUserAPIKeys()

def check_spreadsheet_filetype(uploaded_file):
    global ideas_df
    if uploaded_file.type == "text/csv":
        ideas_df = pd.read_csv(uploaded_file, header=None, index_col=0)
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        ideas_df = pd.read_excel(uploaded_file)
    elif uploaded_file.type == "text/plain":
        ideas_df = pd.read_csv(uploaded_file)
    else:
        st.error("You must upload a csv, spreadsheet, or text file to proceed.")
        return
    return ideas_df

with st.sidebar:
    st.session_state.openai_ky = api_key_manager.enter_api_key("openai")
    st.components.v1.iframe('https://fredzannarbor.substack.com/embed', width=320, height=200, scrolling=False)
    sidebar_message = read_markdown_file("resources/markdown/sidebar_message.md")
    st.sidebar.markdown(sidebar_message)
    st.sidebar.markdown("""**Operational**, no known issues""")
    version2 = json.dumps(get_version_as_dict())
    st.sidebar.json(version2)

st.title("Create and Edit Book Outlines")

tab1, tab2, tab3, tab4 = st.tabs(["... Outlines", "... Chapters", "... Scenes", "Build Full Book"])
job_id = str(uuid4())[0:8]
with tab1:
    with st.form(key='upload specs'):
        uploaded_file = st.file_uploader("Upload a book spec file", type=['xlsx', 'csv', 'txt'])
        st.form_submit_button(label='Upload')
        spec_df = pd.DataFrame()
        if uploaded_file is None:
            st.error("You must upload a file to proceed.")
        else:
            spec_df = check_spreadsheet_filetype(uploaded_file)

            # move uploaded file to working directory
            file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type,
                            "FileSize": uploaded_file.size}
            save_uploaded_file(uploaded_file, "working")


with st.form(key='create_outline'):
    create_outline_button = st.form_submit_button(label='Create Outline')
    if create_outline_button:
        ol = classes.Codexes.Tools.CodexSpecs2OutlinesAndDrafts.IdeaSpecs2Book()
        result_df = ol.main("working/" + uploaded_file.name)
        st.data_editor(result_df)


