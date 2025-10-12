# pipeline for end-to-end text processing of book manuscripts

# ------------------------- IMPORT MODULES -----------------------------------

import argparse
import glob
# standard modules
import os
import shutil
import subprocess
from pathlib import Path

print(os.environ['PYTHONPATH'])

# import app & flask modules


#from . import app
# import app modules

#from app.models.user_models import User, StripeCustomer, Role, UsersRoles, UserPromptForm, UserDocsForm, Presets, Tokens, Transactions, UploadForm, UserDocs, find_or_create_searchdocs, Journals
#from app import db, config

# third-party modules
#from transformers import GPT2TokenizerFast
#from flask_user import current_user
#from sqlalchemy.sql.functions import count

# import local third-party modules

#import app.utilities.DynamicGraphNetworks
#from DynamicGraphNetworks import chapterize
import app.utilities.DynamicGraphNetworks as DGN
print(dir(DGN))
#import app.utilities.DynamicGraphNetworks.src.third_party.chapterize as chapme

from app.utilities.DynamicGraphNetworks.src.third_party.chapterize import chapterize


""" # Load common settings
app.config.from_object('app.settings')
# Load environment specific settings
app.config.from_object('app.local_settings')
"""

# import Nimble AI modules

# from app.utilities.gpt3complete import gpt3complete
#from .s2orc.doc2json.pdf2json.process_pdf import process_pdf


#------------------------- GLOBAL VARIABLES --------------------------------
"""
stripe_keys = {
    "secret_key": os.environ["STRIPE_SECRET_KEY"],
    "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"],
    "price_id": os.environ["STRIPE_PRICE_ID"],
    "endpoint_secret": os.environ["STRIPE_ENDPOINT_SECRET"],
}
"""
#------------------------- CLASSES -------------------------------


#------------------------- FUNCTIONS --------------------------------------

def count_tokens(text):
    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    count_tokens = len(tokenizer(text)['input_ids'])
    return count_tokens
    

#------------------------- MAIN SCRIPT  ------------------------------------


if __name__ == '__main__':

    # set up logging

    # set up argparse

    parser = argparse.ArgumentParser()


    parser.add_argument('-i', '--input_files_list', help='list of file names to process', required=False, default = 'app/data/pipeline/filelist.txt')

    input_files_list = parser.parse_args().input_files_list

    print(input_files_list)

    # get file names from list

    # begin looping over file names
    
    # do processing of full text file
    # loop over files in a directory

    directory_extensions = 'app/data/pipeline/*.txt'
    for srcfilename in glob.iglob(directory_extensions, recursive=True):
        print(srcfilename)
        destfilename = 'app/utilities/DynamicGraphNetworks/data/raw_text' + '/' + Path(srcfilename).stem + '.txt'
        filenameonly = Path(srcfilename).stem
        shutil.copyfile(srcfilename, destfilename)

        os.chdir('app/utilities/DynamicGraphNetworks')
        subprocess.run(['python', 'main.py', "--book", filenameonly])
        os.chdir('../..')


        # option for running character analyzer with raw occ table

        # option for running character analyzer with edited occ table

    # do processing that requires text to be chunked
    chapters = chapterize('app/utilities/DynamicGraphNetworks/data/raw_text/' + line)
    
    for chapter in chapters:
        # less than 1500 tokens
        chapter_tokens = count_tokens(chapter)
        pass


    # do processing that requires text to be summarized under 1500 tokens


