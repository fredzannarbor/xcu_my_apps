import os
from datetime import timedelta

import pandas as pd
import pypandoc
import streamlit as st
import re
from bs4 import BeautifulSoup

"""
Selected helper utilities for the FinancialReportingObjects class module
"""

def clean_text(text):
    # Remove special characters but keep basic punctuation
    cleaned = re.sub(r'[^\x00-\x7F]+', '', text)
    # Remove HTML tags
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    # Replace multiple spaces with single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

def clean_html_content(html_text):
    if pd.isna(html_text):  # Handle NaN/None values
        return html_text
    # Parse HTML and extract text
    soup = BeautifulSoup(str(html_text), 'html.parser')
    # Get text content without HTML tags
    text = soup.get_text()
    # Clean up whitespace
    text = ' '.join(text.split())
    return text

def count_all_keys(d):
    count = 0
    if isinstance(d, dict):
        count += len(d)
        for value in d.values():
            if isinstance(value, (dict, list)):
                count += count_all_keys(value)
    elif isinstance(d, list):
        for item in d:
            if isinstance(item, (dict, list)):
                count += count_all_keys(item)
    return count

def count_authors(data):
    if not isinstance(data, dict):
        return 0

    if "authors" not in data:
        return 0

    authors = data["authors"]
    if isinstance(authors, dict):
        return len(authors)
    elif isinstance(authors, list):
        return len(authors)
    return 0

def count_keys_at_level(data, target_level, current_level=1):
    """
    Count the number of keys at a specific level in a nested structure.

    Args:
        data: The nested dictionary/list structure to analyze
        target_level: The level at which to count keys (1 is top level)
        current_level: Internal tracker for recursion (default=1)

    Returns:
        int: Number of keys at the specified level
    """
    count = 0

    if target_level < 1:
        raise ValueError("Level must be 1 or greater")

    if target_level == current_level:
        if isinstance(data, dict):
            return len(data)
        elif isinstance(data, list):
            return sum(len(item) for item in data if isinstance(item, dict))
        return 0

    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, (dict, list)):
                count += count_keys_at_level(value, target_level, current_level + 1)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                count += count_keys_at_level(item, target_level, current_level + 1)

    return count



def load_spreadsheet(filename):
    """
    Load a spreadsheet file into a pandas DataFrame.

    Parameters:
    filename (str): File path to the spreadsheet.


    Returns:
    DataFrame: pandas DataFrame with the spreadsheet data.

    Try utf-8 encoding first for csv, then ISO-8859-1, then Win-1252

    """
    # Check the file extension
    _, extension = os.path.splitext(filename)

    if extension == '.csv':
        encoding_options = ['utf-8', 'ISO-8859-1', 'Win-1252']
        for encoding in encoding_options:
            try:
                df = pd.read_csv(filename, encoding=encoding, dtype={'ISBN': str})


                break
            except UnicodeDecodeError:
                continue

    elif extension == ".xlsx":
        df = pd.read_excel(filename, engine='openpyxl', dtype={'ISBN': str})

  # check if there are multiple sheets

        sheets_dict = pd.read_excel(filename, sheet_name=None)
        if "Combined Sales" in sheets_dict:
            df = sheets_dict["Combined Sales"]
            return df


    elif extension == ".xls":
        df = pd.read_excel(filename, engine='xlrd', )

    return df



def add_amazon_buy_links(df):
    df['amazon_buy_link'] = 'https://www.amazon.com/dp/' + df['isbn_10_bak'].astype(str) + '?tag=internetbookinfo-20'
    return df


@st.cache_data
def last_day_of_month(any_day):
    # this will never fail
    # get close to the end of the month for any day, and add 4 days 'over'
    next_month = any_day.replace(day=28) + timedelta(days=4)
    # subtract the number of remaining 'overage' days to get last day of current month, or said programattically said, the previous day of the first of next month
    return next_month - timedelta(days=next_month.day)


def md_author_report_to_pdf(report_md, output_file_name="LSI_Author_Reports.pdf"):
    # use pypandoc convert
    try:
        pypandoc.convert_text(report_md, "pdf", "markdown", outputfile=output_file_name)
        st.success("successfully created pdf")
    except RuntimeError as e:
        print(f"An error occurred: {e}")
