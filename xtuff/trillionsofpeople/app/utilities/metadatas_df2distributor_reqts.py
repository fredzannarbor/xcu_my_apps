import json
from datetime import datetime, timedelta
from textwrap import shorten

import math
import pandas as pd
from currency_converter import CurrencyConverter

rendition_costs_df = pd.read_csv('resources/data_tables/LSI/rendition_costs.csv')


def book_metadata_json2distributor_format_targets(distributor_format_target="LSI", thisdoc_dir=''):
    with open("resources/json/book_metadata_objects.json", "r") as f:
        book_metadata_objects = json.load(f)
        # print(book_metadata_objects)

    KDP_targets = book_metadata_objects[1]["KDP required fields"]
    LSI_targets = book_metadata_objects[2]["LSI required fields"]
    LSI_ACS_required_fields = book_metadata_objects[3]["LSI ACS required fields"]

    return KDP_targets, LSI_targets, LSI_ACS_required_fields


def find_first_tuesday(year, month, day):
    d = datetime(year, int(month), 7)
    offset = -d.weekday()  # weekday = 0 means monday
    return d + timedelta(offset)
# find first tuesday of next month
def find_first_tuesday_of_next_month(year, month, day):
    d = datetime(year, int(month), 7)
    offset = -d.weekday()  # weekday = 0 means monday
    return d + timedelta(offset + 28)

# find tuesday N weeks ahead
def find_tuesday_N_weeks_ahead(year, month, day, N):
    d = datetime(year, int(month), 7)
    offset = -d.weekday()  # weekday = 0 means monday
    return d + timedelta(offset + (N*7))

def initialize_LSI_ACS_variables(metadatas_df):
    rendition_booktype_pair = 'POD: 8.5 x 11 in or 280 x 216 mm Case Laminate on White'
    LSI_ACS_publisher = 'W. Frederick Zimmerman'
    imprint = 'Nimble Books LLC'
    usd2gbp = 0.88  # create function
    safeISBN = str(metadatas_df['ISBN'].replace('-', '', regex=True)[0])
    jacket_filepath = ''
    interior_filepath = safeISBN + '_interior.pdf'
    cover_filepath = safeISBN + '_cover.pdf'
    return rendition_booktype_pair, LSI_ACS_publisher, imprint, usd2gbp, jacket_filepath, interior_filepath, cover_filepath


def get_LSI_ACS_keywords(metadatas_df, source="Keywords"):
    if source == "keywords":
        keywords = metadatas_df['Keywords'].values[0].split(';')
        keywords = [keyword.lstrip('\n') for keyword in keywords]
        return keywords
    if source == "Bibliographic Keyword Phrases":
        keywords = metadatas_df['Bibliographic Keyword Phrases'].values[0]
        print('bkb keywords: ', keywords)
        keywords = [keyword.lstrip('\n') for keyword in keywords]
        # drop first item in list
        keywords = keywords[1:]
        # convert keywords to string
        keywords = ';'.join(keywords)
        return keywords
    # otherwise, gets keywords from arbitrary field in metadatas_df
    keywords = metadatas_df[source].values[0][1].split(';')
    keywords = [keyword.lstrip('\n') for keyword in keywords]
    keyphrases = []
    for keyword in keywords:
        keyword_characters = 0
        for k in keywords:
            # get all characters preceding next ;
            # keyphrase = k.split(';')[0]
            keyword_characters += len(k.split(';')[0])
            if keyword_characters > 250:
                break
            keyphrases.append(k)
        print(len(keyphrases), 'keyphrases: ', keyphrases, 'keyword_characters: ', keyword_characters)
        return keyphrases


def estimate_price(rendition_costs_df, rendition_costs_index, pagecount, color_interior, profit_goal=10):
    if pagecount is not None:
        rendition_cost_index = int(rendition_costs_index)

        printing_cost = rendition_costs_df.iloc[rendition_costs_index, 2] + (pagecount *
                                                                             rendition_costs_df.iloc[
                                                                                 rendition_costs_index, 3])  # 2 is unit cost, 3 is cost per page
        recommended_price = (profit_goal + printing_cost) / 0.7
        return recommended_price

    else:
        return 99.00


def get_recommended_BISAC_categories(metadatas_df):
    try:
        BISACs = metadatas_df['Recommended BISAC Categories'].values[0][1].split(';')
    except Exception as e:
        metadatas_df['Recommended BISAC Categories'] = "TBD"
        print(e)
    BISACs = metadatas_df['Recommended BISAC Categories'].values[0][1].split(';')
    BISACs = [BISAC.lstrip('\n') for BISAC in BISACs]
    controlled_vocabulary_BISACs = []
    for b in BISACs:
        # look up BISAC codes in BISACs.json
        # use fuzzy matching to get controlled vocabulary values
        newBISACpair = {'BISAC': b, 'controlled vocabulary': 'TBD'}
        # print('not yet able to fuzzy match BISAC codes')
        controlled_vocabulary_BISACs.append(newBISACpair)
    print(f"found {len(BISACs)} BISACs exactly matching controlled vocabulary")
    return BISACs, controlled_vocabulary_BISACs

def get_rendition_booktype_pair(metadatas_df):
    # KISS version
    height, width = metadatas_df['pageheights'][0], metadatas_df['pagewidths'][0]
    print('height: ', height, 'width: ', width)
    if height == 8.5 and width == 11.0:
        rendition_booktype_pair = 'POD: 8.5 x 11 in or 280 x 216 mm Case Laminate on White'
    else:
        rendition_booktype_pair = 'Add trim size & paper type to csv'
    return rendition_booktype_pair

def create_draft_book_description(metadatas_df):
    try:
        print(metadatas_df['Foreword'][0])
        print(metadatas_df['Book Description'][0][1])
        print(metadatas_df['Book Cover Blurb'][0][1])
        print(metadatas_df['description_of_annotations'][0])
        book_description = "**DRAFT** \n" + metadatas_df['Foreword'][0] + '\n' + metadatas_df['Book Description'][0][1] + '\n' + metadatas_df['Book Cover Blurb'][0][1] + '\n ' + metadatas_df['description_of_annotations'][0]
    except Exception as e:
        print('Exception: ', e)
        print('couldna assemble bd')
        #zabook_description = "**DRAFT** \n" + metadatas_df['Book Description'][1] + '\n' + metadatas_df['Book Cover Blurb'][1] + '\n ' + metadatas_df['description_of_annotations'][1]

    return book_description
def create_LSI_ACS_spreadsheet(metadatas_df, LSI_ACS_required_fields, config=None):
    rendition_booktype_pair, LSI_ACS_publisher, imprint, usd2gbp, jacket_filepath, interior_filepath, cover_filepath = initialize_LSI_ACS_variables(
        metadatas_df)
    #metadatas_df['Parent ISBN'] = metadatas_df['ISBN'] # LSI has concept of Parent ISBN
    #print('metadatas_df: ', metadatas_df['Parent ISBN'])
    c = CurrencyConverter(fallback_on_missing_rate=True)
    df = pd.DataFrame(index=range(1))
    #df["Lightning Source Account #"] = "6024045"
    #df["Metadata Contact Dictionary"] = "Fred Zimmerman"
    df['Parent ISBN'] = metadatas_df['ISBN'].replace('-', '', regex=True)[0]
    df['ISBN or SKU'] = metadatas_df['ISBN'].replace('-', '', regex=True)[0]  # config needed
    rendition_booktype_pair = get_rendition_booktype_pair(metadatas_df)
    df['Rendition /Booktype'] = rendition_booktype_pair
    df['Title'] = metadatas_df['title'][0]
    df['Publisher'] = "W. Frederick Zimmerman"  # LSI_ACS_publisher  # working
    df['Imprint'] = "Nimble Books LLC"  # working
    df['Cover/Jacket Submission Method'] = 'FTP'  # done
    df['Text Block SubmissionMethod'] = 'FTP'  # done
    df['Contributor One'] = metadatas_df['author'][0]
    df['Contributor One Role'] = "A"  # lookup contributor_role_
    # function to decide on rendition costs index
    df['Reserved 1'] = ""  # done
    df['Reserved 2'] = ""  # done
    df['Reserved 3'] = ""  # done
    df['Reserved 4'] = ""  # done
    df['Custom Trim Width (inches)'] = "NA"  # done
    df['Custom Trim Height (inches)'] = "NA"  # done
    df['Weight(Lbs)'] = "NA"  # done

    df['Reserved5'] = ""  # done
    df['Reserved6'] = ""  # done
    df['Reserved7'] = ""  # done
    df['Reserved8'] = ""  # done
    # TODO: write function to extract front cover image from cover PD
    df['Marketing Image'] = ''# 'resources/images/placeholder-page001.jpeg'
    df['Pages'] = metadatas_df['final page count'][0]
    pub_date = calculate_pub_date()
    df['Pub Date'] = pub_date  # metadatas_df['publication date']
    df['Street Date'] = ''  # metadatas_df['publication date']
    df['Territorial Rights'] = 'World'  # informational # done
    contributing_editor = "Hildy Johnson [AI]" # default
    if contributing_editor is not None:
        df['Contributor Two'] = contributing_editor
        df['Contributor Two Role'] = "U"
    else:
        df['Contributor Two'] = ''
        df['Contributor Two Role'] = ''
    df['Contributor Three'] = ''
    df['Contributor Three Role'] = ''
    df['Edition Number'] = ''
    international_edition = False
    if international_edition == True:
        edition_name = 'Global Edition'
        df['Edition Description'] = edition_name
    else:
        df['Edition Description'] = ''
    try:
        df['Jacket Path / Filename'] = jacket_filepath
        df['Interior Path / Filename'] = interior_filepath
        df['Cover Path / Filename'] = cover_filepath
    except Exception as e:
        print(f"Exception: {e}")


    try:
        metadatas_df['Annotation / Summary'] = create_draft_book_description(metadatas_df)
        df['Annotation / Summary'] = metadatas_df['Annotation / Summary']
    except Exception as e:
        print(e)
        df['Annotation / Summary'] = ''
        print("problem creating book description draft ")
    df['Reserved (Special Instructions)'] = ''  # done
    df['LSI Special Category  (please consult LSI before using'] = ''
    df['Stamped Text LEFT'] = ''
    df['Stamped Text CENTER'] = ''  # done
    df['Stamped Text RIGHT'] = ''  # done
    df['Order Type Eligibility'] = 'POD-Distribution & Short Run'  # done
    df['Returnable'] = False  # done
    recommended_BISAC_categories = get_recommended_BISAC_categories(metadatas_df)[0]
    if len(recommended_BISAC_categories) > 0:
        df['BISAC Category'] = recommended_BISAC_categories[0]
    else:
        df['BISAC Category'] = 'N/A'
    df['Language Code'] ="English"
    df['LSI FlexField1 (please consult LSI before using)'] = ''  # done
    df['LSI FlexField2 (please consult LSI before using)'] = ''  # done
    df['LSI FlexField3 (please consult LSI before using)'] = ''  # done
    df['LSI FlexField4 (please consult LSI before using)'] = ''  # done
    df['LSI FlexField5 (please consult LSI before using)'] = ''  # done
    df['Reserved11'] = ''  # done
    df['Reserved12'] = ''  # done
    if len(recommended_BISAC_categories) == 1:
        df['BISAC Category 2'] = ''
        df['BISAC Category 3'] = ''
    if len(recommended_BISAC_categories) == 2:
        df['BISAC Category 2'] = recommended_BISAC_categories[1]
        df['BISAC Category 3'] = ''
    if len(recommended_BISAC_categories) > 2:
        df['BISAC Category 2'] = recommended_BISAC_categories[1]
        df['BISAC Category 3'] = recommended_BISAC_categories[2]
    df['Publisher Reference ID'] = ''
    df['Reserved9'] = ''
    df['Reserved10'] = ''
    df['Carton Pack Quantity'] = ''  # never going to need this
    df['Contributor One BIO'] = ' '
    df['Contributor One Affiliations'] = ' '
    df['Contributor One Professional Position'] = ' '
    df['Contributor One Location'] = ' '
    df['Contributor One Location Type Code'] = ' '
    df['Contributor One Prior Work'] = ' '
    #st.write('testing metadatas_df', metadatas_df)
    recommended_keywords = get_LSI_ACS_keywords(metadatas_df, "Bibliographic Keyword Phrases")
    df['Keywords'] = recommended_keywords
    # TODO: write function to recommend THEMA parameters
    df['Thema Subject 1'] = ''
    df['Thema Subject 2'] = ''
    df['Thema Subject 3'] = ''
    df['Regional Subjects'] = ''
    df['Audience'] = 'General/Trade' # other options include "Young Adult"
    calculate_min_max_age_grade(df)
    df['Short Description'] = shorten(metadatas_df['TLDR'][0][1], 250) # need new preset
    toc_string = process_acrobat_toc(metadatas_df)

    df['Table of Contents'] = toc_string # need new function
    df['Review Quote(s)'] = ''  # need new function
    df['# Illustrations'] = '' \
                            '' # in future count number of "Figure" captions in text
    df['Illustration Notes'] = ''
    df['Series Name'] = ''
    df['# in Series'] = ''
    rci = 3  # hardcoded for now
    us_list_price = estimate_price(rendition_costs_df, rci, metadatas_df['pagecount'], metadatas_df['color_interior'], profit_goal=10)[
        0]
    us_list_price = math.ceil(us_list_price) - 0.01
    print(f"us_list_price: {us_list_price}")
    df['US Suggested List Price'] = us_list_price  # metadatas_df['recommended price']
    # round up to nearest 0.01
    uk_list_price = round(us_list_price * usd2gbp, 2)
    uk_list_price = math.ceil(uk_list_price) - 0.01
    df['UK Suggested List Price'] = uk_list_price  # calculate in future
    df['UK Wholesale Discount (%)'] = 30

    eu_list_price = round(us_list_price * c.convert(1, 'USD', 'EUR'), 2)
    df['EU Suggested List Price (mode 2)'] = eu_list_price
    df['EU Wholesale Discount % (Mode 2)'] = 30

    au_list_price = round(us_list_price * c.convert(1, 'USD', 'AUD'), 2)
    df['AU Suggested List Price (mode 2)'] = au_list_price
    df['AU Wholesale Discount % (Mode 2)'] = 30

    ca_list_price = round(us_list_price * c.convert(1, 'USD', 'CAD'), 2)
    df['CA Suggested List Price (mode 2)'] = ca_list_price
    df['CA Wholesale Discount % (Mode 2)'] = 30

    df['GC Suggested List Price (mode 2)'] = us_list_price
    df['GC Wholesale Discount % (Mode 2)'] = 30

    gcdict = {"USBR1 Suggested List Price (mode 2)": us_list_price, "USBR1 Wholesale Discount % (Mode 2)": 30,
              "USDE1 Suggested List Price (mode 2)": us_list_price, "USDE1 Wholesale Discount % (Mode 2)": 30,
              "USRU1 Suggested List Price (mode 2)": us_list_price, "USRU1 Wholesale Discount % (Mode 2)": 30,
              "USPL1 Suggested List Price (mode 2)": us_list_price, "USPL1 Wholesale Discount % (Mode 2)": 30,
              "USCN1 Suggested List Price (mode 2)": us_list_price, "USCN1 Wholesale Discount % (Mode 2)": 30,
              "USKR1 Suggested List Price (mode 2)": us_list_price, "USKR1 Wholesale Discount % (Mode 2)": 30,
              "USIN1 Suggested List Price (mode 2)": us_list_price, "USIN1 Wholesale Discount % (Mode 2)": 30,
              "USJP2 Suggested List Price(mode 2)" : us_list_price, "USJP2 Wholesale Discount % (Mode 2)": 30,
              "UAEUSD Suggested List Price (mode 2)": us_list_price, "UAEUSD Wholesale Discount % (Mode 2)": 30,
              "US-Ingram-Only* Suggested List Price (mode 2)" : '', "US-Ingram-Only* Wholesale Discount % (Mode 2)": '',
              "US - Ingram - GAP * Suggested List Price (mode 2)": '', "US - Ingram - GAP * Wholesale Discount % (Mode 2)": '',
              "SIBI - EDUC - US * Suggested List Price(mode 2)" : '', "SIBI - EDUC - US * Wholesale Discount % (Mode 2)": ''}
    gcdf = pd.DataFrame(gcdict, index=[0])
    #print(gcdf.shape)

    df = pd.concat([df, gcdf], axis=1, sort=False)
    #print(df.shape)
    print(df.columns)
    print(df)
    return df


def process_acrobat_toc(metadatas_df):
    toc_list_of_lists = metadatas_df['toc']
    toc_list_of_strings = []
    count = 0
    # loop through enumerated items in toc_list_of_lists
    for item in toc_list_of_lists[0]:
        level = item[0]
        value = item[1]
        if level == 1:
            print(f"level: {level}, value: {value}")
            toc_list_of_strings.append(value)
        if level == 2:
            print(f"level: {level}, value: {value}")
            toc_list_of_strings.append(f"    {value}")
    toc_string = '\n'.join(toc_list_of_strings)
    # try using OpenAI to summarize toc
    # try converting to markdown then taking top 2 levels


def calculate_min_max_age_grade(df):
    if df['Audience'][0] == 'Young Adult':
        df['Min Age'] = 13
        df['Max Age'] = 18
        df['Min Grade'] = 8
        df['Max Grade'] = 12
    elif df['Audience'][0] == 'Children/Juvenile':
        df['Min Age'] = 0
        df['Max Age'] = 12
        df['Min Grade'] = 0
        df['Max Grade'] = 7
    else:
        df['Min Age'] = ''
        df['Max Age'] = ''
        df['Min Grade'] = ''
        df['Max Grade'] = ''


def calculate_pub_date():
    current_month = datetime.now().month
    # get current year
    current_year = datetime.now().year
    # get current day
    current_day = datetime.now().day
    next_month = current_month + 1
    pub_date = find_first_tuesday_of_next_month(current_year, current_month, current_day)
    return pub_date


def prepare_for_KDP_data_entry(metadatas_df):
    df = metadatas_df
    KDP_fields = book_metadata_json2distributor_format_targets("KDP")
    # create df columns using KDP_fields
    for field in KDP_fields:
        df[field] = ""
    # fill in df columns using KDP_fields
    df['Title'] = metadatas_df['title']

    return
