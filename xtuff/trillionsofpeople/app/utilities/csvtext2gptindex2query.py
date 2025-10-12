import argparse
import logging
import sys
from pathlib import Path
from timeit import default_timer as timer

import openai
from gpt_index import GPTListIndex, download_loader

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

PandasCSVReader = download_loader("PandasCSVReader")
loader = PandasCSVReader()
openai.api_base = "https://oai.hconeai.com/v1"


def load_PandasCSV(filepath, output_dir):
    documents = loader.load_data(filepath)
    index = GPTListIndex(documents)
    #index_with_query = GPTTreeIndex(documents, summary_template=SUMMARY_PROMPT)
    output_target = output_dir + "/" + Path(filepath).stem + ".index"
    index.save_to_disk(output_target)
    return index


def query_index(index, searchphrase):
    return index.query(searchphrase)




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="path to input file of page/text pairs", default="test/csv/test.csv")
    parser.add_argument("-q", "--query_str", help="query string",
                        default="Create an extremely concise, factual, accurate, insightful summary of the main points of this document.")
    parser.add_argument("-o", "--output", help="path to output index file", default="test/indexes")
    args = parser.parse_args()

    if args.input:
        # print(input)
        index_timer = timer()
        index = load_PandasCSV(args.input, args.output)
        index_time_elapsed = timer() - index_timer
        print(f"Indexing time: {index_time_elapsed}")
    if args.query_str and args.input:
        # logging.info(f"Querying index with {args.query_str}")
        response_timer = timer()

        response = index.query(args.query_str)
        response_time_elapsed = timer() - response_timer
        print(f"Response time: {response_time_elapsed}")
        print(response)
