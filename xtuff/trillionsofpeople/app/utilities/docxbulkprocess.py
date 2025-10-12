# loops over all the pdfs in the directory and begins processing them for distribution

import argparse
import glob
import os
from datetime import datetime

from app.utilities.docx2txt import docx2txt

import app.utilities.docx2copyedit as ce
from app.utilities.docx2chunks import chunkize
from app.utilities.docx2jsonl import docx2jsonl
from app.utilities.utilities import create_safe_dir_from_file_path


def main(docx_directory, output_dir, list2string, limit):
    target_search_path = os.path.join(docx_directory, '*.docx')
    file_list = glob.glob(target_search_path)
    file_list.sort()
    success_count, error_count, filecount = 0, 0, 0

    print("Found", len(file_list), "docx files in", docx_directory)
    print("Found", file_list[:limit])
    for docx_file in file_list[:limit]:
        
        timestamped_filename = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
        
        try:
            print("Sending", docx_file, "to process_docx")
            process_docx(docx_file, output_dir, filecount, timestamped_filename)
            success_count += 1
        except Exception as e:
            print("Error processing", docx_file, e)
            error_count += 1
        filecount += 1
    return


def process_docx(filename, output_dir, filecount, timestamped_filename):
    #print('arriving at process_docx')
    thisdoc_dir_name = create_safe_dir_from_file_path(filename,output_dir)[0]
    print('filename: ', filename, 'thisdoc_dir_name:', thisdoc_dir_name)

    try:
        thisdoc_jsonl_path = docx2jsonl(filename, output_dir)[0]
        with open(thisdoc_jsonl_path[1], 'w') as f:
            f.write(thisdoc_jsonl_path[0])
    except Exception as e:
        print("Error writing thisdoc_jsonl to file", e)
    
        
    try:
        paths = docx2txt(filename, output_dir)
        thisdoc_text_list = paths[0]
        thisdoc_text_path = paths[1]
        thisdoc_text_string = ' '.join(thisdoc_text_list)

        with open(thisdoc_text_path, 'w') as f:
            f.write(thisdoc_text_string)
            
    except Exception as e:
        print('Error writing thisdoc_text to file', e)
        
    try:
        ce.main(filename, output_dir)
    except Exception as e:
        print('Error running copyedit', e)
    
    try:

        chunklist = chunkize(filename, output_dir, chunksize=400)
        #print('successfully chunked', filename)
    except Exception as e:
        print("Error writing thisdoc_chunk to file", e)
    
    return

def argparse_handler():
    argparser = argparse.ArgumentParser()


    argparser.add_argument('--limit', help='limit', default=10)
    argparser.add_argument('--list2string', help='output converted text as single string, not a list', default=False)

    argparser.add_argument("--docx_directory", help="The directory of the files to be processed", default="test/docx")
    argparser.add_argument('--output_dir', help='path to output directory', default='output')
    argparser.add_argument('--working_dir', help='working_dir', default='working')


    args = argparser.parse_args()
    docx_directory = args.docx_directory
    output_dir = args.output_dir
    list2string = args.list2string
    limit = args.limit
    working_dir = args.working_dir

    return docx_directory, output_dir, list2string, limit, working_dir
  

if __name__ == "__main__":

    docx_directory, output_dir, list2string, limit, working_dir = argparse_handler()
    # check if output directory exists, if not create it
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    main(docx_directory, output_dir, list2string, limit)