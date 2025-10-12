import argparse
import json

import pandas as pd

'''
convert edited JSON file to CSV file
include keys from the JSON file as columns in the CSV file
'''
def json2csv(path_to_json_file, path_to_csv_file):
    with open(path_to_json_file, 'r') as f:
        json_file = json.load(f)
    df = pd.DataFrame(json_file)
    df.to_csv(path_to_csv_file, index=False)
    return

def jsonl2csv(path_to_jsonl_file, path_to_csv_file):
    df = pd.read_json(path_to_jsonl_file, lines=True)
    df.to_csv(path_to_csv_file, index=False)
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--path_to_json_file", type=str, required=True)
    parser.add_argument("-o", "--path_to_csv_file", type=str, required=True)
    parser.add_argument("-t", "--file_type", type=str, required=True)
    args = parser.parse_args()
    #print(args)
    path_to_json_file = args.path_to_json_file
    path_to_csv_file = args.path_to_csv_file

    if args.file_type == 'json':
        json2csv(path_to_json_file, path_to_csv_file)
    if args.file_type == 'jsonl':
        jsonl2csv(path_to_json_file, path_to_csv_file)

