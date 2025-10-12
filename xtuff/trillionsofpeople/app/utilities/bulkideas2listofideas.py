'''
bulk idea generation

loop over a list of single ideas and for each idea
create a list of 20-100-1000 ideas

input: dictionary of idea/preset pairs, e.g.:

set',}
    
idea_preset_dict = {'title': 'sentient tanks', 'idea': 'novels about honorable intelligent tanks', 'preset':  'CreateSFNovelIdeas.json', 'number_of_ideas': 20}
list_of_idea_preset_dicts = [idea_preset_dict]

output: dictionary of list of string ideas

[ 'intelligent tanks': ['Intelligent tank takes a selfie--and gets a big surprise', 'Napoleon Bonaparte meets a time-traveling intelligent tank']
'''
import argparse
import csv


# from charset_normalizer import from_path
# import app.utilities.gpt3complete
# import createsyntheticdata
# import app.utilities.utilities
# from app.utilities.utilities import bulk_argparse_handler

def read_list_of_ideas(filename):
    ideas_to_submit = {}
    with open(filename, mode='r') as input:
        reader = csv.reader(input)
        ideas_to_submit = [{k: v for k, v in row.items()} for row in csv.DictReader(input, skipinitialspace=True)]
        print(ideas_to_submit)
    return ideas_to_submit # list of dicts

def submit_ideas_for_expansion(ideas_to_submit):
    # loop through list of dicts, extract values, and submit to gpt3complete
    # for each idea, create a list of 20-100-1000 ideas
    return

if __name__ == '__main__':
    # get arguments
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--infile', type=str, default='working/csv/Longform.csv', help='generic input file parameter')
    
    infile = argparser.parse_args().infile
    
    ideas_to_submit = read_list_of_ideas(infile)
    print('success; read ', len(ideas_to_submit), 'ideas to submit')
    # dict_of_idea_lists = bulk_idea_generator(idea_preset_dict, output_dir, number_of_ideas)
    
    
    # # write listofideas to json file
    # withopen(output_dir + '/listofideas.json', 'w') as outfile:
    #     json.dump(dict_of_idea_lists, outfile)
        
    # # write list of ideas to jsonl file with one idea per line
    
    
    # # write idea_preset_results to csv file
    # with open(output_dir + '/idea_preset_results.csv', 'w') as outfile:
    #     writer = csv.writer(outfile)
    #     writer.writerow(['idea', 'preset', 'listofideas'])
    #     for idea, preset, listofideas in dict_of_idea_lists.items():
    #         writer.writerow([idea, preset, listofideas])
    # # write idea_preset_results to txt file
    # with open(output_dir + '/idea_preset_results.txt', 'a') as outfile:
    #     for idea, preset, listofideas in dict_of_idea_lists.items():

    #         outfile.write(idea.title() + ': \t' + preset + '\n')
    #         outfile.write(listofideas + '\n')
    
    

