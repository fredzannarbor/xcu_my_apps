import argparse
import datetime
import glob
import inspect
import json
import os
import re
import subprocess
import traceback
from datetime import datetime
from inspect import currentframe
from pathlib import Path

import ftfy
import nltk
import pandas as pd
import spacy
import streamlit as st
import streamlit.components.v1 as components
import tiktoken
from docx2txt import docx2txt
from pandas.api.types import is_categorical_dtype
from pdfminer.high_level import extract_text
from rich.console import Console
from spacy.language import Language
from spellchecker import SpellChecker

encoding = tiktoken.get_encoding("p50k_base")
encoding35 = tiktoken.get_encoding("cl100k_base")
#from xls2xlsx import XLS2XLSX

console = Console(record=True)

from random import choice
from string import punctuation

import numpy as np
from PIL import Image
from fasttext.FastText import _FastText
from app.utilities.text2sumy_summarize import sumy_summarize

def get_info(obj):

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
    print('reading BIPdf from filename', filename)
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
    # drop index column if it exists
    if 'Unnamed: 0' in BIPdf.columns:
        BIPdf = BIPdf.drop(columns=['Unnamed: 0'])
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
    return LanguageDetector()
 
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



def cacheaware_summarizer(text, wordcount):

    summary = sumy_summarize(text, 20)
    sentences = nltk.sent_tokenize(summary)
    summary_sentence_list = []
    for sentence in sentences:
        summary_sentence_list.append(sentence)
    return summary_sentence_list

def spell_check_text(text):
    #remove all punctuations before finding possible misspelled words
  s = re.sub(r'[^\w\s]','',text)
  wordlist=s.split()
  spell = SpellChecker()
  misspelled = list(spell.unknown(wordlist))
  problemwordstuple = []
  for word in misspelled:
      thiswordtuple = spell.candidates(word, spell.correction(word), spell.candidates(word))
      problemwordstuple.append(thiswordtuple)
  return problemwordstuple


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
    return re.sub(r'[^\w\s]','',basename)

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
 
def detect_languages(text):
    try:
        model = _FastText(model_path="resources/models/lid.176.ftz")
        text = re.sub(r"[\n]", "", text) # converts to giant blob
        languages = model.predict(text, k=3)
        print(languages)
        languages = f"{languages[0][0]}: {languages[1][0]}, {languages[0][1]}: {languages[1][1]}, {languages[0][2]}: {languages[1][2]}"
        return languages
    except Exception as e:
        polyglot_message = "polyglot error" + str(e)

        return polyglot_message

def fix_escape_sequences_in_text(text):

    repaired = ftfy.fixes.decode_escapes(text)
    return repaired

def get_globbed_files_from_directory(directory, file_extension):
    files = glob.glob(directory + "/*." + file_extension)
    return files