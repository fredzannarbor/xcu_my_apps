# loops over all the pdfs in the directory and begins processing them for distribution

import argparse
import os
os.chdir('/Users/fred/bin/nimble/unity/')
import glob
import streamlit as st
import json
import app.utilities.docx2dataframe.main_code.Para_table_image_extraction as d2df

import pandas as pd
import datetime

from pathlib import Path

from app.utilities.utilities import create_safe_dir_from_file_path


def main(target_directory="working/contracted/am_editing", output_dir="output", payservices=False, config=None,
         timestamped_filename=None, filecount=None):
    target_search_path = os.path.join(target_directory, '*.docx')

    # set up

    timestamped_filename = datetime.datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")

    df_all_processed_files = pd.DataFrame()
    df_row = pd.DataFrame()
    results_df = pd.DataFrame()
    print('looping over target files in directory: ' + target_search_path)
    success, errors = 0, 0
    filecount = 0
    config_file_count = 0
    results = []

    config = {}

    # run loop over all files in directory
    for filename in glob.glob(target_search_path):
        print(filename)
        pathfile = Path(filename)
        shortname = pathfile.with_suffix('')
#check for custom configuration file
        shortname_config = shortname.with_suffix('.config')
        if os.path.exists(shortname_config):
            config_file = str(shortname_config)
            config_file_count += 1
            print('found config file: ', config_file)
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    print(config)
                    #exit()
            
            except Exception as e:
                print('error loading config file: ' + config_file)
                print(e)
                
# request analysis of *current* document in the loop

        try:

            results = process_function(filename, output_dir, timestamped_filename=None, filecount=None,  payservices=False, config=None)  # calls a function that contains the meaty logic opf what to do to each file
            print(results)
            df_row['success'] = True
            df_row.to_json(output_dir + '/dfrow.json', orient='records')

        except Exception as e:
            df_row['success'] = False
            st.error('error processing pdf: ' + filename + '\n' + str(e))

            errors += 1 

        try:
            df_row['filename'] = filename

            success += 1
        except Exception as e:
                print('error writing filename to df_row: ' + filename)
                print(e)
                errors += 1
        
        filecount += 1

        df_all_processed_files = pd.concat([df_all_processed_files, df_row])
        
        #print('cumulative df is now',cumulative_df)
        
    
    cumulative_file_name = timestamped_filename
    if not os.path.exists(output_dir + '/' + 'job_results'):
        os.mkdir(output_dir + '/' + 'job_results')
        

    print('success: ' + str(success), 'errors: ' + str(errors))
    print('custom config files found: ' + str(config_file_count))
    df_all_processed_files.to_excel(output_dir + '/' + 'job_results' + '/' + timestamped_filename + '.xlsx', index=False)
    df_all_processed_files.to_json(output_dir + '/' + timestamped_filename + '.json', orient='records')

    return



def process_function(filename, output_dir, timestamped_filename=None, filecount=None,  payservices=False, config=None):
    # open next pdf and create directory to house working materials
    print('top of process function', filename, output_dir)
    thisdoc_dir = create_safe_dir_from_file_path(filename, output_dir)[0]
    thisdoc_basename = create_safe_dir_from_file_path(filename, output_dir)[1]
    print('thisdoc_dir: ', thisdoc_dir)
    # extract file name from path

    #
    function_output = {}
    function_output_results =[]
    function_output_df = pd.DataFrame() 
    
    df_row = pd.DataFrame()
    print('filename: ' + filename)
    try: # this is the meaty part of the function
        function_output_results = d2df.main(filename) 
    except Exception as e:
        print('error creating function_output_df: ' + filename + '\n' + str(e))
    function_output_df = function_output_results[0]
    function_output_df.to_csv(thisdoc_dir + '/' + thisdoc_basename + '_df.csv', index=False)
    return function_output, function_output_df

def argparse_handler():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--target_directory', type=str, default='/Users/fred/bin/nimble/unity/working/contracted/am_editing')
    argparser.add_argument('--output_dir', type=str, default='/Users/fred/bin/nimble/unity/output')
    argparser.add_argument('--payservices', type=bool, default=False)
    argparser.add_argument('--config', type=str, default=None)
    argparser.add_argument('--timestamped_filename', type=str, default=None)
    argparser.add_argument('--filecount', type=int, default=None)
    
    

    args = argparser.parse_args()
    target_directory = args.target_directory
    output_dir = args.output_dir
    payservices = args.payservices
    config = args.config
    timestamped_filename = args.timestamped_filename
    filecount = args.filecount
    return target_directory, output_dir, payservices, config, timestamped_filename, filecount
if __name__ == "__main__":

    target_directory, output_dir, payservices, config, timestamped_filename, filecount = argparse_handler()

    # check if output directory exists, if not create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    #output_dir + '/' + str(uuid.uuid4()) + cumulative_file_name

    
    main(target_directory, output_dir, payservices, config, timestamped_filename, filecount)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    print('returned from processing function at ' + str(timestamp))


