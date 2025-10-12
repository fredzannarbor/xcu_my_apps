# uses pypaperbot to get complete text of papers from SciHub and download for further action

import argparse
import os
# call subprocess
import subprocess
from datetime import datetime

import fitz
import pandas as pd

import app.utilities.RecursiveSummarizer.recursively_summarize as rs
from app.utilities.gpt3complete import gpt3complete


# run pypaperbot as subprocess
# python -m PyPaperBot --query="Machine learning" --scholar-pages=3  --min-year=2018 --dwn-dir="C:\User\example\papers" --scihub-mirror="https://sci-hub.do"

def open_pdf_convert_to_text(fname):
    doc = fitz.open(fname)  # open document
    alltext = ""
    for page in doc:  # iterate the document pages
        text = page.get_text().encode("utf8")  # get plain text (is in UTF-8)
        alltext += text.decode("utf8")  # decode to plain text (is in UTF-8)
    return alltext


def run_pypaperbot(query, scholar_pages=1, min_year=2017, output_dir='working/pypaperbot/test',
                   scihub_mirror="https://sci-hub.do", restrict=0):
    try:
        subprocess.run(
            ['python', '-m', 'PyPaperBot', '--query=', query, '--scholar-pages=', scholar_pages, '--min_year=',
             min_year, '--dwn-dir=', output_dir, '--scihub-mirror=', scihub_mirror, '--restrict', restrict])
    except Exception as e:
        print(e)
        failure_message = f'pypaperbot failed to run with error: {e}'
        print(failure_message)
        return failure_message
    success_message = f'pypaperbot run with query {query}, {scholar_pages} pages, min year {min_year}, output dir {output_dir}, scihub mirror {scihub_mirror}'
    return success_message


# should I run bulkpdfprocess over these? no because they are not becoming books

def loop_over_directory_summarize_files(directory, limit=3):
    # loop over directorym -- USES PAYSERVICES
    # assumes input files are PDFs
    print("directory: ", directory)
    doc = fitz.open()
    summary_of_file_text = ""
    all_files_summary_df = pd.DataFrame()
    for counter, file in enumerate(os.listdir(directory)):
        if counter == 0:
            file_header = "\n" + "Summary of file: " + file + "\n"
            summary_of_file_text += file_header
        if counter >= limit:
            break
        print('summarizing file: ', file)
        openthisfilename = directory + '/' + file
        doc_text = open_pdf_convert_to_text(openthisfilename)

        # now summarize the text of the current file until it is small enough
        # to submit with preses

        result = rs.loop_until_floor_and_ceiling_satisfied(doc_text)
        counter += 1

        file_destination = args.basedir + '/summaries/' + str(file[:-3]) + 'txt'
        with open(file_destination, 'w') as f:
            f.write(result)

    return f'Successfully summarized {counter} files in {directory}'


def loop_over_summaries_run_presets(summaries_dir, preset_list=['tldr_vanila'], limit=3):
    # loop over directory
    print('running presets on summaries')
    all_files_summary_df = pd.DataFrame()
    preset_results = {}
    for file in os.listdir(summaries_dir):
        # each file is a text summary of a header
        # run each preset on each fil
        print(f'... working on file {file} in dir {summaries_dir}')

        with open(summaries_dir + '/' + file, encoding="latin-1") as f:
            summary_text = f.read()
        # check summary size in tokens
        # need to check to make sure summary + prompt + preset will fit
        preset = "tldr_vanilla"
        for preset in preset_list:
            # create directory for each preset
            print('running preset: ', preset)
            preset_dir = args.basedir + '/' + preset
            if not os.path.exists(preset_dir):
                os.mkdir(preset_dir)
                print('created directory: ', preset_dir)
            response = gpt3complete(preset, summary_text, engine='text-davinci-003')
            result = response[0]['choices'][0]['text']
            print(result)
            preset_result_destination = preset_dir + '/' + str(file[:-3]) + '.txt'
            with open(preset_result_destination, 'w') as f:
                f.write(result)
        file_header = "\n" + "Summary of file: " + file + "\n"
        list_of_chunks = [file_header]
        list_of_chunks.append(rs.summarize_by_chunks(file))
        # create dataframe from list of chunks\
        file_df = pd.DataFrame(list_of_chunks)
        pd.concat([all_files_summary_df, file_df])
        file_destination = preset_dir + '/' + preset + '_all.txt'
        with open(file_destination, 'w') as f:
            f.write(result)
    return all_files_summary_df

def assemble_chapter_for_each_file(directory, preset_list, limit=3):
    # loop over directorym -- USES PAYSERVICES
    # assumes input files are PDFs
    print("directory: ", directory)
    doc = fitz.open()
    summary_of_file_text = ""
    all_files_summary_df = pd.DataFrame()
    for counter, file in enumerate(os.listdir(directory)):
        if counter == 0:
            file_header = "\n" + "Summary of file: " + file + "\n"
            list_of_chunks.append(file_header)
        if counter >= limit:
            break
        print('summarizing file: ', file)
        openthisfilename = directory + '/' + file
        doc_text = open_pdf_convert_to_text(openthisfilename)

        # now summarize the text of the current file until it is small enough
        # to submit with preses

        summary_result = rs.loop_until_floor_and_ceiling_satisfied(doc_text)
        counter += 1
        all_preset_results = ""
        for preset in preset_list:
            # create directory for each preset
            print('running preset: ', preset)
            preset_dir = args.basedir + '/' + preset
            if not os.path.exists(preset_dir):
                os.mkdir(preset_dir)
                print('created directory: ', preset_dir)
            response = gpt3complete(preset, result, engine='text-davinci-003')
            this_preset_result = response[0]['choices'][0]['text']
            all_preset_results += this_preset_result
        chapter_text_this_file = all_preset_results + summary_text
        if not os.path.exists(chapters_dir):
            os.mkdir(chapters_dir)
    return

if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument('--query', type=str, help='query to search for')
    argparser.add_argument('--scholar-pages', type=int, help='number of pages to search')
    argparser.add_argument('--min-year', type=int, help='minimum year to search')
    argparser.add_argument('--scihub-mirror', type=str, help='scihub mirror', default="https://sci-hub.do")
    argparser.add_argument('--basedir', type=str, help='target directory', default='working/pypaperbot/test/')
    argparser.add_argument('--preset-list', type=str, help='preset list', default=['tldr_vanilla'])
    argparser.add_argument('--start-mode', type=str, help='mode', default='start_with_pypaperbot')
    argparser.add_argument('--limit', type=int, help='limit', default=3)
    argparser.add_argument('--restrict', type=int, help='bibtex only is 0', default=0)
    args = argparser.parse_args()
    restrict = args.restrict
    # preset list for #5GW

    # check if basedir exists
    if not os.path.exists(args.basedir):
        os.makedirs(args.basedir)
    if not os.path.exists(args.basedir + '/summaries'):
        os.makedirs(args.basedir + '/summaries')
    if not os.path.exists(args.basedir + '/pdfs'):
        os.makedirs(args.basedir + '/pdfs')
    if not os.path.exists(args.basedir + '/presets'):
        os.makedirs(args.basedir + '/presets')

    if args.start_mode == 'start_with_pypaperbot':
        run_pypaperbot(args.query, args.scholar_pages, args.min_year, args.scihub_mirror, args.basedir,
                       restrict=0)  # bibtex only
        run_pypaperbot(args.query, args.scholar_pages, args.min_year, args.basedir, args.scihub_mirror,
                       restrict=1)  # pdf only
        loop_over_bibtext()
        loop_over_directory_summarize_files(args.basedir + '/pdfs', limit=3)
        loop_over_summaries_run_presets(args.basedir + '/summaries', preset_list=args.preset_list, limit=3)
    if args.start_mode == 'start_with_pdfs':
        loop_over_directory_summarize_files(args.basedir + '/pdfs', limit=3)
        loop_over_summaries_run_presets(args.basedir + '/summaries', preset_list=args.preset_list, limit=3)
    if args.start_mode == 'start_with_summaries':
        loop_over_summaries_run_presets(args.basedir + '/summaries', preset_list=args.preset_list, limit=3)

    current_time = datetime.now().strftime("%H:%M:%S")
    print(current_time, ": Finished...")
    print('output files are in: ', args.basedir)
