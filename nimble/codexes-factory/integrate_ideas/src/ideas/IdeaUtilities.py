#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import json

import pandas as pd
import streamlit as st
from pathlib import Path
from uuid import uuid4

from app.utilities.gpt3complete import chatcomplete
from app.utilities.utilities import read_markdown_file, get_version_as_dict, spreadsheet2df
import nltk
import random
from typing import Optional, List, Union



class IdeaUtilityFunctions:

    def __init__(self):
        pass

    def normalize_idea_headings(self, ideas_df):
        ideas_df = ideas_df.rename(columns={'idea': 'Idea', 'author': 'Author', 'author_take': 'AuthorTake'})
        return ideas_df

    def ideas2moreideas(self, ideas_df, preset, model, num_expansions):
        new_idea_df = pd.DataFrame()
        ideas_df = self.normalize_idea_headings(ideas_df)
        #st.write(ideas_df.head(5), preset, model, num_expansions)
        # fill in nans in idea_df as strings
        ideas_df = ideas_df.astype(str)
        ideas_df.fillna("")
        print(ideas_df.columns)
        for index, row in ideas_df.iterrows(): # each row is an idea to expand
            prompt = row['Idea']
            st.write(f"Expanding idea {index} of {ideas_df.shape[0]}")
            #st.write(f"prompt: {prompt}")
            for i in range(num_expansions):
                try:
                    response_text = chatcomplete(preset, prompt, model)
                    result = response_text
                    st.info(result)
                except Exception as e:
                    st.error(e)
                    result = "OpenAI Error" + str(e)
                    break
                new_row = {'Idea': row['Idea'], 'Expansion': result, "number": i}
                df_row = pd.DataFrame([new_row])
                new_idea_df = pd.concat([new_idea_df, df_row], ignore_index=True)
                if index % 25 == 0:
                    new_idea_df.to_csv("output/tmp_save_ideas2moreideas_results" + str(uuid4())[:6] + ".csv")
        return new_idea_df

    def ideas2authors_for_expansion(self, author_stable_df, ideas_df, preset="BookIdeaSimpleVariation", model="gpt-3.5-turbo", num_authors_per_idea=1):
        ideas_df = self.normalize_idea_headings(ideas_df)
        # rotate through the ideas and assign each one to an author
        # for each idea, expand it into a number of ideas
        author_generated_ideas = pd.DataFrame()
        for index, row in ideas_df.iterrows():
            # get an author
            author = author_stable_df.sample(n=num_authors_per_idea)
            # convert author to a single row df
            author_df = author.iloc[0]
            row_df = row
            preset = "BookIdeaSimpleVariation"
            current_idea = row_df['Idea']
            # loop through author_df and assemble the key/value pairs into a string
            author_persona_block = ""
            for key, value in author_df.items():
                author_persona_block = author_persona_block + f"{key}: {value}\n\n"
            current_idea =  "You are a skilled author whose personal attributes are as follows:\n\n" + author_persona_block + "\n---\n" + "Book Idea:\n" + current_idea
            try:
                author_take_on_current_idea = chatcomplete(preset, current_idea, model)
            except Exception as e:
                st.error(e)
                author_take_on_current_idea = "Completion Error"
            st.write(author_take_on_current_idea)
            try:
                author_take_result = author_take_on_current_idea
            except Exception as e:
                st.error(e)
                author_take_result = "Completion Error"
            new_row = { 'Author': author_df["Pen Name"], 'AuthorTake': author_take_result, 'Idea': current_idea}
            author_generated_ideas = pd.concat([author_generated_ideas, pd.DataFrame([new_row])], ignore_index=True)
        return author_generated_ideas

    def ideas2presets(self, ideas_df: list, presets: list, prompts: list, idea_rows=10, idea_beginning_row=0, idea_ending_row=10, model="gpt-3.5-turbo"):

        if not isinstance(ideas_df, pd.DataFrame):
            print("Ideas_df not a valid df")
            return
        if 'Idea' not in ideas_df.columns:
            print("Ideas_df does not have a column named 'Idea'")
            if 'idea' in ideas_df.columns:
                ideas_df = ideas_df.rename(columns={'idea': 'Idea'})
            else:
                print("Ideas_df does not have a column named 'idea'")
                return
        if not isinstance(presets, list):
            print("Presets not a valid list")
            return
        results = []
        prompt_dfs = []
        for prompt in prompts:
            st.info(f'looking for occurrences of {prompt} in ideas_df')
            prompts = prompt # Define your fixed prompts
            prompt_df = pd.DataFrame()

            for index, idea in ideas_df.iterrows():

                idea = idea['Idea']
                #st.info(idea)
                for preset in presets:
                    # Using full_prompts as the concatenation of fixed prompts and the current idea
                    full_prompts = prompts + '\n\n' + idea
                    try:
                        response_text = chatcomplete(preset, full_prompts, engine=model)
                        st.write(response_text)
                    except Exception as e:
                        st.error(e)
                        result = "Completion Error"
                        break
                    result = response_text
                    # add result to current row of df
                    ideas_df.loc[index, preset] = result
                    prompt_df.loc[index, prompt] = result
                # Review where 'idea_rows' is coming from, it seems not defined
                #st.write(index, idea_rows)
                if index > idea_rows:
                    break
                print(ideas_df.head(5))

            prompt_dfs.append(prompt_df)
            prompt_df.to_csv(f"output/{prompt}_{str(uuid4())[:6]}.csv")
            prompt_df.to_json(f"output/{prompt}_{str(uuid4())[:6]}.json")
        return ideas_df, prompt_dfs




