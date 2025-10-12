import json
import os
from uuid import uuid4

import pandas as pd
import streamlit as st

import app.ManageUserAPIKeys as appmgr
from app.utilities.gpt3complete import presets_parser
from app.utilities.utilities import (
    read_markdown_file,
    get_version_as_dict, submit_guard)
from classes.BookSeries import BookSeries
from classes.BookSeries.CreateSeries import save_cumulative_idea_results
from classes.Ideas.IdeaAnalysis.IdeaThemesAnalyzer import IdeaAnalysis
from classes.Ideas.IdeaUtilities import IdeaUtilityFunctions as iuf
from classes.SyntheticReaders.RatingUtilities import rate_ideas
# from ideas.SyntheticReaders import Reader, ReaderPanels as rp, RatingUtilities as cu
from classes.SyntheticReaders.ReaderPanels import ReaderPanels

api_key_manager = appmgr.ManageUserAPIKeys()


def check_spreadsheet_filetype(uploaded_file):
    global ideas_df
    if uploaded_file.type == "text/csv":
        ideas_df = pd.read_csv(uploaded_file)
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
st.title("Idea Forge")

tab1, tab2, tab3, tab4 = st.tabs(["Expand Ideas", "Evaluate Ideas", "Book Series", "Build Out Ideas"])

with tab1:
    with st.form(key='eeideas'):
        st.info(
            "Here you will pour the Promethean fire of your personal creativity into a cauldron of AI-assisted imagination. The strongest and best ideas will emerge to be shaped, tempered, and honed to a razor's edge by Nimble's AI Reader Panels.")
        uploaded_file = st.file_uploader("Upload a file of ideas to explore and elaborate", type=['xlsx', 'csv', 'txt'])
        st.form_submit_button(label='Upload')
        newideas_df = pd.DataFrame()
        if uploaded_file is None:
            st.error("You must upload a file to proceed.")
        else:
            check_spreadsheet_filetype(uploaded_file)
            edited_df = st.data_editor(ideas_df, num_rows="dynamic")
            # move uploaded file to working directory
            file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type,
                            "FileSize": uploaded_file.size}
            st.info(file_details)
            col1, col2 = st.columns(2)
            num_ideas = col1.radio("Number of expansions per idea row in the dataframe", ["1", "5", "10", "20", "100"],
                                   index=0)
            num_ideas = int(num_ideas)
            preset_expand_this_book = col2.selectbox(
                options=["BookIdeaSimpleVariation", "BookIdeaExpander", "BookIdeaDramatic", "BookIdeaMajorTwist",
                         "BookIdeaRebootViaPremises"], index=0, label="Choose a strategy for expanding these ideas")
            expand = st.form_submit_button(label='Expand ideas')
            if expand:
                submit_guard()
                edited_df.to_excel("edited_ideas.xlsx")
                st.success(
                    "Any changes you made to the ideas dataframe have been saved to edited_ideas.xlsx.  Now ready to expand these ideas.")
                preset_instruction = "Instructions: " + presets_parser(preset_expand_this_book)[7]
                # st.info(preset_instruction)
                with st.spinner("Expanding ideas..."):
                    iuf_instance = iuf()
                    newideas_df = iuf_instance.ideas2moreideas(edited_df, preset_expand_this_book,
                                                               model="gpt-3.5-turbo", num_expansions=num_ideas)
                    st.success("Ideas expanded.")
                    # tweakedideas = st.dataframe(newideas_df)
                    newideas_df.to_excel("newideas.xlsx")
                    st.success("New ideas saved to newideas.xlsx.")
    if not newideas_df.empty:
        ideafilename = "resources/ideas/newideas_" + str(uuid4())[:6] + ".csv"
        button = st.download_button(label="Download new ideas", data=newideas_df.to_csv(), file_name=ideafilename,
                                    mime="text/csv")
        if button:
            st.success("New ideas downloaded, check your Downloads folder.")
        else:
            st.info("Click the button to download the new ideas.")

    with st.expander("Experimental Idea Analysis", expanded=False):
        if os.path.exists("resources/ideas/Reader_Panel_idea_results.csv"):
            analysis = IdeaAnalysis("resources/ideas/Reader_Panel_idea_results.csv")
            analysis.display_analysis(10, 20)
        else:
            st.warning("You must first evaluate ideas using the Reader Panels before you can analyze them.")

with tab2:
    st.write("On this page, you can explore how different Readers react to book ideas.")
    with st.expander("About Synthetic Readers", expanded=True):
        st.markdown(
            """Synthetic Readers are AI and LLM-powered agents whose job is to simulate an individual human's experience reading a book.  They are designed to be used by authors, publishers, and readers to help them understand what makes a book work, and what makes it fail. They arrive at their recommendations by evaluating a book three ways: page by page, cumulatively, and globally.  Further details are available on the documentation pages.""")
        st.markdown(
            """Each Reader has a unique set of preferences and there are thousands of them.  On this page, you can use preconfigured Reader Panels to explore the different ways Readers experience ideas.""")

    with st.expander("Choose a Reader Panel", expanded=True):
        rp_instance = ReaderPanels()  # Assuming you wanted to create an instance of ReaderPanels
        panel_df = rp_instance.user_interface()

    with st.expander("Submit Ideas", expanded=True):
        with st.form(key='ideas dataframe'):
            st.markdown("""Here, you can submit idea to the Reader Panels for evaluation.""")
            st.markdown(
                """The Reader Panels will evaluate your ideas one at time return a dataframe of results. In this initial version, each paragraph is evaluated on its own merits. In future, a paragraph will be evaluated in the context of the entire preceding content.""")
            uploaded_file = st.file_uploader("Upload csv, spreadsheet, or text file", type=["csv", "xlsx", "txt"])
            submit_button = st.form_submit_button("Upload Ideas", on_click=None, help=None)
            if uploaded_file is not None:
                check_spreadsheet_filetype(uploaded_file)

                # move uploaded file to working directory
                file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type,
                                "FileSize": uploaded_file.size}
                st.info(file_details)
            else:
                st.error("You must upload a file to proceed.")

    with st.expander("Evaluate the Ideas", expanded=True):
        results_df = pd.DataFrame()
        with st.form(key='submit to readers'):
            n_rows = st.radio("Number of rows to evaluate", [5, "all"], index=0)
            submitted = st.form_submit_button("Send To Readers")
            submit_guard = st.empty()
            if submitted:
                if n_rows == "all":
                    n_rows = ideas_df.shape[0]
                results_df = rate_ideas(ideas_df, panel_df, "EvaluateIdea", n_rows)
                st.success(f"Completed evaluation of {results_df.shape[0]} ideas.")

                filename = "Reader_Panel_results_" + str(uuid4())[:6] + ".csv"
        if results_df.shape[0] > 0:
            st.dataframe(results_df)
            st.download_button("Download results", results_df.to_csv(), "Reader_Panel_results.csv", "text/csv",
                               key="download1")
            jobid = str(uuid4())[:6]
            results_df.to_json("resources/ideas/Reader_panel_idea_results" + jobid + ".json", orient="records")
            results_df.to_csv("resources/ideas/Reader_Panel_idea_results" + jobid + ".csv")

with tab3:
    with st.expander("About book series", expanded=True):
        st.markdown(
            "Series are books that are explicitly connected to each other, either by high similarity of title and topic, or because they are published in a specific order.")
        st.markdown(
            "The main thing to know is that *series sell*. A useful proof point is to observe that over the years Amazon has inexorably increased the visibility of series, to the point where they are now the dominant way that books are sold online. If you are a reader, you are likely to crave the familiarity of a series. If you are an author, you should probably think long and hard before writing a book that is not part of a series. If you are a publisher, you are likely to discourage your authors from writing one-offs. And if you are a bookseller, you are likely to give series a lot of visibility.")

        st.write(
            "This tool will help you create lots of ideas for book series.  You can then sift through these ideas to find the ones that are most interesting to you, or submit them to one of Nimble's Reader Panels.")


        def submit_guard():
            if "openai_key" not in st.session_state:
                st.session_state.openai_key = None
            if st.session_state.openai_key == "" or st.session_state.openai_key is None:
                st.error("Before submitting a request, you must enter an API key for OpenAI in the sidebar.")
                st.stop()
            return


        with st.form("series_info"):
            reboot = st.radio("Reboot?", [True, False], index=1)
            franchise = st.radio("Franchise?", [True, False], index=1)
            series_description = st.text_area("Series Description",
                                              "Kids complain about things that separate them from their parents.")
            if reboot:
                whatsbeingrebooted = st.text_input("Name/Short Description of Series Being Rebooted", "Harry Potter")
                reboot_prefix = "Reboot of " + whatsbeingrebooted + ". "
                st.info("The reboot begins with the description of the original series.")
            if franchise:
                min_formulaicness = 0.7
                st.info("Franchises must be quite formulaic.")
            else:
                min_formulaicness = 0.0
            random_genre = "snarky children's stories"
            genre = st.text_input("Genre", random_genre)
            word_count = st.text_input("Word Count", 500)
            audience = st.text_input("Audience", "children")
            formulaicness = st.slider("Formulaicness", min_formulaicness, 1.0, 0.7, 0.05)
            if formulaicness == 0:
                formulaic = "Not at all"
            elif formulaicness < 0.25:
                formulaic = "Not very"
            elif formulaicness < 0.5:
                formulaic = "Somewhat"
            elif formulaicness < 0.7:
                formulaic = "Quite"
            elif formulaicness < 0.9:
                formulaic = "Highly"
            elif formulaicness == 1:
                formulaic = "Completely"
            else:
                formulaicness == 0.7
                formulaic = "Quite"
                st.caption(
                    "How closely the series will adhere to a formula. 0.0 means not at all, 1.0 means completely.")
            number_of_titles = st.number_input("Number of Titles", 2, 100, 12, 1)

            submitted = st.form_submit_button("Create Series")
            if submitted:
                submit_guard()
                title_requirements_prompt = f" Words: {word_count}. Genre: {genre}. Audience: {audience}. {formulaic} formulaic."

                description = series_description + title_requirements_prompt
                infomessage = "You asked for series ideas fitting the following parameters: \n" + description
                st.info(infomessage)
                bs = BookSeries()
                with st.spinner("Generating ideas..."):
                    ideas_result = bs.get_ideas(description=description, model="gpt-3.5-turbo")
                st.write(ideas_result)
                ideas_df = bs.convert_ideas_result_to_dataframe(ideas_result, series_description)
                try:
                    cumulative_ideas_df = save_cumulative_idea_results("userdocs/cumulative_ideas.csv", ideas_df, )

                except Exception as e:
                    errormessage = "Error saving ideas to cumulative ideas file. " + str(e)
                    st.error(errormessage)

                st.dataframe(ideas_df, hide_index=True)
                st.caption("The AI sometimes slips from describing series into describing titles that are part of a series. If this\
                            happens, simply resubmit the form.")
    with st.expander("Further information", expanded=False):
        st.info(
            "This is a beta feature. If you have questions, suggestions, or feedback, please contact me at the address in the sidebar.")

with tab4:
    with st.expander("Building  Out", expanded=True):
        st.markdown("This page provides tools to build out ideas into the elements of a successful book or franchise.")

    with st.expander("Extract Elements from Many Ideas"):
        st.markdown("This tool will extract elements from a large number of ideas and put them into a dataframe.")
        with st.form(key='uplofile'):
            uploaded_file = st.file_uploader("Upload csv, spreadsheet, or text file", type=["csv", "xlsx", "txt"])
            submit_button = st.form_submit_button("Upload Ideas", on_click=None, help=None)
            if uploaded_file is not None:
                check_spreadsheet_filetype(uploaded_file)
                file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type,
                                "FileSize": uploaded_file.size}
                st.info(file_details)
            else:
                st.error("You must upload a file to proceed.")
        if uploaded_file is not None:
            with st.form(key='extract elements'):

                element_types = st.multiselect("Type of element to extract",
                                               ["Named characters", "Named characters with capsule bio",
                                                "Specific physical location", "plot twists", "revelations",
                                                "character arcs", "theme", "McGuffins", "titles", "protagonists",
                                                "villains", "friends", "Cast of Characters with pithy 30s-style bios"])
                idea_rows_num = st.radio("Number of rows to extract from", [5, "all"], index=0)
                model = st.radio("model:", ["gpt-3.5-turbo", "gpt-4"], index=0,
                                 help="gpt-4 is more powerful and much more expensive.")
                submit_button = st.form_submit_button("Extract Elements", on_click=None, help=None)
                if submit_button:
                    submit_guard()
                    st.write(f"Extracting elements...\n{element_types}")
                    iuf_instance = iuf()
                    # st.write(ideas_df, [presets, element_types, idea_rows, idea_beginning_row, idea_ending_row, model)
                    if idea_rows_num == "all":
                        idea_rows_num = ideas_df.shape[0]
                    extracted_elements_df, prompt_dfs = iuf_instance.ideas2presets(ideas_df, ["ExtractElements"],
                                                                                   element_types,
                                                                                   idea_rows=idea_rows_num,
                                                                                   idea_beginning_row=0,
                                                                                   idea_ending_row=5, model=model)
                    # st.dataframe(extracted_elements_df)
                    extracted_elements_df.to_csv("resources/ideas/extracted_elements_" + str(uuid4())[:6] + ".csv")
                    st.success("Elements extracted and saved to extracted_elements.csv.")
                    st.write("You can now use the elements in this dataframe to build out your ideas.")
                    for d in prompt_dfs:
                        st.dataframe(d)
