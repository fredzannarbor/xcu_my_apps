
# create class for managing creation of longform documents


from pydantic import NoneBytes
from streamlit import echo

import app.utilities.gpt3complete
import app.utilities.syntheticdata
from gpt3_reduced_fx import presets_parser, gpt3complete
import uuid
from uuid import uuid4
import os
from os import environ as osenv
import stripe
import csv
import json
#import createsyntheticdata as csd

stripe_keys = {
    "secret_key": os.environ["STRIPE_SECRET_KEY"],
    "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"],
    "price_id": os.environ["STRIPE_PRICE_ID"],
    "endpoint_secret": os.environ["STRIPE_ENDPOINT_SECRET"],
}

stripe.api_key = stripe_keys["secret_key"]

import openai

openai.api_key = os.environ['OPENAI_API_KEY']
openai_user_id_for_safety_tracking = os.environ['OPENAI_USER_ID_FOR_SAFETY_TRACKING']


# tuple1 = ['SimpleXmasStoryIdeas', 'csd', ['n=3'],'intelligent tanks', None, NoneBytes]
# tuple2 = ['SimpleXmasStoryIdeas', 'csd', ['n=4'],'Napoleon Bonaparte', None, None]
# tuple3 = ['SimpleXmasStoryIdeas', 'csd', ['n=5'],'from the perspective of the infant Jesus', None, None]
# tuple_list = ['tuplelist1',tuple1, tuple2, tuple3]
# tuple4 = ['CreatePersonBackstory', 'gpt3complete', 'n=3','\n$NAME will be born in the area currently known as Russia in the year 3000 CE.\n', None, None]
# tuple5 = ['NFTBioCreator', 'gpt3complete', 'Napoleon Bonaparte', None, None, None]
# tuple6 = ['NFTWhyPersonIsGreat', 'gpt3complete', 'Napoleon Bonaparte', None, None, None]
# tuple_list = ['NFTmaker', tuple5, tuple6 ]
class Longform:
    def __init__(self, list_of_preset_tuples, output_dir):
        self.list_of_preset_tuples = list_of_preset_tuples
        self.output_dir = output_dir

        return

    def data_dir(output_dir):
        output_dir = 'app/data/longform_test'
        return output_dir

    def set_defaults(self):
# set
        return

    def open_tuple_csv(filename):
        with open(filename, newline='') as f:
            reader = csv.reader(f)
            next(reader)
            tuple_list = [tuple(row) for row in reader]
            print(tuple_list)
        return tuple_list

    def create_longform(tuplenow, output_dir):
        results = []
        results_dict = {}
        for project, preset, completion_type, prompt, parameters, function4each, functionatend in tuplenow:
            datadir = output_dir + '/' + project + '_' + str(uuid4())[0:4]
            os.mkdir(datadir)
            print('datadir is: ' + datadir)
            print('***')
            print(preset, completion_type, prompt, parameters, function4each, functionatend)
            print('***')
            if parameters:
                for parameter in parameters:
                        #print(parameter)
                        if parameter.startswith("n="):
                            n = parameter.split("=")[1]
            else:
                print('no parameters set')

            if completion_type == 'gpt3complete':

                response = gpt3complete(preset, prompt, parameters)
                openai_response = response[0]
                #print('preset is: ' + preset)
                text = openai_response['choices'][0]['text']
                #print('text is', text)
                presetappend = preset +  '\n'
                
                results.append(presetappend)
                textappend = text + '\n'
                results.append(textappend)
                results_dict.update({preset: text})

            elif completion_type == 'csd':
               # print('got to csd', 'preset is', preset, 'parameters are', parameters, 'prompt is', prompt, 'datadir is', datadir)
                response = csd.main(article_writer_preset=preset,number=n, generate_articles=True, article_titles_only=True, article_title_prompt=prompt, datadir=datadir)
                text = openai_response['choices'][0]['text']
                results.append(preset)
                results.append(text)
                results_dict.update({preset: textappend})
            elif completion_type == 'gpt3complete':
                gpt3complete.create_longform(preset, parameters, prompt, datadir)
            else:
                print('completion_type not recognized')
                return
            # save as json
            with open(datadir + '/results.json', 'w') as f:
                json.dump(results_dict, f)

        return results, results_dict
    
    tuplenow = open_tuple_csv('app/data/tuples2.csv')
    print('tuplenow', tuplenow)
    cumulative = create_longform(tuplenow, 'app/data/longform_test')
    #convert cumulatie to string
    print(cumulative)
    with open('app/data/longform_test/results.txt', 'w') as f:
        f.write('\n'.join(cumulative[0]))
    print(cumulative)
