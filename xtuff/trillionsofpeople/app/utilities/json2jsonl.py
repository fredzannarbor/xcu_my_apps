import argparse
import json
import os

import pandas as pd
from doc2json.pdf2json.process_pdf import process_pdf_file

parser = argparse.ArgumentParser()
parser.add_argument("--infile", help = "seed file", default = 'utilities/s2orc/tests/pdf/2020.acl-main.207.pdf')

args = parser.parse_args()

filename = args.infile

temp_dir = 'utilities/s2orc/temp/'
output_dir = 'utilities/s2orc/output/'

def pdf2jsonl(filename):
    jsonfile = process_pdf_file(filename, temp_dir, output_dir)
    filepathname = os.path.splitext(filename)
    basename = os.path.splitext(os.path.basename(filename))[0]
    print(basename)
    # prepare filename to save 
    jsonfilename = output_dir + basename + '.json'
    data = json.load(open(jsonfilename))
    df = pd.DataFrame(data['pdf_parse']['body_text'])
    df1 = df[['text']]
    # prepare filename to save modified df
    jsonlfilename = output_dir + basename + '.jsonl'
    df1.to_json(jsonlfilename, orient="records", lines=True)
    return jsonlfilename

if __name__ == "__main__":
    pdf2jsonl(filename)