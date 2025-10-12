import argparse
import os

import pandas as pd

# from app.utilities.utilities import statcounter
from app.utilities.files2llamaindex import query_index, load_text_directory


def loop_through_directories_to_index(booksdir):
    list_of_indexes = []
    for book in os.listdir(booksdir):
        bookdir = booksdir + book
        if os.path.isdir(bookdir):
            print(bookdir)
            try:
                book_index = load_text_directory(bookdir)
            except Exception as e:
                print(e)
                continue
            list_of_indexes.append(book_index)
    return list_of_indexes


def loop_through_directories_to_query(list_of_directories, question):
    response_df = pd.DataFrame()
    list_of_responses = []
    for bookdir in list_of_directories:
        response = query_index(book_index, question)
        list_of_responses.append(response)
        response_df = response_df.append(response.get_formatted_sources())
    return list_of_responses, response_df


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--chapdir', '-C', type=str, default='test/text/269books/421-chapters')
    argparser.add_argument('--question', '-Q', type=str, default='What is the name of the book?')
    argparser.add_argument('--booksdir', '-B', type=str, default=None)
    args = argparser.parse_args()
    chapdir = args.chapdir
    question = args.question
    booksdir = args.booksdir
    book_index = None
    # build indexes
    if booksdir is None:
        book_index = load_text_directory(chapdir)
    else:
        loop_through_directories_to_index(booksdir)

    response = query_index(book_index, question)
    print(response.get_formatted_sources())
    print(response)
    # submit queries

    # if booksdir is None:
    #     response = query_index(book_index, question)
    #     print(response.get_formatted_sources())
    #     print(response)
    # else:
    #     list_of_responses, response_df = loop_through_directories_to_query(list_of_directories, question)
    #     print(response_df)


