import argparse
import os
from pprint import pprint

import streamlit as st
from bs4 import BeautifulSoup
from pyzotero import zotero

from src.codexes.core.utilities.webapp import read_markdown_file

zot = zotero.Zotero(
    os.environ["ZOTERO_LIBRARY_ID"],
    os.environ["ZOTERO_LIBRARY_TYPE"],
    os.environ["ZOTERO_API_KEY"],
)


# @st.cache_data()
def get_AI_bibliography(
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
    #st.write(AI4booklovers_bibliography)
    return AI4booklovers_bibliography

"""sort options

sort (str) – The name of the field by which entries are sorted: (dateAdded, dateModified, title, creator, type, date, publisher, publicationTitle, journalAbbreviation, language, accessDate, libraryCatalog, callNumber, rights, addedBy, numItems, tags)
direction (str) – asc or desc
limit (int) – 1 – 100 or None
start (int) – 1 – total number of items in your library or None
"""

def process_zotero_results(results):
    r = "".join(results)  # now it is a string
    soup = BeautifulSoup(r, "lxml")
    t = []
    body = ""
    for div in soup.findAll("div", {"class": "csl-entry"}):
        annotation = ""

        for viv in div.find_all("div", {"class": "csl-block"}):
            # extra = viv.text
            # remove the csl-block div
            if viv.text.startswith("WFZ"):  # save the content of csl-block
                annotation = "_" + viv.text[4:] + "_"
                viv.decompose()
                # div now contains no csl-block plus annotation
            else:  # don't save the content of csl-block at all
                # remove viv element from div
                viv.decompose()
                # div now contains no csl-block and no annotation

        # body = div.contents[:-1]
        bodytext = div.text[:-1]
        t.append(bodytext)
        t.append(annotation)
        t.append("***")
    t1 = "\n".join(t).replace("\n", "\n\n")
    return t1


def process_zotero_results_to_list(results):
    r = "".join(results)  # now it is a string
    soup = BeautifulSoup(r, "lxml")
    t = []
    body = ""
    for div in soup.findAll("div", {"class": "csl-entry"}):
        annotation = ""

        for viv in div.find_all("div", {"class": "csl-block"}):
            # extra = viv.text
            # remove the csl-block div
            if viv.text.startswith("WFZ"):  # save the content of csl-block
                annotation = "_" + viv.text[4:] + "_"
                viv.decompose()
                # div now contains no csl-block plus annotation
            else:  # don't save the content of csl-block at all
                # remove viv element from div
                viv.decompose()
                # div now contains no csl-block and no annotation

        # body = div.contents[:-1]
        bodytext = div.text[:-1]
        t.append(bodytext)
        t.append(annotation)
        t.append("***")
    return t


def zotero2stexpander(title, collection_id, markdown_file, expanded=True, sort="date"):
    with st.expander(title, expanded=expanded):
        results = get_AI_bibliography(collection_id, sort=sort)  # retrieved JSON in chronological order
        t1 = process_zotero_results(results)
        sortmessage = "Collection Id: " + collection_id + " | " + "Sorted by " + sort
        st.caption(sortmessage)

        if markdown_file is not None:
            introduction = read_markdown_file(markdown_file)
            st.markdown(introduction)
        
        st.markdown(t1, unsafe_allow_html=True) 
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
    collection_id = (
        "DZEEWBWC"  # for AI for book-lovers N3EXZ3VT for referring to Nimble
    )
    results = get_AI_bibliography(collection_id, format="", sort="creator")
    pprint(results)
