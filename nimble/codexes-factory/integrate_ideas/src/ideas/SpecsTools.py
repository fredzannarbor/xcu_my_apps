#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
'''
tools to manipulate book spec files
'''
import pandas as pd
from app.utilities.gpt3complete import chatcomplete

class SpecsAndSpecTools:
    def specs2prompt(self, specs_df):
        print(f"spec_df shape is {spec_df.shape}")
        valids_df = spec_df[spec_df.iloc[:, -1].notna()]
        print(f"valids_df shape is {valids_df.shape}")
        # assemble prompt by concatenating key value pairs in valids_df
        cumulative_prompt = ''
        # print(valids_df.columns)
        for index, row in valids_df.iterrows():
            # get value of index for current row as string
            prompt = str(index) + ': ' + valids_df.loc[index, valids_df.columns[0]] + '\n'
            cumulative_prompt = cumulative_prompt + prompt

        return cumulative_prompt


    def create_missing_valids(self, spec_df):
        ''' calls function to complete missing valids in book spec'''

        missings_df = spec_df[spec_df.iloc[:, -1].isna()].copy()

        cumulative_prompt = cdx.specs2prompt(missings_df)
        for m in missings_df.index:
            # print(f"index is {m}")
            prompt = f"{cumulative_prompt} Missing field: {m}"
            print(prompt)
            try:
                result = chatcomplete("CodexSpecsFillInMissingValid", prompt, engine="gpt-3.5-turbo", max_tokens=100)

            except Exception as e:
                print(e)
                result = "error"
            missings_df.loc[m, spec_df.columns[0]] = result
        return missings_df

        def spec_df_row2variables(self, spec_df):
            # get variable values from index of spec_df
           # print(spec_df)
            title = spec_df.loc['title', spec_df.columns[0]]
            idea = spec_df.loc['Idea', spec_df.columns[0]]
            author_voice = spec_df.loc['author_voice', spec_df.columns[0]]
            protagonist = spec_df.loc['protagonist', spec_df.columns[0]]
            antagonist = spec_df.loc['antagonist', spec_df.columns[0]]
            good_guys = spec_df.loc['good_guys', spec_df.columns[0]]
            bad_guys = spec_df.loc['bad_guys', spec_df.columns[0]]
            locations = spec_df.loc['locations', spec_df.columns[0]]
            mcguffins = spec_df.loc['mcguffins', spec_df.columns[0]]
            plot_twists = spec_df.loc['plot_twists', spec_df.columns[0]]
            themes = spec_df.loc['themes', spec_df.columns[0]]
            revelations = spec_df.loc['revelations', spec_df.columns[0]]
            character_arcs = spec_df.loc['character_arcs', spec_df.columns[0]]
            num_chapters = spec_df.loc['num_chapters', spec_df.columns[0]]
            num_chapters = int(num_chapters)
            num_scenes_per_chapter = spec_df.loc['num_scenes_per_chapter', spec_df.columns[0]]
            num_scenes_per_chapter = int(num_scenes_per_chapter)
            num_tokens_total = spec_df.loc['num_tokens_total', spec_df.columns[0]]
            num_tokens_total = int(num_tokens_total)
            special_instructions = spec_df.loc['special_instructions', spec_df.columns[0]]

            return title, idea, author_voice, protagonist, antagonist, good_guys, bad_guys, locations, mcguffins, plot_twists, themes, revelations, character_arcs, num_chapters, num_scenes_per_chapter, num_tokens_total, special_instructions

        def get_attribute(self, attribute):
            return getattr(self, attribute)

        def get_all_attributes(self):
            return self.__dict__.keys()

        def get_all_attributes_as_dict(self):
            return self.__dict__

        def reset_all_attributes(self):
            for attribute in self.__dict__.keys():
                setattr(self, attribute, None)

        def load_all_attributes_from_json(self, json_specs_file):
            # print(json_specs_file)
            with open(json_specs_file) as f:
                data = json.load(f)
                # get first item from list
                data = data[0]
               # print(data)
            return data

        def load_attribute_from_json(self, json_specs_file, attribute):
            #print(json_specs_file, attribute)
            with open(json_specs_file) as f:
                data = json.load(f)
            self.set_attribute(attribute, data[attribute])
