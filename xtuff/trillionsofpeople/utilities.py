from argparse import PARSER
from os import pardir
import pandas as pd
import streamlit as st
import os

import nltk

import re
import csv
# import inspect
# from inspect import currentframe
from datetime import datetime
import subprocess
# inspection utility


def get_info(obj):

  type_name = type(obj).__name__
  print('Value is of type {}!'.format(type_name))
  prop_names = dir(obj)

  for prop_name in prop_names:
    prop_val = getattr(obj, prop_name)
    prop_val_type_name = type(prop_val).__name__
    print('{} has property "{}" of type "{}"'.format(type_name, prop_name, prop_val_type_name))

    try:
      val_as_str = json.dumps([ prop_val ], indent=2)[1:-1]
      print('  Here\'s the {} value: {}'.format(prop_name, val_as_str))
    except:
      pass
    return val_as_str

def get_linenumber():
    cf = currentframe()
    return cf.f_back.f_line

def standard_nimble_argparse():
    import argparse
    parser = argparse.ArgumentParser(description='Nimble Standard')
    parser.add_argument('--infile', '-i', type=str, default='../data/input.txt', help="input file")
    parser.add_argument('--outfile', '-o', type=str, default='../data/output.txt', help="output file")
    parser.add_argument('--datadir', '-d', type=str, default='../data', help="data directory")
    parser.add_argument('--tmpdir', '-t', type=str, default='/tmp', help="temporary directory")
    parser.add_argument('--logdir', '-l', type=str, default='../logs', help="log directory")
    parser.add_argument('--logfile', '-f', type=str, default='nimble.log', help="log file")
  
    args = parser.parse_args()

    infile = args.logfile
    outfile = args.outfile
    datadir = args.datadir
    tmpdir = args.tmpdir
    logdir = args.logdir
  
    print('made it')
    return 'made it', infile, outfile, parser
  


#@st.cache
def cacheaware_file_uploader(user_id):
    uploaded_file = None
    st.info('inside cacheaware fileuploader')

    try:

      uploaded_file = st.file_uploader(   
          "Upload your document", type=['pdf', 'docx'])

    except Exception as ex:
                st.write('## Trapped exception')
                st.error(str(ex))# display error message

    if uploaded_file is not None:
        file_details = {"FileName":uploaded_file.name,"FileType":uploaded_file.type,"FileSize":uploaded_file.size}
        user_docs_target_dir =  'app/userdocs/' + str(user_id)
        tempdir_target_dir = '/tmp/unity/' + str(user_id)
        if not os.path.exists(tempdir_target_dir):
            os.makedirs(tempdir_target_dir)
        save_uploaded_file(uploaded_file, user_docs_target_dir)
        st.write("File uploaded successfully; check details below to be sure it was the right one:")
        st.write(file_details)

        st.write(" Now processing document ...")

        text, jsondata = None, None
        FileName = str(file_details['FileName'])
        if FileName.endswith('.docx'):
            st.info("You uploaded a .docx file.")
            text = docx2txt.process(uploaded_file)
            
        elif FileName.endswith('.pdf'):

            st.info("Converting PDF to text ...")
            FileLocation = os.path.join(user_docs_target_dir, FileName)

            text = high_level.extract_text(uploaded_file)
        
        #st.json(jsondata)
        if text is None:
          st.error("Error: No text found in uploaded file [None]")
          return None
        elif len(text) == 0:
          st.error("No text found in uploaded file [len == 0]")
          return None
        else:
            print(len(text))
            st.info("Text successfully extracted.") 
            return file_details, text


def save_uploaded_file(uploaded_file, user_docs_target_dir):
    with open(os.path.join(user_docs_target_dir, uploaded_file.name),"wb") as f:
        f.write(uploaded_file.getbuffer())
    success_msg = f"File {uploaded_file.name} saved successfully to " + f"{user_docs_target_dir}."
    return success_msg

def show_current_version():
    
  try:
        mtime = os.path.getmtime('.git/FETCH_HEAD')
  except OSError:
      mtime = 0
  last_modified_date = datetime.fromtimestamp(mtime)

  git_describe_long = subprocess.check_output(["git", "describe", "--long"]).decode("utf-8").strip()

  most_recent_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()

  last_commit_message = str(subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode('utf-8').strip())

  __version_info__ = subprocess.check_output(["git", "describe", "--long"]).decode("utf-8").strip() + " | " + subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip() + ' | last updated: ' + last_modified_date.strftime("%Y-%m-%d %H:%M:%S") + ' | ' + last_commit_message

  version_info_list = [ git_describe_long, most_recent_branch, last_commit_message, last_modified_date.strftime("%Y-%m-%d %H:%M:%S")]

  __version__ =  version_info_list
  ##__version__=__version_info__  

  return __version__