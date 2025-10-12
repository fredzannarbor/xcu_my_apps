import argparse
import glob
from os import environ, listdir, path, makedirs, stat

import pandas as pd
import streamlit as st
from internetarchive import search_items, download, get_item

username = environ["IA_USERNAME"]
password = environ["IA_PASSWORD"]
# configure(username, password)
import uuid


def lsla(path):
    list_of_files = filter(path.isfile,
                           glob.glob(path + '*'))
    # get list of ffiles with size
    files_with_size = [(file_path, stat(file_path).st_size)
                       for file_path in list_of_files]
    # Iterate over list of tuples i.e. file_paths with size
    # and print them one by one
    for file_path, file_size in files_with_size:
        print(file_size, ' -->', file_path)
    return files_with_size


def iametadata2productionspecs(item):
    item = get_item(item)
    st.write(item.metadata)
    # add columns to dataframe
    try:
        specs_cols = ['title', 'creator', 'date', 'subject', 'language', 'mediatype', 'Publisher-supplied Keywords',
                      'Publisher-supplied synopsis', 'filetype', 'filesize', 'fileformat', 'identifier', 'collection']
        specs_row = pd.DataFrame(columns=specs_cols)
        specs_row['title'] = item.metadata['title']
        specs_row['author'] = item.metadata['creator']
        specs_row['ISBN'] = ''

        specs_row['date'] = item.metadata['date']
        specs_row['language'] = item.metadata['language']
        specs_row['Publisher-supplied Keywords'] = item.metadata['subject']
        specs_row['Publisher-supplied synopsis'] = item.metadata['description']
        # specs_row['filename'] = item.metadata.files[0].name
        # specs_row['filetype'] = item.metadata.files[0].format
        # specs_row['filesize'] = item.metadata.files[0].size
        specs_row.to_csv('productionspecs.csv', mode='a', header=True, index=True)
        specs_row['publisher'] = item.metadata['publisher']
    except Exception as e:
        errormessage = f"Error saving specs_row: {e}"
        st.error(errormessage)
    return specs_row


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # optional arguments
    parser.add_argument("--ia_uniq_id", help="internet archive unique identifier", default="shouldbarackobam0000zimm")
    parser.add_argument("--search_phrase", help="search phrase", default="date:1927 AND mediatype:texts")
    args = parser.parse_intermixed_args()
    ia_uniq_id = args.ia_uniq_id
    search_phrase = args.search_phrase

with st.form(key='my_form'):
    search_phrase = st.text_input(label='Enter a search phrase')
    submit_button = st.form_submit_button(label='Submit')
    dfsearch = pd.DataFrame()
    if submit_button:

        st.write("You entered:", search_phrase)

        count = 0
        short_id = uuid.uuid4().hex[:6].upper()
        result = search_items(search_phrase)
        # save results to a json file for later use
        if len(result) == 0:
            st.warning("No results found")
        else:
            st.write(f"The answer set contains {len(result)} items.")
            row_df_dict = {}
            for item in result.iter_as_items():
                count += 1
                item_dict = item.metadata
                row_df_dict[count] = item_dict
                if count % 25 == 0:
                    st.write("Saved metadata for {} items so far.".format(count))
            st.write("### Metadata for {} items".format(count))
            st.write(row_df_dict)
            df_all_metadata = pd.DataFrame.from_dict(row_df_dict, orient='index')
            st.dataframe(df_all_metadata)# s
            df_all_metadata.to_excel('output/internetarchive/' + short_id + '_all.xlsx')# elect just the most readable columns
            # get all column names from df_all_metadata
            all_cols = df_all_metadata.columns
            # we want only these columns
            cols = ['identifier', 'title', 'creator', 'subject', 'date', 'description', 'language', 'mediatype',  'imagecount']
            # create a new dataframe with just these columns
            # if a column is not in the original dataframe, it will be filled with NaN
            df_specs_only = df_all_metadata[cols]
            st.write("### Metadata for {} items".format(count))
            st.dataframe(df_specs_only)
            df_specs_only.to_excel('output/internetarchive/' + short_id + '_specs.xlsx')


with st.form(key='download item'):
    text_input2 = st.text_input(label='Enter an item identifier')
    submit_button2 = st.form_submit_button(label='Get It')
    ia_uniq_id = text_input2
    lf = 'pdf'
    if submit_button2:
        st.write("You entered:", ia_uniq_id)
        # check if directory ∃
        if not path.exists("output/internetarchive/" + ia_uniq_id):
            makedirs("output/internetarchive/" + ia_uniq_id)
        download(ia_uniq_id, destdir="output/internetarchive/", verbose=True, glob_pattern="*.{}".format(lf))
        # download(ia_uniq_id, destdir="output/internetarchive/", verbose=True)
        # show file in os
        ls_result = listdir("output/internetarchive/" + ia_uniq_id + "/")
        st.write(ls_result)

        metadata = iametadata2productionspecs(ia_uniq_id)
        st.write(metadata)

    st.info("Now sending the document over to bulkprocesspdf")

