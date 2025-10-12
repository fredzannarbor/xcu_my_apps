import argparse
import os
import re
from os import path

import fitz
import pandas as pd
import spacy
# from cv2 import add
import streamlit as st
import yake
from nameparser import HumanName as hn
from numeral import int2roman

# rom pdf2pages2text import tokenize_text_removing_new_lines_inside_sentences
from app.utilities.text2spacyner import extract_NER_from_text


# currently relies on hard-coded list of index terms

def find_named_entities(pdf_file_path, pages_limit=1200):
    entities = find_entities_as_candidate_index_terms(pdf_file_path, pages_limit)
    entities_found = str(len(entities)) + " total entities found"
    st.write(entities_found)
    left, middle, right, far_right = st.columns([3, 3, 3, 4])
    df_entities = pd.DataFrame(entities)
    df_entities.columns = ["text", "label_", "explanation"]
    # st.write(df_entities.describe())
    left.markdown("""*Entities by label_ type*""")
    left.write(df_entities["label_"].value_counts())
    df_entities.to_csv("output/entities.csv")

    # select rows with label_ == 'PERSON'
    df_entities_person = df_entities[df_entities["label_"] == "PERSON"]
    # get unique values from text column

    persons_list = df_entities_person["text"].unique()
    print(type(persons_list))
    # .tolist()
    # persons_list.sort()
    persons = "\n".join(persons_list)
    return


def create_keyword_list_yake(filename, output_dir):
    text = ""
    word_count = 100000  # reasonable default
    number_of_pages = 300  # reasonable default
    index_page_entry_count = 100  # landscape 11 x 8.5
    index_verbosity = 200  # range from 10 to 1000, with 10 being the most verbose
    doc = fitz.open(filename)  #
    print(doc.page_count)

    try:
        print("successfully opened pdf in create_yake", pdf_file_path)

    except Exception as e:
        print("error opening pdf", e)
    try:
        print(doc.page_count)
        for page in doc:
            print(page.get_text())
            text += page.get_text()
        # length of doc in pages
        number_of_pages = len(doc)
        word_count = len(text.split())

        print("successfully extracted text to single file")
        word_list = text.split()#
        word_count = len(word_list)

    except Exception as e:
        print("error in extracting text to single file", e)
    keyword_list = []

    target_number_of_pages = number_of_pages / index_verbosity
    target_number_of_index_entries = round(
        (target_number_of_pages * index_page_entry_count)
    )

    print(
        number_of_pages,
        word_count,
        index_verbosity,
        target_number_of_pages,
        target_number_of_index_entries,
    )
    print("target number of index entries", target_number_of_index_entries)
    # per MIT Press
    # https://mitpress.mit.edu/sites/default/files/quicklinks/2017-08/indexing_instructions_for_authors_0.pdf
    # p.3  says between 1/50 and 1/20 index pages per text page
    language = "en"
    max_ngram_size = 3
    deduplication_thresold = 0.9
    deduplication_algo = "seqm"
    windowSize = 1
    numOfKeywords = target_number_of_index_entries
    custom_kw_extractor = yake.KeywordExtractor(
        lan=language,
        n=max_ngram_size,
        dedupLim=deduplication_thresold,
        dedupFunc=deduplication_algo,
        windowsSize=windowSize,
        top=numOfKeywords,
        features=None,
    )
    keywords = custom_kw_extractor.extract_keywords(text)
    for count, kw in enumerate(keywords):
        print(kw)
        if count % 100 == 0:
            print("created ", count, "keywords")
        keyword_list.append(kw)
    # save keyword list of tuples to file as strings
    with open(output_dir + "/" + "keyword_list.txt", "w") as f:
        # each kw on one line
        for item in keyword_list:
            kw = item[0]
            print(kw)
            f.write("%s\n" % kw)
    #print(keyword_list)
    # sleep(5)
    return keyword_list


def find_new_mwes_by_regex_rules(filename, lookaheadlimit):
    print(type(lookaheadlimit))
    lookaheadlimit = int(lookaheadlimit)
    recommended_mwes_untokenized = (
        []
    )  # list of string multiple word index phrases: ["AKAGI MARU","air superiority"]
    count = 0
    print(filename)
    doc = fitz.open(filename)  #
    print(doc.page_count)
    try:
        print("successfully opened pdf in mwe", pdf_file_path)

        text = ""
        rules = ["[A-Z]* MARU", "(USS [A-Z]+\s?\\b [A-Z]+)", "(USS [A-Z]{2,})", "(HMS [A-Z]+\s?\\b [A-Z]+)",
                 "(HMS [A-Z]{2,})"]  # type: ignore
        # rules = ["[A-Z]* MARU", "(USS [A-Z]+\s?\\b [A-Z]+)"]
        print("hardcoded regexes to find recommended multiword expressions in text")
        print(rules)

        for count, page in enumerate(doc, 1):
            print("page", page)
            text = page.get_text()
            print("converting page", count, "to text")
            print(text)
            for rule in rules:
                # print(rule)
                result = re.compile(rule).findall(text)
                # print('result for searching page', count, 'for rule', rule, result)
                if result:
                    # get unique items from result list
                    for item in result:
                        if item not in recommended_mwes_untokenized:
                            recommended_mwes_untokenized.append(item)

            if count == lookaheadlimit:
                break
    except Exception as e:
        print("error in find_new_mwes_by_regex_rule", e)

    # save lookahead terms to file
    with open(output_dir + "/" + "recommended_mwes_untokenized.txt", "w") as f:
        for item in recommended_mwes_untokenized:
            f.write("%s\n" % item)

    return recommended_mwes_untokenized


def identify_mwe_terms(pdf_file_path=None, mwe_terms_filepath=None):
    st.info("arrived in identify_mwe_terms")
    mwe_search_terms = []
    if mwe_terms_filepath is not None:
        if os.path.exists(mwe_terms_filepath):
            st.info("found mwe_terms_filepath")
            with open(mwe_terms_filepath, "r") as f:
                print("reading mwe terms file", mwe_terms_filepath)
                for line in f:
                    mwe_search_terms.append(line.strip())
                # print('mwe terms specific to this book are', mwe_search_terms)
            st.write("mwe terms specific to this book are", mwe_search_terms)
            return mwe_search_terms
        else:
            print("no prepared mre_terms file, building list")

            mwe_search_terms = find_new_mwes_by_regex_rules(
                pdf_file_path, lookaheadlimit=10
            )
            print("mwe terms found by regex search are", mwe_search_terms)
    return mwe_search_terms


def find_entities_as_candidate_index_terms(filename, pages_limit=1200):
    # print(type(lookaheadlimit))

    entities = (
        []
    )  # list of string multiple word index phrases: ["AKAGI MARU","air superiority"]
    count = 0
    print(filename)

    try:
        doc = fitz.open(filename)  #
        print(doc.page_count)
        message = "opened " + pdf_file_path +\
                  " successfully"
        print(message)
        #st.info(message)
    except Exception as e:
        print("error opening pdf", e)

    for count, page in enumerate(doc, 1):
        text = page.get_text()
        result = extract_NER_from_text(text)
        if result:

            for item in result:
                if item.text not in entities:
                    explanation = str(spacy.explain(item.label_))
                    appendthis = {
                        "text": item.text,
                        "label": item.label_,
                        "explanation": explanation,
                    }
                    entities.append(appendthis)
                else:
                    pass
        if count == pages_limit:
            #st.info("breaking")
            break
    df_entities = pd.DataFrame(entities)
    df_entities.columns = ["text", "label_", "explanation"]
    df_entities.to_csv("output/entitiesinfx.csv")
    df_entities_person = df_entities[df_entities["label_"] == "PERSON"]
    persons_list = df_entities_person["text"].unique().tolist().sort()
    new_persons_list = []
    print(persons_list)
    if persons_list:
        for person in persons_list:
            search_list_for_person = expand_person_to_search_term_list(person)
            #st.write("for person", person, "found search term list", search_list_for_person)
            new_persons_list.append(search_list_for_person)

    return df_entities  # , new_persons_list


def expand_person_to_search_term_list(fullname):
    name = hn(fullname)
    namedict = name.as_dict(False)
    st.write(namedict)
    lastname = name.last
    titlename = name.title + " " + name.last
    nminame = name.last + " " + name.first
    st.write(fullname, lastname, titlename, nminame)
    search_term_list = [fullname, titlename, nminame, lastname]
    return search_term_list


def search_pdf_pages_with_list_of_search_synonyms(pdf_file_path, search_terms_list, searchpageslimit):
    index_term_occurrence_dict = {}
    converted_page_and_text_list = []
    with fitz.open(pdf_file_path) as doc:  # type: ignore

        for count, page in enumerate(doc, 1):

            if count % 50 == 0:
                infomessage = (
                        "processing page " + str(count) + " of " + str(doc.page_count)
                )
                print(infomessage)
            text = page.get_text()
            page_text_pair = {"page": count, "text": text}
            converted_page_and_text_list.append(
                page_text_pair)  # save the converted page/text pairs for future reference

            # tokenizer = MWETokenizer()
            # mwetext = tokenizer.tokenize(text.split())
            # displayinfo = "tokenized text is " + str(mwetext)

            addentry = []
            for term in search_terms_list:
                # list_status = str(list[0])
                # print('processing list of search synonyms beginning with index entry ' + list_status)
                if str(term) in text:  # mwetext
                    termfound = 'search term ' + term + ' found in text on page ' + str(count)
                    if term not in index_term_occurrence_dict:
                        addpage = [count]
                        addentry = {term: addpage}
                        index_term_occurrence_dict.update(addentry)
                    else:
                        current_pages_in_index_entry_root = index_term_occurrence_dict[term]
                        current_pages_in_index_entry_root.append(count)
                else:
                    pass

            if count == searchpageslimit:
                print("search pages limit reached")
                break
        print('search complete, cleaning up index term occurrence dict')
    index_term_occurrence_dict_clean = {}
    for key, value in index_term_occurrence_dict.items():
        index_term_occurrence_dict_clean[key.replace("_", " ")] = value
    print('reach end of search_pdf_pages_with_list_of_search_synonyms')
    return index_term_occurrence_dict_clean, converted_page_and_text_list

# def search_pdf_pages_from_search_term_df(pdf_file_path, search_terms_df, searchpageslimit):
#     index_term_occurrence_dict = {}
#     converted_page_and_text_list = []
#     with fitz.open(pdf_file_path) as doc:  # type: ignore
#
#         for count, page in enumerate(doc, 1):
#
#             if count % 50 == 0:
#                 infomessage = (
#                         "processing page " + str(count) + " of " + str(doc.page_count)
#                 )
#                 print(infomessage)
#             text = page.get_text()
#             page_text_pair = {"page": count, "text": text}
#             converted_page_and_text_list.append(
#                 page_text_pair)  # save the converted page/text pairs for future reference
#
#             # tokenizer = MWETokenizer()
#             # mwetext = tokenizer.tokenize(text.split())
#             # displayinfo = "tokenized text is " + str(mwetext)
#
#             addentry = []
#             for term in search_terms_df[index_header]:
#                 # list_status = str(list[0])
#                 # print('processing list of search synonyms beginning with index entry ' + list_status)
#                 if str(term) in text:  # mwetext
#                     termfound = 'search term ' + term + ' found in text on page ' + str(count)
#                     if term not in index_term_occurrence_dict:
#                         addpage = [count]
#                         addentry = {term: addpage}
#                         index_term_occurrence_dict.update(addentry)
#                     else:
#                         current_pages_in_index_entry_root = index_term_occurrence_dict[term]
#                         current_pages_in_index_entry_root.append(count)
#                 else:
#                     pass
#
#             if count == searchpageslimit:
#                 print("search pages limit reached")
#                 break
#         print('search complete, cleaning up index term occurrence dict')
#     index_term_occurrence_dict_clean = {}
#     for key, value in index_term_occurrence_dict.items():
#         index_term_occurrence_dict_clean[key.replace("_", " ")] = value
#     print('reach end of search_pdf_pages_with_list_of_search_synonyms')
#     return index_term_occurrence_dict_clean, converted_page_and_text_list
#

def indexresults2indexentries(index_dict_results):
    terms2entries = {}
    terms2entries = {
        "terms": ["Nimitz", "Chester Nimitz", "Admiral Chester Nimitz"],
        "entries": "Nimitz, Admiral Chester",
    }
    return


def process_index_dict_results(
        index_dict, output_dir, front_matter_last_page, unnumbered_front_matter_pages_list=[0, 1, 3],
        do_not_index_these_pages_list=[0, 1, 2, 3]
):
    pages = 0

    # save index_dict to properly formatted text
    # note first step is to convert from logical page numbers in PDF
    # to physical page numbers as they would be printed in the book
    # this is the *only* output from this program that has printed book style numbering

    for key, value in index_dict.items():
        skip_these_pages = unnumbered_front_matter_pages_list + do_not_index_these_pages_list
        for i, page in enumerate(value):
            if int(page) <= int(front_matter_last_page):
                if page in skip_these_pages:
                    value[i] = None
                else:
                    value[i] = int2roman(page, only_ascii=True).lower()
            else:
                value[i] = int(page) - int(front_matter_last_page)
            print(value[i])

        index_dict[key] = value

    with open(path.join(output_dir, "index_dict_physical_page_numbers.txt"), "w") as f:
        for key, value in sorted(index_dict.items()):
            pages = ", ".join(str(x) for x in value)
            f.write(key + "\t" + str(pages) + "\n")

    infomessage = "successfully indexed PDF document " + "after converting digital to printed page numbering " + " and saved to output directory " + str(
        output_dir)
    print(infomessage)
    return index_dict  # , pages


if __name__ == "__main__":

    argparser = argparse.ArgumentParser("process pdf pages for an index")
    argparser.add_argument(
        "--pdf_file_path",
        help="path to pdf file",
        default="/Users/fred/bin/nimble/unity/app/data/test.pdf",
    )
    argparser.add_argument("-i", "--input", help="path to input file", default="/Users/fred/bin/nimble/unity/app/data/test.pdf")
    argparser.add_argument(
        "--output_dir", help="path to output directory", default="output"
    )
    argparser.add_argument("--lookaheadlimit", help="limit", default=1000)
    argparser.add_argument("--searchpageslimit", help="searchpageslimit", default=1000)
    argparser.add_argument(
        "--index_term_file_path",
        help="path to index term file",
        default="/Users/fred/bin/nimble/unity/app/data/book-specific-index-terms.txt",
    )
    argparser.add_argument(
        "--front_matter_last_page", "-P", help="path to index term file", default=12
    )
    argparser.add_argument(
        "--unnumbered_front_matter_pages",
        help="list of unnumbered pages in front matter",
        default=[2],
    )
    argparser.add_argument(
        "--mwe_terms_filepath",
        help="path to book-specific multiple word encodings file",
        default="/Users/fred/bin/nimble/unity/app/data/mweterms.txt",
    )
    argparser.add_argument(
        "--rule_file_path",
        help="path to rule file",
        default="/Users/fred/bin/nimble/unity/app/data/rules.json",
    )
    argparser.add_argument("--final_search_terms", "-F", help="path to text file of final search terms", default=None)
    argparser.add_argument('--book_specific_search_terms', help='list of book specific search terms', default="")
    args = argparser.parse_args()

    pdf_file_path = args.input#pdf_file_path
    mwe_terms_filepath = args.mwe_terms_filepath
    output_dir = args.output_dir
    # max number of pages in target PDF to process
    lookaheadlimit = args.lookaheadlimit
    searchpageslimit = args.searchpageslimit

    print(lookaheadlimit, searchpageslimit)

    index_term_file_path = args.index_term_file_path

    # last roman numbered front matter page, used for offsetting page values
    front_matter_last_page = args.front_matter_last_page

    # certain pages in front matter are always unnumbered and should not be included, this is a list of them
    unnumbered_front_matter_pages = args.unnumbered_front_matter_pages
    final_search_terms = args.final_search_terms
    #
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    else:
        print("output directory already exists")

    # identify keywords that are candidates for indexing
    unsupervised_keyword_list = create_keyword_list_yake(pdf_file_path, output_dir)
    print(unsupervised_keyword_list)
    keywords = [x[0] for x in unsupervised_keyword_list]
    # write list of tuples to file with one item per line
    with open(path.join(output_dir, "unsupervised_keyword_list.txt"), "w") as f:
        for item in unsupervised_keyword_list:
            f.write(item[0] + "\t" + str(item[1]) + "\n")
            #exit()
    # identify multi word expressions in the text
    mwe_search_terms = []
    if os.path.exists(mwe_terms_filepath):
        with open(mwe_terms_filepath, "r") as f:
            print("reading mwe terms file", mwe_terms_filepath)

            for line in f:
                try:
                    print(line.strip())
                    if line.strip() != "":
                        mwe_search_terms.append(line.strip())
                except Exception as e:
                    print("error reading line", line, e)
    else:
        print("no prepared mre_terms file, building list")
        mwe_search_terms = find_new_mwes_by_regex_rules(pdf_file_path, lookaheadlimit)
        print("mwe terms found by regex search are", mwe_search_terms)
    with open(path.join(output_dir, "mwe_search_terms.txt"), "w") as f:
        for item in mwe_search_terms:
            f.write("%s" % item)

    # identify named entities in the text
    entities = []
    try:
        entities_df = find_entities_as_candidate_index_terms(pdf_file_path, lookaheadlimit)
        # drop duplicate rows
        entities_df.drop_duplicates(inplace=True)
        print("entities found by spacy are", entities_df)
        entities_df.to_csv(path.join(output_dir, "entities1.csv"))
        print(entities_df.columns)
        selected_rows = entities_df[entities_df['label_'].isin(["PERSON", "PRODUCT", "ORG", "LOC"])]
        selected_rows.to_csv(path.join(output_dir, "entities2.csv"))
    except Exception as e:
        print("Exception while finding entities: " + str(e))

    # get all unique values of 'text' where label_ == PRODUCT
    products = entities_df[entities_df['label_'] == "PRODUCT"]['text'].unique().tolist()
    facilities = entities_df[entities_df['label_'] == "FAC"]['text'].unique().tolist()

    # union of unsupervised keywords, mwe terms and named entities
    print("keywords", keywords)

    unified_search_terms = keywords + products + mwe_search_terms
    print(len(unified_search_terms))
    print("unified_search_terms", unified_search_terms)

    if final_search_terms is not None:
        with open(final_search_terms, "r") as f:
            for line in f:
                unified_search_terms.append(line.strip())
    else:
        final_search_terms = unified_search_terms

    page_search_results = search_pdf_pages_with_list_of_search_synonyms(
        pdf_file_path, final_search_terms, searchpageslimit
    )
    index_dict = page_search_results[0]
    index_list_of_pages = page_search_results[1]
    index_list_of_pages_df = pd.DataFrame(index_list_of_pages)
    index_list_of_pages_df.to_csv(path.join(output_dir, "index_list_of_pages.csv"))
    with open(path.join(output_dir, "index_dict.txt"), "w") as f:
       # save index_tuple to file:
       for key, value in sorted(index_dict.items()):
            pages = ", ".join(str(x) for x in value)
            f.write(key + "\t" + str(pages) + "\n")

    with open(path.join(output_dir, "index_list_of_pages.txt"), "w") as f:
        for page_dict  in index_list_of_pages:
            f.write(str(page_dict) + "\n")

    try:
        results = process_index_dict_results(index_dict, output_dir, front_matter_last_page)
    except Exception as e:
        print("Exception in processing index dict: " + str(e))

    print(len(results))
    with open(path.join(output_dir, "index_dict_results.txt"), "w") as f:
        for key, value in sorted(results.items()):
            pages = ", ".join(str(x) for x in value)

            f.write(key + "\t" + str(pages) + "\n")
