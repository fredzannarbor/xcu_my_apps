# loops over all the pdfs in the directory and begins processing them for distribution

import argparse
import os
os.chdir('/Users/fred/bin/nimble/unity/')
import glob
import streamlit as st
import json

import pandas as pd
import datetime

from pathlib import Path

from app.utilities.utilities import create_safe_dir_from_file_path


def main(target_directory, output_dir):
    target_search_path = os.path.join(target_directory, '*.pdf')
    # open file and create directory to house working materials

    timestamped_filename = datetime.datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")

    df_all_processed_files = pd.DataFrame()
    df_row = pd.DataFrame()
    results_df = pd.DataFrame()
    print('looping over pdfs in directory: ' + target_search_path)
    success, errors = 0, 0
    filecount = 0
    config_file_count = 0
    results = []

    config = {}
    #endregion  
    for filename in glob.glob(target_search_path):
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
            results = process_function(filename, output_dir, timestamped_filename=None, filecount=None,  payservices=False, config=None)
            #print(results)
            df_row = pd.DataFrame(results[1])
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
                print('error writing to df_row: ' + filename)
                print(e)
                errors += 1
        
        filecount += 1

        df_all_processed_files = pd.concat([df_all_processed_files, df_row])
        
        #print('cumulative df is now',cumulative_df)
        
    
    cumulative_file_name = timestamped_filename
    if not os.path.exists(output_dir + '/' + 'job_results'):
        os.mkdir(output_dir + '/' + 'job_results')
        
    df_all_processed_files.to_csv(output_dir + '/' + 'job_results' + '/' + cumulative_file_name, index=False)
    
    df_all_processed_files.to_csv(output_dir + '/' + 'cumulative_metadata.csv', index=False)
    print('success: ' + str(success), 'errors: ' + str(errors))
    print('custom config files found: ' + str(config_file_count))
    df_all_processed_files.to_excel(output_dir + '/' + 'job_results' + '/' + timestamped_filename + '.xlsx', index=False)
    df_all_processed_files.to_json(output_dir + '/' + timestamped_filename + '.json', orient='records')

    return



def process_function(filename, output_dir, timestamped_filename=None, filecount=None,  payservices=False, config=None):
    # open next pdf and create directory to house working materials
    thisdoc_dir = create_safe_dir_from_file_path(filename, output_dir)[0]

    #
    function_output = {}
    function_output_df = pd.DataFrame() 
    
    df_row = pd.DataFrame()
    
    try: # creating metadatas_df
        function_output_df = pd.DataFrame.from_dict(function_output, orient='columns')
    except Exception as e:
        print('error creating function_output_df: ' + filename + '\n' + str(e))
    return function_output, function_output_df

def argparse_handler():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--target_directory', type=str, default='/Users/fred/bin/nimble/unity/output')
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


