import csv

from isbnlib2dict import get_isbn_info_from_isbnlib

#import streamlit as st

filename = "app/data/BIP4streamlit.csv"
isbn_dicts_list = []
isbn_info_dict = {}
with open(filename, 'r') as f:
    # Read the csv file line by line
    reader = csv.reader(f)
    # Skip the header row
    next(reader)
    # Iterate over each row in the csv file
    for count, row in enumerate(reader):
        # Get the ISBN-13 from the row
        isbn_13 = row[14]
        print(isbn_13)

        isbn_info_dict = get_isbn_info_from_isbnlib(isbn_13)
        # Get the book description from isbnlib
        print(isbn_info_dict)
       # print(isbn_info_dict)
        #st.write(isbn_info_dict)
        print(count)
        #if count > 3:
        #    break
    # save the dict to a list
        isbn_dicts_list.append(isbn_info_dict)
    print(isbn_dicts_list)
# Write the list to a csv file
with open('app/data/add2BIPtruth.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['ISBN-13', 'Title', 'Author', 'Publisher', 'Year', 'lang','description', 'smallThumbnail', 'thumbnail'])
    for isbn_dict in isbn_dicts_list:
        writer.writerow(isbn_dict.values())
    