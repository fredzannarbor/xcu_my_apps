#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
'''
tools to manipulate book spec files
'''
import pandas as pd
from app.utilities.gpt3complete import chatcomplete

class SpecsTools:
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
