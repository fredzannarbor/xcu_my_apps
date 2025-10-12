import argparse
import json
import os

import pandas as pd
from pyzotero import zotero

from app.utilities.bulkprocesspdfs import text_df_to_ai_services
from app.utilities.zotero2json import process_zotero_results_to_list, process_zotero_results

zot = zotero.Zotero(
    os.environ["ZOTERO_LIBRARY_ID"],
    os.environ["ZOTERO_LIBRARY_TYPE"],
    os.environ["ZOTERO_API_KEY"],
)


# @st.cache_data()
def get_bibliography(
        collection_id="DZEEWBWC",
        style="chicago-annotated-bibliography",
        format="bib",
        content="bib",
        linkwrap="1",
        sort="date",
        limit="300",
        direction="asc"
):
    bibliography = zot.collection_items_top(
        collection_id,
        content=content,
        style=style,
        format=format,
        linkwrap=linkwrap,
        sort=sort,
        limit=limit,
        direction=dir
    )
    return bibliography

"""sort options

sort (str) – The name of the field by which entries are sorted: (dateAdded, dateModified, title, creator, type, date, publisher, publicationTitle, journalAbbreviation, language, accessDate, libraryCatalog, callNumber, rights, addedBy, numItems, tags)
direction (str) – asc or desc
limit (int) – 1 – 100 or None
start (int) – 1 – total number of items in your library or None
"""


def get_all_items_in_collection(collection_id):
    all_items = zot.all_collections(collection_id)
    listolists = [zot.collection_items(c['key']) for c in all_items]
    with open("output/zotero/" + "all_items.json", "w") as f:
        json.dump(listolists, f)

    return all_items

def run_items_through_openai(all_items):
    text_df = pd.DataFrame(all_items)


    return

def zotero_results_2_pdfs(results):
    # loop through the zotero results object
    # get the pdf if possible

    return


def process_pdfs(pdf_directory):
    # loop through each pdf in the directory
    # get the raw text
    # do a recursive summary
    # save the summary in a dictionary
    # save the dictionary in a json file
    # return the dictionary of summaries

    return


def assemble_book(summaries):
    # create front matter
    # loop through the summaries to create body
    # create back matter
    # assemble the book
    # save the book as docx pdf & epub
    # return

    return


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Get bibliography from Zotero collection"
    )

    argparser.add_argument("--collection_id", help="collection id", default="DZEEWBWC")
    argparser.add_argument(
        "--style", help="style", default="chicago-annotated-bibliography"
    )
    args = argparser.parse_args()
    collection_id = args.collection_id
    style = args.style
    results = get_bibliography(collection_id, format="", sort="date", )
    all_items_in_collection = get_all_items_in_collection(collection_id)  # pprint(resultss
    print(all_items_in_collection)

    print(len(results))
    for r in results:
        print(process_zotero_results(r))
        print("---")
    processed_results = process_zotero_results_to_list(results)
    with open("output/zotero/" + collection_id + '/' + "bibliography.txt", "w") as f:
        f.write(''.join(processed_results))
    print(len(processed_results))
    for p in processed_results:
        print(p)
    text_df = pd.DataFrame(all_items_in_collection)
    text_enhancements = text_df_to_ai_services(text_df, service="openai", presets="zotero2book_default")
    # loo

"""
# TODO: get the content each bibliograpny entry
# if there is an attachment already in the library, get it
# if there is no attachment, follow the url
# if the url is a PDF, get it
# if the url is a webpage, convert it to readable document
"""
# TODO: process each PDF or document using non-payservices
# TODO: process each PDF or document using payservices
