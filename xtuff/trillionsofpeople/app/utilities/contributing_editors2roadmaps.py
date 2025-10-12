#!/usr/bin/python
'''
create roadmaps for contributing editors
'''

import argparse
import os

import pandas as pd
from summarizers import Summarizers

from app.utilities.gpt3complete import gpt3complete

summ = Summarizers()


def loop_over_remits(remits_search_path, output_dir):
    agenda_df = pd.DataFrame(dtype=str)
    cumulative_df_path = os.path.join(output_dir, 'cumulative_agendas.xlsx')
    if not (os.path.exists(cumulative_df_path)):
        cumulative_agendas_df = pd.DataFrame(dtype=str)
    else:
        cumulative_agendas_df = pd.read_excel(cumulative_df_path)
    row_df = pd.DataFrame()
    with open(remits_search_path, 'r') as f:
        remits_df = pd.read_csv(f, header="infer")
    for index, row in remits_df.iterrows():
        prompt = remits_df['Remit'][index]
        print(prompt)
        result = create_roadmap(preset, prompt, engine, output_dir)
        print('result: ', result)
        agenda = result[0]['choices'][0]['text']
        print('agenda: ', agenda)
        df_row = pd.DataFrame([[row['Product Line'], row['Remit'], agenda]], columns=['productline', 'remit', 'agenda'])
        print(df_row.head())
        agenda_df = pd.concat([agenda_df, df_row])
    #agenda_df.reset_index(drop=True, inplace=True)
    agenda_df.to_csv(os.path.join(output_dir, 'agendas.csv'))
    agenda_df.to_json(output_dir + '/' + 'agendas.json', orient='records')
    #agenda_df.astype(str).dtypes
    
    #cumulative_agendas_df.reset_index(drop=True, inplace=True)
    cumulative_agendas_df = pd.concat([cumulative_agendas_df, agenda_df]).drop_duplicates()
    print(cumulative_agendas_df)
    cumulative_agendas_df.reset_index(drop=True, inplace=True)
    cumulative_agendas_df.to_json(os.path.join(output_dir, 'cumulative_agendas.json'), orient='records')
    cumulative_agendas_df.to_excel(os.path.join(output_dir, 'cumulative_agendas.xlsx'), index=False)
    
    summary_df = pd.DataFrame(columns=['productline', 'remit', 'agenda'])

    return

def create_roadmap(preset, prompt,engine, output_dir, editorname=None, suffix=None):
    result = gpt3complete(preset, prompt, engine, suffix=suffix)
    print(result[0]['choices'][0]['text'])
    return result

def textinpandascolumn2text(dataframe, column):
    return ' '.join(dataframe[column])

def concatenate_agenda_items(agenda_items, productline):
    # agenda items are rows in a column
    # read json file into dataframe
    with open(agenda_items, 'r') as f:
        agenda_df = pd.read_json(f, orient='records')
    # read productline row into list
    productlines_list = agenda_df['productline']
    # concatenate productlines as string
    productline_string = ' '.join(productlines)
    productline_dict = {'productline': productlines_list, 'productline_string': productline_string, 'remit': 'concatenated'}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', help='prompt', default="All good men must come to the aid of the party.")
    parser.add_argument('--output_dir', help = 'directory where output will be stored', default = 'contributing_editors')
    parser.add_argument('--preset', help = 'preset file', default = 'ContributingEditor2Agenda')
    parser.add_argument('--engine', help = 'engine', default = 'text-davinci-002')
    parser.add_argument('--remits_search_path', help = 'files containing editor remits', default = 'contributing_editors/remits_test.csv')
    parser.add_argument('--suffix',help="for OpenAI insert mode", default=None)
    args = parser.parse_args()
    output_dir = args.output_dir
    prompt = args.prompt
    preset = args.preset
    engine = args.engine
    suffix = args.suffix
    remits_search_path = args.remits_search_path
    
    loop_over_remits(remits_search_path, output_dir)
    #user_id = "37" #hack
    