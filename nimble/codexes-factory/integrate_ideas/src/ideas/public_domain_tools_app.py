import streamlit as st

from argparse import FileType
import csv
import os
import subprocess
import sys
import tempfile
# import sleep
import time
from io import StringIO
from pathlib import Path
from re import M, U
import createsyntheticdata
from createsyntheticdata import create_record_topics 

import docx2txt
from docx2txt.docx2txtimport process
import nltk
import pandas as pd

import pdfminer
from pdfminer import high_level
from stripe import upload_api_base

from app.utilities.gensim_summarizer import gensim_summarizer
from app.utilities.gpt3complete import (gpt3complete, post_process_text,presets_parser, get_user_id_for_username)


from docx2python import docx2python
from hydralit import HydraHeadApp

from apps import myloading_app
from apps.myloading_app import MyLoadingApp


class LongformWorkbenchApp(HydraHeadApp):

    def __init__(self, title = 'Longform Workbench', **kwargs):
        self.__dict__.update(kwargs)
        self.title = title

    def run(self):

        def save_uploaded_file(uploaded_file, user_docs_target_dir):
            with open(os.path.join(user_docs_target_dir, uploaded_file.name),"wb") as f:
                f.write(uploaded_file.getbuffer())
            success_msg = f"File {uploaded_file.name} saved successfully to " + f"{user_docs_target_dir}."
            return st.success(success_msg)

        @st.cache
        def cacheaware_summarizer(text, wordcount):
            summary = gensim_summarizer(text, wordcount)
            return summary

        def create_longform_manuscript(stages):

            # Create a temporary directory to store the manuscript
            temp_dir = tempfile.TemporaryDirectory()
            temp_dir_path = temp_dir.name

            # Create a temporary file to store the manuscript
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
            temp_file_path = temp_file.name

            idea_to_process = select_idea(text)

            # Select author persona

            # Select style

            # Create cast of characters

            # Create settings

            # Create arcs for major and minor characters with objectives and McGuffins

            # Create plot points, reversals, and rewvelations for arcs

            # Create inverse character network graph with character co-occurences by chapter

            # Loop through chapters in 








            # Front matter 
            
            # Generate introduction







            return text

        def generate_ideas(longform_preset_dict):

            idea_preset_dict = {'GenericLoglineCreator': 'Simple Logline Creator', 'StructuredLoglineCreator': 'Structured Logline Creator'}
            # idea_preset_dict = longform_preset_dict
            # need to add longform preset dicts to UI function that invokes this one
            with st.form(key='idea_gen'):
                idea_presets = st.multiselect("Select the idea generators you want to run", options=["GenericLoglineCreator","StructuredLoglineCreator"],format_func = lambda x: idea_preset_dict.get(x), help="These forms assume you are starting from scratch and looking for ideas.")
                override_post = st.text_input("Enter a few keywords or phrases providing more detail about the ideas you need.")
                st.write(override_post)
                submitted = st.form_submit_button('Generate Ideas')
            if submitted:
                for idea_preset in idea_presets:
                    result = create_record_topics(datadir, idea_preset, 20, "", override_post, "", "")
                    st.write(result[2])
                    result_list = result[2]
                    results = "\n".join(result_list)
                    st.download_button("Download These Ideas", results)


        def select_idea(idea_list):
            with st.expander("Select and refine an idea."):
                selected_idea = st.selectbox("Select an idea", idea_list)
                refined_idea = st.text_area("Refine the wording of the idea", value=selected_idea)
            return refined_idea

        
           
        # main
        

        user_access_level, username = self.check_access()
        user_id = get_user_id_for_username(username)
        datadir = 'app/userdocs/' + str(user_id)

        st.title("Longform Workbench")

    
        with st.expander("What It is"):
            st.markdown("""
                        
  
                A set of tools for creating longform novels, books, and screenplays.
                """)
                        
        with st.expander("Your Role"):
            st.markdown("""
            
                You, the human author, are the lead author. The computer is your junior co-author.
                
                You use these tools to create a draft of your work.
                
                Then, you are responsible for editing the draft and deciding when it is up to your standards of quality.
                        """)
            
        with st.expander("How it Works"):
            st.markdown("""
            
            1. Generate initial ideas for a novel, book, or screenplay.
            2. Define the structure of the document.
            3. Generate lists of key elements:
            - cast of characters
            - important locations
            - tropes, gimmicks, McGuffins, etc.
            - key moments
            - author persona
            - writing style (transfer learning)
            4. Select the elements you like; add your own.
            5. Using Nimble's proprietary model, the AI will use these elements to generate a _directed graph of element co-occurrences_. This serves as the specification for the work.  You will edit and approve the specification.
            6.  The AI will loop over the elements and generate a narrative in chunks that fall within the token generation limit of the model (currently, around 1500 words). You will download the document as a .docx file with appropriate paragraph styles already applied.
            7.  You, the human author, will edit the document, fix inconsistencies, add new content as you see fit, and decide when the result meets your standards for quality.
            8.  You may submit the the narrative to Nimble Books for publication.  If accepted, Nimble will publish in hardcover, paperback and Kindle with distribution worldwide via Amazon and the largest US distributor, Ingram. The process for publication is the same as with a traditionally written book, i.e. the book will be designed, copy-edited, proofread, and published within a timeframe of months.
        """)
        
        with st.expander("What It Costs/How to Pay"):
            st.markdown(""" ## What It Costs/How to Pay
    
            -  Works preapproved by Nimble Books are free. This is limited to situations where we are confident the final work will be suitable for publication by Nimble Books. To propose a project, send a letter with description of the planned work and your background as a writer to wfz at nimblebooks dot com.  Nimble reserves the right of first refusal on the resulting manuscript.
            -  Otherwise, each complete first draft of 100,000 words or less downloaded costs $49.99.
            """)
        with st.expander("Examples"):
            st.markdown("""
                - [Eccentric Dictionaries: An Experiment in AI-Enhanced Human Creativity](https://amzn.to/3GKl1rU) by Frederick Zimmerman. (Nimble, 2021)
                - [Sybil's World: An AI Re-Imagines Herself and Her World Using GPT-3](https://amzn.to/3xM7D2o) by Marc Strassman. (Nimble, 2021)

            """)
        
        with st.expander("Generate Ideas"):
            scripted_video_dict = {'GenericLoglineCreator': 'Simple Logline Creator', 'StructuredLoglineCreator': 'Structured Logline Creator'}
            longform_types = {"Scripted Video": scripted_video_dict, "Short stories": "Short Stories", "Novel": "Novels"}
            longform_types_list = list(longform_types.keys())
            longform_type_selected = st.selectbox("Select a type of longform work", options=longform_types_list, help="Major categories of longform work.")
            generate_ideas(longform_type_selected)



        
        










