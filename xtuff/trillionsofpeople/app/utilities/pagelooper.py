import argparse

import pandas as pd

from bulkprocesspdfs import text_df_to_ai_services
from pdf2pages2text import pdf_pages_to_list_of_text_strings


def main(filename, limit, output_dir):
    print("limit", limit)
    text = pdf_pages_to_list_of_text_strings(filename, limit=limit, output_dir="output")  # text is list of strings
    text_df = pd.DataFrame(text)
    page_by_page_results = text_df_to_ai_services(text_df, service="openai", presets=["tax_summarizer"])


    return page_by_page_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", type=str, default="working/public_domain/schmitz-batch-002/DJT2015.pdf")
    #parser.add_argument("--filename", type=str, default="test/pdf/DJTtax.pdf")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output_dir", type=str, default="output")
    args = parser.parse_args()
    results = main(args.filename, args.limit, args.output_dir)

    df = pd.DataFrame(results)
    df.to_excel("output/resultsdjt.xlsx")





