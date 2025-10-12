import argparse
import json
import os

import requests
from fitz import open as fitz_open
from pyzotero import zotero

zot = zotero.Zotero(
    os.environ["ZOTERO_LIBRARY_ID"],
    os.environ["ZOTERO_LIBRARY_TYPE"],
    os.environ["ZOTERO_API_KEY"],
)

# @st.cache_data()
def get_zotero_bibliography(
        collection_id="DZEEWBWC",
        style="chicago-annotated-bibliography",
        format="bib",
        content="bib",
        linkwrap="1",
        sort="date",
        limit="300",
):
    AI4booklovers_bibliography = zot.collection_items_top(
        collection_id,
        content=content,
        style=style,
        format=format,
        linkwrap=linkwrap,
        sort=sort,
        limit=limit,
    )
    # st.write(AI4booklovers_bibliography)
    return AI4booklovers_bibliography


"""sort options

sort (str) – The name of the field by which entries are sorted: (dateAdded, dateModified, title, creator, type, date, publisher, publicationTitle, journalAbbreviation, language, accessDate, libraryCatalog, callNumber, rights, addedBy, numItems, tags)
direction (str) – asc or desc
limit (int) – 1 – 100 or None
start (int) – 1 – total number of items in your library or None
"""


def get_semantic_scholar_by_keyword(keyword_phrase):
    # get the semantic scholar results for the keyword phrase
    # return the results
    request_url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={keyword_phrase}&sort=relevance&per_page=100'
    response = requests.get(request_url)
    return response.json()


def open_better_bibtex_json(filename):
    # open the better bibtex json file
    # return the json object
    with open(filename) as f:
        collection_data = json.load(f)
    return collection_data

def zotero_results_2_pdfs(results):
    # loop through the zotero results object
    # get the pdf if possible

    return


def process_collection_data(collection_data):
    # loop through the collection data
    for item in collection_data['items']:
        print(item['title'], item['attachments'][0]['path'])
        realpath = '/Users/fred/Downloads/5GW/' + str(item['attachments'][0]['path'])
        with open(realpath, 'rb') as f:
            doc = fitz_open(stream=f.read(), filetype="pdf")
            a = doc.page_count
            print(a)
            all_text = []
            for count, page in enumerate(doc, 1):
                text = page.get_text()
                print(text)
                print('')
                all_text = all_text.append(text)
            print(all_text[0])
        print('-------')
        # get the semantic scholar results for the keyword phrase
    return

def get_dois_from_zotero_collection(collection_data):
    dois = []
    count = 0
    for item in collection_data['items']:
        print(count)
        print(item["title"])
        # check if item has key "DOI"
        if "DOI" in item:
            print(item["DOI"])
            dois.append(item["DOI"])
        count += 1
    return dois


def assemble_book(summaries):
    # create front matter
    # loop through the summaries to create body
    # create back matter
    # assemble the book
    # save the book as docx pdf & epub
    # return

    return


def get_clean_list_of_citations(bibtex_file):
    # open the bibtex file
    with open(bibtex_file) as f:
        bibtex_string = f.read()
    # clean the bibtex file
    # return the list of citations

    return dois


def get_pdfs_by_doi(dois):
    # loop through the dois
    # get the pdf from semantic scholar
    # return the pdfs
    return pdfs


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
    collection_id = (
        "DZEEWBWC"  # for AI for book-lovers N3EXZ3VT for referring to Nimble # for 5GW 6F586UIT
    )
    # process_collection_data(open_better_bibtex_json('/Users/fred/Downloads/5GW/5GW.json'))
    # try:
    #     dois = get_dois_from_zotero_collection(open_better_bibtex_json('/Users/fred/Downloads/5GW/5GW.json'))
    # except Exception as e:
    #     print(e)
    #     print("couldn't get dois from collection data")
    # print(len(dois))
    # exit()
    try:
        ssresults = get_semantic_scholar_by_keyword("5GW")
        print(ssresults)
        print(len(ssresults['data']))
    except Exception as e:
        print('failure on ss get' + str(e))

    # results = get_zotero_bibliography(collection_id, format="", sort="creator")
# print(results)
