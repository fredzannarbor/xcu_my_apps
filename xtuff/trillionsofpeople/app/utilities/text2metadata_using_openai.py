# import sleep
import json
import os
import sys

import pandas as pd
import streamlit as st
import tiktoken

# from app.utilities.gensim_summarizer import gensim_summarizer
from app.utilities.gpt3complete import (gpt3complete, post_process_text, presets_parser, chatcomplete)
from app.utilities.text2spacyextractivesummary import spacy_summarize

encoding = tiktoken.get_encoding("p50k_base")
encoding35 = tiktoken.get_encoding("cl100k_base")
#


'''
    The following fields are required on the KDP Details page.

    - Language*
    - Book Title
    - Book Subtitle
    - Series*
    - Series Number*
    - Edition Number*
    - Publisher*
    - Primary Author or Contributor*
    - Prefix, First Name, Middle Name, Last Name*
    - Description
    - Publishing Rights*
    - Keywords
    - Categories

    The fields marked with an asterisk are clerical in nature and simply require accurately entering known information. **The remaining fields need to be created by the author or publisher.** This task can be both vitally important to the book's sales and quite time-consuming.
    '''


def get_token_counts_for_presets(preset_dict):
    token_counts = []

    for preset in preset_dict:
        presetdf = presets_parser(preset)[0]
        list1 = presetdf.iloc[0, 5:8].tolist()
        # print(list1)
        # convert list11 to string
        str1 = ''.join(list1)
        list1tokens = encoding.encode(str1)
        token_counts.append(len(list1tokens))
    print(token_counts)

    return token_counts


def common_presets_for_metadata():
    common_presets = {'TitleFromDescription': 'Title & Subtitle',
                      'BibliographicKeywordsGenerator': 'Bibliographic Keywords',
                      'BookDescriptionWriter': 'Book Detail Page Description',
                      'BISAC_CategoryRecommender': "BISAC Categories",
                      "BlurbWriter": "Back Cover Blurb Writer",
                      "ELI5": "ELI5",
                      "tldr_vanilla": "TL;DR",
                      "tldr_one_word": "TLDR in One Word",
                      "FormalDissent": "Formal Dissent",
                      "HostileMAGA": "Hostile MAGA Perspective",
                      "RedTeamCritique": "Red Team Critique",
                      "ActionItems": "Action Items",
                      "AbstractOneShotNature": "Scientific Style",
                      "CoverDesigner": "Cover Illustration Designer",
                      'CreateText2CoverImagePrompt': 'CreateText2ImageCoverPrompt',
                      'CreateText2CoverImagePromptForStableDiffusion':
                          'CreateText2CoverImagePromptForStableDiffusion',
                      'CreateText2MoodImagePrompt': 'Prompt for Mood Illustrations'
                      }

    # common_presets = {"BlurbWriter": "Back Cover Blurb Writer" }
    return common_presets


def create_title_metadata_using_openai(summary_sentences_string, output_dir='output', engine="gpt-3.5-turbo", thisdoc_dir='thisdoc'):
    # returns result list df
    print('length of summary_sentences_string', len(summary_sentences_string))

    preset_dict = common_presets_for_metadata()
    #print(preset_dict)

    result_list = []
    presets = list(preset_dict.keys())

    # print(KDP_results_df)
    if presets:
        actual_responses = []
        for preset in presets:
            current_presetdf = presets_parser(preset)[0]
            preset_result_df = pd.DataFrame()

            try:
                # print(engine)
                if engine == "gpt-3.5-turbo":
                    current_response = chatcomplete(preset, summary_sentences_string, engine, '37')
                    actual_responses.append(current_response)
                    current_response_text = current_response[0]['choices'][0]['message']['content']
                    current_response_text = post_process_text(current_response_text)
                    completion_heading = f"{current_presetdf['completion_heading'].iloc[0]}"
                    append_item = [preset, str(current_response_text)]
                    # print(append_item)
                    result_list.append(append_item)
                else:
                    current_response = gpt3complete(preset, summary_sentences_string, engine)
                    actual_responses.append(current_response)
                    current_response_text = current_response[0]['choices'][0]['text']
                    current_response_text = post_process_text(current_response_text)
                    completion_heading = f"{current_presetdf['completion_heading'].iloc[0]}"
                    append_item = [preset, str(current_response_text)]
                    # print(append_item)
                    result_list.append(append_item)

            except Exception as e:
                st.error('error in text2metadata_using_openai.py')
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)

        actual_responses_df = pd.DataFrame(actual_responses)
        actual_responses_df.to_json(f'{output_dir}/actual_responses.json')
        result_list_df = pd.DataFrame(result_list, columns=['preset', 'response'])
        result_list_df.to_json(f'{output_dir}/result_list.json')
        result_list_df.to_csv(f'{output_dir}/result_list.csv', index=False)
        return result_list


def create_series_metadata_using_openai(summary_sentences_string):
    '''
    Additional metadata is required for books that are part of a series. If you are in doubt as to whether a book should be considered part of a series, note that over time Amazon has added a lot of features to support them.  Series sell.
    '''
    engine = 'gpt-3.5-turbo'
    series_result_list = []
    new_series = True
    main_content = True
    if new_series:
        if main_content == 'Yes':

            series_dict = {'SeriesTitleOnlyGenerator': 'Series Title Ideas',
                           'SeriesTitleandDescriptionGenerator': 'Series Title & Description  Ideas',
                           'SeriesSequelTitles': 'Series Sequel Ideas',
                           'SeriesDescriptionGenerator': 'Series Description'}
            series_presets = ["SeriesTitleOnlyGenerator", 'SeriesDescriptionGenerator',
                              "SeriesTitleandDescriptionGenerator"]
            if series_presets:
                for preset in series_presets:
                    series_presetdf = presets_parser(preset)
                    if engine == "gpt-3.5-turbo":
                        series_response = chatcomplete(preset, summary_sentences_string, engine, '37')
                        series_result_list.append(series_response[0]
                                              ['choices'][0]['message']['content'])
                    else:
                        series_response = gpt3complete(preset, summary_sentences_string, engine="text-davinci-003")

                        series_result_list.append(series_response[0]
                                              ['choices'][0]['text'])
    print(series_result_list)
    with open('output/series_results.json', 'w') as f:
        json.dump(series_result_list, f)

    return series_result_list


if __name__ == "__main__":
    filename = ('app/utilities/data/granddaughter.txt')
    with open(filename, 'r') as f:
        teststring = f.read()
    synopsis = spacy_summarize(teststring, 0.005, 'output')
    print(len(synopsis.split(' ')))
    print('synopsis is', synopsis)
    results = create_title_metadata_using_openai(synopsis)
    print(results)
