#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

'''
accepts a dataframe with a column named 'result' that contains a list of objects each of which is a string with many ideas contained in it

the  results must have been created with a preset like BookIdeaExpander that is instructed to generate Python-list lists

results generated with other types of presets will not be parsed correctly
'''
from sys import argv as sysargv

import pandas as pd


# ideas_df to explode function

def check_for_unmatched_brackets(ideas_df):
    for i, result in enumerate(ideas_df['result']):
         # check for mismatched brackets
         # make result not a float
        result = str(result)
        if result.count('[') != result.count(']'):
            print(f"mismatched brackets in row {i}")
            print(result)
            return False
    print('No mismatched brackets found')
    return True
def listify_ideas(ideas_df):
    # convert list of strings from string to list, do not use ast.literal_eval
    ideas_df = ideas_df['result'].astype(str, copy=False)
    ideas_df['result'] = ideas_df['result'].apply(lambda x: x.strip('][').split(', '))
    print(ideas_df.dtypes)
    print(ideas_df['result'].head(5) )
    return ideas_df
def explode_ideas_df(ideas_df):
    # explode ideas_df
    exploded_ideas_df = pd.DataFrame(ideas_df['result'].explode().reset_index(drop=True))
    exploded_ideas_df.columns = ['expanded_result']
    return exploded_ideas_df

def merge_exploded_with_original(ideas_df, exploded_ideas_df):

    # Dropping the 'result' column from the original dataframe
    ideas_df_dropped = ideas_df.drop(columns='result')

    # Replicating the rows of the original dataframe based on the length of result_df
    df_replicated = ideas_df_dropped.loc[ideas_df_dropped.index.repeat(exploded_ideas_df.shape[0])].reset_index(drop=True)

    # Merging the replicated dataframe with the expanded results dataframe
    merged_df = pd.concat([df_replicated, exploded_ideas_df], axis=1)
    # rename column from expanded_result to idea
    #merged_df.rename(columns={'expanded_result': 'idea'}, inplace=True)
    return merged_df

if __name__ == '__main__':
    # use sysargv to pass in tuplefile

    ideas_df = pd.read_csv(sysargv[1])
    #ideas_df = listify_ideas(ideas_df)
    print(ideas_df.head(5))
    print(ideas_df.shape)
    exit()
    exploded_ideas_df = explode_ideas_df(ideas_df)
    print(exploded_ideas_df.head(5))
    print(exploded_ideas_df.shape)
    merged_df = merge_exploded_with_original(ideas_df, exploded_ideas_df)
    print(merged_df.shape)
    print(merged_df.sample(20))
    merged_df.to_csv(sysargv[1].replace('.csv', '_exploded.csv'), index=False)