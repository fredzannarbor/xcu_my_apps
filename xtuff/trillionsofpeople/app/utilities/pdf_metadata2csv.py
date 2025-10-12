from __future__ import print_function

import argparse
import csv

import fitz


def pdf_metadata2csv(filename, output_dir, cumulative_filename, delimiter):
    doc = fitz.open(filename)
    meta = doc.metadata
    records = []
    ext = filename[-3:].lower()
    filename1 = filename[:-4] + "-meta.csv"
    # outfile = open(filename1, "w")
    cumulative_file_path = output_dir + '/jobcontrol/' + cumulative_filename
    # cumulative_file = open(cumulative_file_path, "a")
    for k in meta.keys():
        v = meta.get(k)
        #print(k, v)
        if not v:
            v = ""
        record = delimiter.join([k, v])
        
        # save record to file as row
        records.append(record)
    #print('records', records)
    rows = zip(records)   
    #print(*rows)
    with open(cumulative_file_path, "a") as f1:
        writer = csv.writer(f1)
        for row in rows:
            print(row)
            writer.writerow(row)
    print('filename1: ' + filename1)
    with open(filename1, 'w') as f2:
        writer = csv.writer(f2)
        for row in rows:
            writer.writerow(row)

    f2.close()
    return meta

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Enter CSV delimiter [;] and document filename")
    parser.add_argument('--delimiter', help='CSV delimiter [;]', default = ';')
    parser.add_argument('--output_dir', help='output directory', default='working/output_dir')
    parser.add_argument('--filename', help='document filename')
    parser.add_argument('--cumulative_filename', help='cumulative filename', default = 'cumulative_metadata.csv')
    args = parser.parse_args()
    output_dir = args.output_dir
    delimiter = args.delimiter             # requested CSV delimiter character
    filename = args.filename
    cumulative_file_name = args.cumulative_filename


    pdf_metadata2csv(filename, output_dir, cumulative_file_name, delimiter)
