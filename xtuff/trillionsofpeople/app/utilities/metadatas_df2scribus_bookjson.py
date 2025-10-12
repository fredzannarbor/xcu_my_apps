import pandas as pd


def create_bookjson_for_scribus(metadatas_df, thisdoc_dir):
    # writes the book.json file that my Scribus program, lsicover.py, wants to ingest

    df = pd.DataFrame()

    '''
    Need to update bulkpdfprocess to generate the fields on right hand column, most of which are not currently in metadatas_df
    '''
    df['ImprintText'] = metadatas_df['imprint']
    df['distributor'] = metadatas_df['distributor']
    df['trimsizewidth'] = metadatas_df['trimsizewidth']
    df['trimsizeheight'] = metadatas_df['trimsizeheight']
    df['spinewidth'] = metadatas_df['spinewidth']
    df['dominantcolor'] = metadatas_df['dominantcolor']
    df['invertedcolor'] = metadatas_df['invertedcolor']

    df['BookTitle'] = metadatas_df['final_title']
    df['SubTitle'] = metadatas_df['subtitle']
    byline_text = metadatas_df['final_author'] + "\nEnhanced by AI"
    df['Byline'] = byline_text
    backtext = metadatas_df['BookDescription'] + metadatas_df['Back Cover Blurb']
    df['backtext'] = backtext
    output_file_path = thisdoc_dir + "/bookspecs.json"
    df.to_json(output_file_path, orient='records', lines=True)
    return df
