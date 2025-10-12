'''move catalog analysis to its own file'''
from app.utilities.text

2
isbnmeta
import text2goom2isbnmetadict
import pandas as pd


def check_if_titles_are_in_isbnlib(titlelist):
    catalog_results = text2goom2isbnmetadict(titlelist)
    return catalog_results


def process_catalog_analysis_results(title, author=None, publisher=None, keywords=None, language=None):
    catalog_results_list_of_dicts = []
    catalog_titles = []
    try:
        catalog_results_list_of_dicts = check_if_titles_are_in_isbnlib(metadatas['title'])
        print('catalog_results_list_of_dicts', catalog_results_list_of_dicts)
    except Exception as e:
        print('couldnae check isbnlib for catalog results', e)
    catalog_results_df = pd.DataFrame(catalog_results_list_of_dicts)
    if catalog_results_df is not None:
        catalog_title = catalog_results_df[0]['Title']
        isbn_title = catalog_results_df[0]['ISBN-13']
    else:
        print('catalog_results_list_of_dicts is empty')

    try:
        for c in catalog_titles:
            print(metadatas['title'], c)
            exactmatch = texts2exactmatch(metadatas['title'], c)
            if exactmatch:
                flipexactmatch = True
        for c in catalog_titles:
            #print(metadatas['title'], c)
            caseinsensitivematch = texts2caseinsensitivematch(metadatas['title'], c)
            if caseinsensitivematch:
                break
        for c in catalog_titles:
            print((metadatas['title'], c))
            fuzzymatch = texts2fuzzymatch(metadatas['title'], c)
            print(fuzzymatch)
            if fuzzymatch[0]:
                break
            
        print('exactmatch', exactmatch, 'caseinsensitivematch', caseinsensitivematch, 'fuzzymatch', fuzzymatch)
    except Exception as e:
        print("can't match title to catalog: " + filename, e)
    metadatas['exactmatch'] = exactmatch
    metadatas['caseinsensitivematch'] = caseinsensitivematch
    metadatas['fuzzymatch'] = fuzzymatch[0]
    metadatas['fuzzymatchscore'] = fuzzymatch[1]
    
    #print(catalog_results_list_of_dicts)
    catalog_results_df = pd.DataFrame(catalog_results_list_of_dicts)
    catalog_results_df.T.to_json(thisdoc_dir + '/' + 'isbnlib_matches.json')
    #print('catalog_results_df', catalog_results_df)
    metadatas['catalog_titles_found'] = str(catalog_titles)
    #metadatas['catalog_series'] = catalog_series
    if exactmatch or caseinsensitivematch or fuzzymatch[0]:
        metadescription = desc(isbn_title)
        metadatas['catalog_description'] = metadescription
        with open(thisdoc_dir + '/' + 'metadescription.json', 'w') as f:
            json.dump(metadescription, f)

    else:
    metadatas['catalog_description'] = 'NaN'