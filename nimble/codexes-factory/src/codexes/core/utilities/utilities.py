#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

import argparse
import datetime
import glob
import inspect
import json
import os
import re
import subprocess
import sys
import traceback
from datetime import datetime
from inspect import currentframe
from pathlib import Path
import shutil
import ftfy
import spacy
import streamlit as st
import streamlit.components.v1 as components
import tiktoken
from docx2txt import docx2txt
from pandas.api.types import is_categorical_dtype
from pdfminer.high_level import extract_text
from rich.console import Console
from spacy.language import Language
import numpy as np


#from spellchecker import SpellChecker
from streamlit.web.server.websocket_headers import _get_websocket_headers
import logging
encoding = tiktoken.get_encoding("p50k_base")
encoding35 = tiktoken.get_encoding("cl100k_base")
#from xls2xlsx import XLS2XLSX

log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
numeric_level = getattr(logging, log_level, None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % log_level)
logging.basicConfig(level=numeric_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

console = Console(record=True)

from random import choice
from string import punctuation

from PIL import Image
#from fasttext.FastText import _FastText
#from app.utilities.text2sumy_summarize import sumy_summarize

def get_info(obj):
    """

    This method called "get_info" takes an object as a parameter.

    It prints the type name of the object and then iterates over the properties of the object using the "dir" function. For each property, it prints the name and type of the property, and
    * then tries to convert the value of the property to a string using the "json.dumps" function. If successful, it prints the property value.

    The method returns the value of the last property converted to a string.

    Example usage:
    obj = SomeClass()
    result = get_info(obj)

    Parameters:
    - obj: The object to get information from.

    Return:
    - The value of the last property converted to a string.

"""
    type_name = type(obj).__name__
    print('Value is of type {}!'.format(type_name))
    prop_names = dir(obj)
    val_as_str = ''
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
  
def read_BIP_dataframe(filename, maxrows=10):
    cwd = os.getcwd()
    filename = os.path.join(cwd, filename)
    # st.info(filename)
    BIPdf = pd.DataFrame()
    # if extension is .csv, read as csv
    if filename.endswith('.csv'):
        try:
            BIPdf = pd.read_csv(filename, parse_dates=['Pub Date'])
        except Exception as e:
            print(e)
    elif filename.endswith('.xlsx'):
        try:
            BIPdf = pd.read_excel(filename)
        except Exception as e:
            print(e)
    elif filename.endswith('.json'):
        try:
            BIPdf = pd.read_json(filename)
        except Exception as e:
            print(e)
    else:
        print('filetype not supported')
        return ('Could not read filetype, no BIPdf returned')
    #BIPdf = B  IPdf.drop(columns=['old', 'suffix'])
    #BIPdf['Pub Date'] = pd.to_datetime(BIPdf['Pub Date'])
    # truncate ISBNs after decimal point

    BIPdf['ISBN'] = BIPdf['ISBN'].astype(str).str.split('.').str[0]
    return BIPdf
    
def get_PDF_info(uploaded_file):
    import io

    import PyPDF2
    with io.BytesIO(uploaded_file) as open_pdf_file:
      read_pdf = PyPDF2.PdfFileReader(open_pdf_file)
    info = read_pdf.getDocumentInfo()

    return info 
  
def get_PDF_lang_value(filename):
    from PyPDF2 import PdfFileReader
    print('entered lang value')
    pdfFile = PdfFileReader(open(filename, 'rb'))
    catalog = pdfFile.trailer['/Root'].getObject()
    try:
        langs = catalog['/Lang']
        print('langs', langs)
        #st.write('langs', langs)
        return langs
    except:
        print('no lang value')
        #st.write('no lang value')
        return 'no lang value'
      

def get_lang_detector(nlp, name):
    return nlp.LanguageDetector()
 
def detect_language_of_text(text):
  
  nlp = spacy.load("en_core_web_sm")
  Language.factory("language_detector", func=get_lang_detector)
  nlp.add_pipe('language_detector', last=True)
  text_content = text
  doc = nlp(text_content) 
  detected_language = doc._.language #4
  print('detected language', detected_language)
  return detected_language


def get_GPT2_token_count(text):
    tokencount = len(encoding.encode(text))
    return tokencount



# def cacheaware_summarizer(text, wordcount):
#
#     summary = sumy_summarize(text, 20)
#     sentences = nltk.sent_tokenize(summary)
#     summary_sentence_list = []
#     for sentence in sentences:
#         summary_sentence_list.append(sentence)
#     return summary_sentence_list

# def spell_check_text(text):
#     #remove all punctuations before finding possible misspelled words
#   s = re.sub(r'[^\w\s]','',text)
#   wordlist=s.split()
#   spell = SpellChecker()
#   misspelled = list(spell.unknown(wordlist))
#   problemwordstuple = []
#   for word in misspelled:
#       thiswordtuple = spell.candidates(word, spell.correction(word), spell.candidates(word))
#       problemwordstuple.append(thiswordtuple)
#   return problemwordstuple
#
# import numpy as np


def make_dict_arrays_equal_length(metadatas_dict):
    max_len = max((len(lst) if isinstance(lst, list) else 1) for lst in metadatas_dict.values())

    for k, v in metadatas_dict.items():
        if isinstance(v, bool):
            metadatas_dict[k] = [v] * max_len
        elif isinstance(v, list):
            pad_length = max_len - len(v)
            if all(isinstance(item, (int, float)) for item in v):
                metadatas_dict[k] += [np.nan] * pad_length
            else:
                metadatas_dict[k] += [''] * pad_length
        else:
            metadatas_dict[k] = [v] * max_len

    return metadatas_dict

#@st.cache_data
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

            text = extract_text(uploaded_file)
            #text = pdfminer.(uploaded_file)
        
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
  
def bulk_argparse_handler():
    argparser = argparse.ArgumentParser()
  
    argparser.add_argument('--infile', type=str, default='', help='generic input file parameter')
    argparser.add_argument('--limit', help='limit', default=10)
    argparser.add_argument('--list2string', help='output converted text as single string, not a list', default=False)

    argparser.add_argument("--pdf_directory", help="The directory of the files to be processed", default="working/pdf")
    argparser.add_argument('--output_dir', help='path to output directory', default='output')
    argparser.add_argument('--jobcontroldir', help='jobcontrol', default='output/jobcontrol')
    argparser.add_argument('--tmpdir', help='tmpdir', default='output/tmp')
    argparser.add_argument('--working_dir', help='working_dir', default='working')
    argparser.add_argument('--cumulative_file_name', help='cumulative_file_name', default='cumulative_metadata.csv')
    
    args = argparser.parse_args()
    pdf_directory = args.pdf_directory
    limit = args.limit
    output_dir = args.output_dir
    list2string = args.list2string
    cumulative_file_name = args.cumulative_file_name


    working_dir = args.working_dir
    infile = args.infile
    
    # check if output directory exists, if not create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)

    return args

def create_safe_dir_from_file_path(filename, output_dir):
    thisdoc_dir_name, thisdoc_dir_path, thisdoc_basename ='', '', ''
    thisdoc_suffix = ''
    thisdoc_basename = os.path.basename(filename)
    #print('thisdoc_basename', thisdoc_basename)
# replace all punctuation with underscores
    convert_to_underscores = punctuation
    translate_table = str.maketrans(convert_to_underscores, '_'*len(convert_to_underscores))
    thisdoc_suffix = Path(filename).suffix
    thisdoc_suffix_length = len(thisdoc_suffix)
    thisdoc_basename = thisdoc_basename.translate(translate_table)[:-thisdoc_suffix_length] # needs to be 5 characers because ".docx" is 5 chars
    thisdoc_dir_path = output_dir + '/' + thisdoc_basename
    #print('thisdoc_dir_path', thisdoc_dir_path)
    if not os.path.exists(thisdoc_dir_path):
        try:
            with open(filename,'rb') as f:
                        os.makedirs(thisdoc_dir_path)
                        print('created directory using safe name: ' + thisdoc_dir_path)
        except Exception as e:
            print(e)
            print("not creating temp directory because could not open file: " + filename)

    return thisdoc_dir_path, thisdoc_basename

def make_basename_safe(basename):
    return re.sub(r'[^\w\s]','_',basename)


def remove_extension_from_filename(filename):
    filename_components = filename.rsplit(".", 1)
    return filename_components[0]

def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()

def statcounter(height, width):
    return components.html('''<!-- Default Statcounter code for Nimble Books
        https://NimbleBooks.com -->
        <script type="text/javascript">
        var sc_project=12694777; 
        var sc_invisible=1; 
        var sc_security="cf16ad25"; 
        </script>
        <script type="text/javascript"
        src="https://www.statcounter.com/counter/counter.js"
        async></script>
        <noscript><div class="statcounter"><a title="free hit
        counter" href="https://statcounter.com/"
        target="_blank"><img class="statcounter"
        src="https://c.statcounter.com/12694777/0/cf16ad25/1/"
        alt="free hit counter"
        referrerPolicy="no-referrer-when-downgrade"></a></div></noscript>
        <!-- End of Statcounter Code -->
       ''', height=height, width=width)

    
def detailed_error_message(e):
        
        error_message = traceback.format_exc()
        return(error_message)
    
def get_current_version():
    try:
        mtime = os.path.getmtime('.git/FETCH_HEAD')
    except OSError:
        mtime = 0
    last_modified_date = datetime.fromtimestamp(mtime)

    last_commit_message = str(subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode('utf-8').strip())

    __version_info__ =  subprocess.check_output(["git", "describe", "--long"]).decode("utf-8").strip() + '\n\nlast updated: ' + last_modified_date.strftime("%Y-%m-%d %H:%M:%S") 
    #  "\n - " + subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip() + '\n - ' + last_commit_message

    __version__=__version_info__  

    return(__version__)

def get_version_as_dict():
    
    try:
        mtime = os.path.getmtime('.git/FETCH_HEAD')
    except OSError:
        mtime = 0
    last_modified_date = datetime.fromtimestamp(mtime)
    try:
        version_line = subprocess.check_output(["git", "describe", "--long"]).decode("utf-8").strip()

        last_commit_message = str(subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode('utf-8').strip())

        update_line = last_modified_date.strftime("%Y-%m-%d %H:%M:%S")
        current_branch = 'unknown'
        branches =   subprocess.check_output(['git', 'branch']).decode('utf-8').strip().split('\n')
            # loop through list and select the current branch

        for branch in branches:
            if branch.startswith('*'):
                current_branch = branch[2:]

        data = {"version": version_line, "current branch": current_branch, "last updated": update_line, 'most recent commit message': last_commit_message}
        #data = version_line, update_line, last_commit_message

        datalist = [version_line, current_branch, update_line, last_commit_message]


        df = pd.DataFrame(data, index=[0]).T.rename(columns={0: ''})

        return data

    except Exception as e:
        logger.error(e)


def build_trifecta_banner():
    AI_banner_image_list = ["./resources/jackson-so-TQ3SgrW9lkM-unsplash.jpg", "./resources/markus-winkler-tGBXiHcPKrM-unsplash.jpg", "./resources/max-langelott-wWQ760meyWI-unsplash.jpg", "./resources/franki-chamaki-z4H9MYmWIMA-unsplash.jpg", "./resources/mauro-sbicego-4hfpVsi-gSg-unsplash.jpg"]
    AI_banner_image = choice(AI_banner_image_list)
    book_banner_image = choice(["./resources/henry-be-lc7xcWebECc-unsplash.jpg", "./resources/ed-robertson-eeSdJfLfx1A-unsplash.jpg", "./resources/laura-kapfer-hmCMUZKLxa4-unsplash.jpg", "./resources/chris-lawton-zvKx6ixUhWQ-unsplash.jpg"])
    logo_image_list = [("./resources/AILAB2.jpg", "Logo design by Fred Zimmerman.")]
    logo_image_tuple = choice(logo_image_list)
    #st.write(logo_image_tuple)
    logo_image = logo_image_tuple[0]
    #st.write(logo_image)
    #logo_image = choice(["./resources/AI4booklovers.png"])
    logo_caption = (logo_image_list[0][1])

    list_im = [AI_banner_image, logo_image, book_banner_image]
    caller_path = Path(inspect.stack()[1][1])
    print(f'{caller_path.name}: calculating banner images: {list_im}')
    print(list_im)
    imgs    = [ Image.open(i) for i in list_im ]
    # pick the image which is the smallest, and resize the others to match it (can be arbitrary image shape here)
    print(imgs)
    min_shape = sorted( [(np.sum(i.size), i.size ) for i in imgs])[0][1]
    print("minimum image shape is", min_shape)
    imgs_comb = np.hstack( (np.asarray( i.resize(min_shape) ) for i in imgs ) )

    # save that beautiful picture
    imgs_comb = Image.fromarray( imgs_comb)
    imgs_comb.save('resources/Trifecta.jpg' )    
    logo_image = 'resources/Trifecta.jpg'
    return logo_image, logo_caption

#st.cache_data
def create_date_variables():
    # what does the next line do?
    today = pd.to_datetime("today")
    today_str = today.strftime("%Y-%m-%d")
    
    thisyear = datetime.date.today().year
    thismonth = datetime.date.today().month
    this_year_month = str(thisyear) + '-' + str(thismonth)
    starting_day_of_current_year = datetime.date.today().replace(year=thisyear, month=1, day=1)
    daysYTD = datetime.date.today() - starting_day_of_current_year
    annualizer = 365 / daysYTD.days
    
    return today, thisyear, starting_day_of_current_year, daysYTD, annualizer, this_year_month

def df_get_most_popular_values_in_all_columns(df, n):
    for col in df.columns:
        print(col, end=' - \n')
        print('_' * 50)
        if col in ['Magnitude'] or is_categorical_dtype(col):
             return(pd.DataFrame(df[col].astype('str').value_counts().sort_values(ascending=False).head(n)))
        else:
            return (pd.DataFrame(df[col].value_counts().sort_values(ascending=False).head(n)))

@st.cache_data()
def df2csv(df):
   return df.to_csv().encode('utf-8')

def get_caller_path(text):
    caller_path = Path(inspect.stack()[1][1])
    print(f'{caller_path.name}: {text}')
    
def reorder_df_columns(df, cols_to_order=[]):
    new_columns = cols_to_order + (df.columns.drop(cols_to_order).tolist())
    df = df[new_columns]
    return df
 
# def detect_languages(text):
#     try:
#         model = _FastText(model_path="resources/models/lid.176.ftz")
#         text = re.sub(r"[\n]", "", text) # converts to giant blob
#         languages = model.predict(text, k=3)
#         logging.info(languages)
#         languages = f"{languages[0][0]}: {languages[1][0]}, {languages[0][1]}: {languages[1][1]}, {languages[0][2]}: {languages[1][2]}"
#         return languages
#     except Exception as e:
#         polyglot_message = "polyglot error" + str(e)
#         logging.error(polyglot_message)
#         return polyglot_message

def fix_escape_sequences_in_text(text):

    repaired = ftfy.fixes.decode_escapes(text)
    return repaired

def get_globbed_files_from_directory(directory, file_extension):
    files = glob.glob(directory + "/*." + file_extension)
    return files

def submit_guard():
    if "openai_key" not in st.session_state:
        st.session_state.openai_key = None
    if st.session_state.openai_key == "" or st.session_state.openai_key is None:
        st.error("Before submitting a request, you must enter an API key for OpenAI in the sidebar.")
        st.stop()
    return st.session_state.openai_key

def am_I_running_under_streamlit():
    try:
        if _get_websocket_headers():

            return True
    except Exception as e:
        return False

def smart_print(text, both=False):
    if am_I_running_under_streamlit():
        if both:
            logging.info(text)
            st.warning(text)
        else:
            st.info(text)
    else:
        logging.info
    return

def streamlit_display_info_about_venv():
    st.info("test")
    st.info(sys.path)
    st.info(sys.executable)
    st.info(sys.prefix)
    st.info(sys.version)
    st.info(sys.version_info)
    return


import pandas as pd
import chardet


def get_encoding(file):
    rawdata = open(file, "rb").read()
    result = chardet.detect(rawdata)
    return result['encoding']


def spreadsheet2df(file_path):
    # Determine file type from file object
    if file_path.endswith('.csv'):
        try:
            return pd.read_csv(file_path, encoding=get_encoding(file_path))
        except pd.errors.ParserError:
            pass

    try:
        return pd.read_excel(file_path, engine='openpyxl')
    except pd.errors.ParserError:
        traceback.print_exc()

    # If file type is not supported
    raise ValueError(f'Unsupported file type: {file_path}')

def dict2dict_with_truncated_values(input_dict, length_threshold):
    # Create a new dictionary to store the original keys with truncated values
    truncated_dict = {}
    # Iterate through the keys and values in the input dictionary
    for key, value in input_dict.items():
        try:
            # Check if the value has a length (e.g., a string)
            if len(value) > length_threshold:
                # Truncate the value to the specified length
                truncated_value = value[:length_threshold] + ' ...'
            else:
                # If the value is below the threshold, use it as is
                truncated_value = value
        except TypeError:
            # If the value does not have a length, use it as is
            truncated_value = value

        # Add the original key with the truncated value to the new dictionary
        truncated_dict[key] = truncated_value

    return truncated_dict


def get_environment_variables():
    import os
    env_variables = os.environ
    # sort
    env_variables = {k: env_variables[k] for k in sorted(env_variables)}

    return env_variables

# streamlit helper functions

def tree(dir_path: Path, prefix: str = ''):
    """A recursive generator, given a directory Path object
    will yield a visual tree structure line by line
    with each line prefixed by the same characters
    """
    contents = list(dir_path.iterdir())
    # contents each get pointers that are ├── with a final └── :
    pointers = [tee] * (len(contents) - 1) + [last]
    for pointer, path in zip(pointers, contents):
        yield prefix + pointer + path.name
        if path.is_dir():  # extend the prefix and recurse:
            extension = branch if pointer == tee else space
            # i.e. space because last, └── , above so no more |
            yield from tree(path, prefix=prefix + extension)

def get_dirs_inside_dir(folder):
    return [my_dir for my_dir in list(
        map(lambda x: os.path.basename(x), sorted(Path(folder).iterdir(), key=os.path.getmtime, reverse=True))) if
            os.path.isdir(os.path.join(folder, my_dir))
            and my_dir != '__pycache__' and my_dir != '.ipynb_checkpoints' and my_dir != 'API']

def list_folders_in_folder(folder):
    return [file for file in os.listdir(folder) if os.path.isdir(os.path.join(folder, file))]

def show_dir_tree(folder):
    with st.expander(f"Show {os.path.basename(folder)} folder tree"):
        for line in tree(Path.home() / folder):
            st.write(line)

def delete_folder(folder, ask=True):
    if not ask:
        shutil.rmtree(folder)
    else:
        folder_basename = os.path.basename(folder)
        if len(os.listdir(folder)) > 0:
            st.warning(f"**{folder_basename} is not empty. Are you sure you want to delete it?**")
            show_dir_tree(folder)
            if st.button("Yes"):
                try:
                    shutil.rmtree(folder)
                except:
                    st.error(f"Couldn't delete {folder_basename}:")
                    e = sys.exc_info()
                    st.error(e)
        else:
            st.write(f"**Are you sure you want to delete {folder_basename}?**")
            if st.button("Yes"):
                try:
                    shutil.rmtree(folder)
                except:
                    st.error(f"Couldn't delete {folder_basename}:")
                    e = sys.exc_info()
                    st.error(e)

        # Implementation

        col1_size = 10
        col1, col2 = st.columns((col1_size, 1))

        with col1:
            models_abs_dir = os.path.join(configs['APP_BASE_DIR'], configs['MODELS_DIR'])
            temp = []
            i = 0
            while temp != configs['CURRNET_FOLDER_STR'] and temp != configs['CREATE_FOLDER_STR']:
                i += 1
                state.files_to_show = get_dirs_inside_dir(models_abs_dir)
                temp = st.selectbox("Models' folder" + f": level {i}",
                                    options=[configs['CURRNET_FOLDER_STR']] + state.files_to_show
                                            + [configs['CREATE_FOLDER_STR']] + [configs['DELETE_FOLDER_STR']],
                                    key=models_abs_dir)
                if temp == configs['CREATE_FOLDER_STR']:
                    new_folder = st.text_input(label="New folder name", value=str(state.dataset_name) + '_' +
                                                                              str(state.model) + '_models',
                                               key="new_folder")
                    new_folder = os.path.join(models_abs_dir, new_folder)
                    if st.button("Create new folder"):
                        os.mkdir(new_folder)
                        state.files_to_show = get_dirs_inside_dir(models_abs_dir)
                elif temp == configs['DELETE_FOLDER_STR']:
                    if list_folders_in_folder(models_abs_dir):
                        chosen_delete_folder = st.selectbox(
                            label="Folder to delete", options=list_folders_in_folder(models_abs_dir),
                            key="delete_folders")
                        chosen_delete_folder = os.path.join(models_abs_dir, chosen_delete_folder)
                        delete_folder(chosen_delete_folder)
                        state.files_to_show = get_dirs_inside_dir(models_abs_dir)
                    else:
                        st.info('No folders found')
                elif not temp == configs['CURRNET_FOLDER_STR']:
                    models_abs_dir = os.path.join(models_abs_dir, temp)
            try:
                show_dir_tree(models_abs_dir)
            except FileNotFoundError:
                pass
            table = st.empty()
            try:
                files_in_dir = os.listdir(models_abs_dir)
                if ".gitignore" in files_in_dir:
                    files_in_dir.remove(".gitignore")
                table.write(models_table(files_in_dir))
            except FileNotFoundError:
                st.error("No 'saved_models' folder, you should change working dir.")
            except ValueError:
                pass
            except:
                e = sys.exc_info()
                st.info(e)


def directory_contains_subdirectory(path):
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_dir():
                return True
    return False


def load_spreadsheet(filename):
    """
    Load a spreadsheet file into a pandas DataFrame.

    Parameters:
    filename (str): File path to the spreadsheet.


    Returns:
    DataFrame: pandas DataFrame with the spreadsheet data.

    Try utf-8 encoding first for csv, then ISO-8859-1, then Win-1252

    """
    # Check the file extension
    _, extension = os.path.splitext(filename)

    if extension == '.csv':
        encoding_options = ['utf-8', 'ISO-8859-1', 'Win-1252']
        for encoding in encoding_options:
            try:
                df = pd.read_csv(filename, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

    elif extension == ".xlsx":
        df = pd.read_excel(filename, engine='openpyxl')

    elif extension == ".xls":
        df = pd.read_excel(filename)

    return df


def select_dataframe_rows_from_string(specs_df, rows_to_select):
    """
    Selects rows in a dataframe based on the given string value.

    Args:
        specs_df (DataFrame): The dataframe to select rows from.
        rows_to_select (str): The string value used to select rows.

    Raises:
        ValueError: If rows_to_select is not a string.

    Returns:
        DataFrame or None: The selected rows dataframe if rows are found,
        None otherwise.
    """
    if "select" not in specs_df.columns:
        specs_df["select"] = False  # replace some_default_value with value you want

    if not isinstance(rows_to_select, str):
        raise ValueError("rows_to_select must be a string")
    if rows_to_select:
        logging.info(f"Selecting rows in df based on string value {rows_to_select}")
        rows_list = parse_row_ranges(rows_to_select)
        logging.info(f"rows selected are {rows_list}")
        for row in rows_list:
            specs_df.at[row, 'select'] = True

    specs_df['select'] = specs_df['select'].astype('bool')
    logging.info(f"Selected {len(rows_list)} rows")
    selected_rows_df = specs_df[specs_df['select'] == True]
    logging.info(f"df with only selected_rows is")
    logging.info(selected_rows_df)
    logging.info("--- Leaving row selector function in utilties.py---")

    if selected_rows_df.count == 0:
        logging.warning('No rows selected')
        return
    else:
        return selected_rows_df


def parse_row_ranges(row_ranges):
    """
    Convert a string of number ranges into a list of integer numbers.

    Args:
    doc_ranges (str): A string containing row numbers and ranges, e.g., "1, 3-5, 7".

    Returns:
    list: A list of integers representing the row numbers.
    """
    if not isinstance(row_ranges, str):
        raise ValueError("row_ranges must be a string")
    else:
        rows = []
        for part in row_ranges.split(','):
            if '-' in part:
                start, end = part.split('-')
                rows.append(range(int(start), int(end) + 1))
            else:
                rows.append(int(part.strip()))
        logging.info("Parsed ranges: {}".format(rows))
        return rows


def safely_add_empty_column(specs_df, col):
    if col not in specs_df.columns:
        specs_df[col] = ''
    return specs_df


def create_safe_file_name(file_path):
    # Extract file name from given path
    file_name_with_extension = os.path.basename(file_path)
    # Remove extension
    file_name, _ = os.path.splitext(file_name_with_extension)
    # Replace special characters with _
    safe_file_name = re.sub('[^A-Za-z0-9]+', '_', file_name)

    return safe_file_name


def set_logging_level(log_level: str):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    logging.basicConfig(filename="logs/applications.log", level=numeric_level,
                        format='%(asctime)s - %(levelname)s - %(message)s')


def where_am_i_running_to_dict():
    modulename = __name__
    functionname = inspect.currentframe().f_code.co_name
    return modulename, functionname


def where_am_I_running_to_string(modulename, functionname):
    modulename = __name__
    functionname = inspect.currentframe().f_code.co_name
    return f"{modulename}:{functionname}"


def make_ISBN_and_title_safe(ISBN, title):
    if ISBN:
        # replace special characters with undersocres in ISBN
        ISBN_safe = re.sub(r'\W+', '_', ISBN)
        shortname = f"{ISBN_safe}"
    else:
        title_safe = re.sub(r'\W+', '_', ISBN)
        shortname = f"{title_safe}"
    return shortname


import logging


def configure_logger(log_level):
    # Create logger object
    # logger = logging.getLogger(__name__)
    logger = logging.getLogger("applications")
    # print(logger)

    # Set logger to handle all messages
    logger.setLevel(logging.DEBUG)

    for handler in logger.handlers[:]:  # list copy for iteration
        handler.close()
        logger.removeHandler(handler)

    # Create a file handler that handles all messages and writes them to a file
    file_handler = logging.FileHandler('logs/applications.log')
    file_handler.setLevel(logging.DEBUG)

    # Create a stream handler that handles only warning and above messages
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    formatter_string = '%(asctime)s - %(levelname)s - %(module)s - %(lineno)d: %(message)s'
    # Create formatter
    formatter = logging.Formatter(formatter_string)

    # Assign the formatter to the handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    numeric_level = console_handler.level

    # Convert numeric level to string
    level_name = logging.getLevelName(numeric_level)

    print(f"The level of the console handler is: {level_name}")
    print(f"the formatter string is {formatter_string}")

    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

