from __future__ import print_function

import argparse
import csv
import json

import fitz


def pdfmetadata2dict(filename):
    doc = fitz.open(filename)
    metadata_dict = doc.metadata

    # print('records', records)

    return metadata_dict


def pdfmetadata2json(filename):
    doc = fitz.open(filename)
    metadata_dict = doc.metadata
    metadata_text = json.dumps(metadata_dict)
    #print('records', records)
    
    return metadata_text

def pdfmetadata2csv(filename, metadata_csv_filename):
    doc = fitz.open(filename)
    metadata_dict = doc.metadata
    # write dict to csv
    with open(metadata_csv_filename, 'w') as csvfile:        
        fieldnames = metadata_dict.keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(metadata_dict)
            #print('records', records)   
    return 

def pdfgetlistoftoc(filename, simple=True):
    doc = fitz.open(filename)
    toc = doc.getToC(simple=simple)
    print('toc', toc)
    return toc

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Enter CSV delimiter [;] and document filename")
    parser.add_argument('--delimiter', help='CSV delimiter [;]', default = ';')
    parser.add_argument('--output_dir', help='output directory', default='working/output_dir')
    parser.add_argument('--filename', help='document filename', default='test/pdf/Lorem_all_arabic.pdf')
    parser.add_argument('--cumulative_filename', help='cumulative filename', default = 'cumulative_metadata.csv')
    parser.add_argument('--thisdoc_dir', help='thisdoc_dir', default = 'output/thisdoc_dir')
    args = parser.parse_args()
    output_dir = args.output_dir
    delimiter = args.delimiter             # requested CSV delimiter character
    filename = args.filename
    cumulative_file_name = args.cumulative_filename
    thisdoc_dir = args.thisdoc_dir
    metadata_csv_filename =  (thisdoc_dir + '/' + 'metadata.csv')

    print(pdfmetadata2dict(filename))
    print(pdfmetadata2json(filename))
    print(pdfmetadata2csv(filename, metadata_csv_filename))
    print(pdfgetlistoftoc(filename))
