
'''
Class create a book series
Input: textual description of a book series and optional parameters
Output: a book series object

Create high-level title requirements that all books in the series must meet:
- genre
- word count
- audience
- alignment with series theme
Create a series of ideas for books in the series
Create a list of possible characters in the series
Create a list of possible locations in the series
Create a list of possible events in the series
Create a list of possible themes in the series
Create a list of possible McGuffins in the series
Create a list of possible plot twists in the series

Allow the user to select which book ideas to use for the book series
For each book, assign a title, description, and order
For each book, assign a list of related characters, locations, events, themes, McGuffins, and plot twists

'''
import os
from random import sample, randint

import openai
import pandas as pd
import streamlit as st

from app.utilities.gpt3complete import chatcomplete

# openai.api_key = os.getenv("OPENAI_API_KEY")
print(openai.api_key)

openai.api_base = os.getenv("OPENAI_API_BASE")

class BookSeries:
    def __init__(self, description="", model="gpt-3.5-turbo", title_requirements=None, ideas=None, characters=None,
                 locations=None,
                 events=None,
                 themes=None, mcguffins=None, plot_twists=None, books=None, genre=None, word_count=None, audience=None,
                 universe="Earth-1218"):
        self.description = description
        self.ideas = ideas
        self.characters = characters
        self.locations = locations
        self.events = events
        self.themes = themes
        self.mcguffins = mcguffins
        self.plot_twists = plot_twists
        self.books = books
        self.title_requirements = title_requirements
        self.genre = genre
        self.word_count = word_count
        self.audience = audience
        self.universe = universe


    def get_description(self):
        return self.description

    def set_description(self, new_description):
        self.description = new_description

    def get_title_requirements(self):
        return self.title_requirements

    def set_title_requirements(self, new_title_requirements):
        self.title_requirements = new_title_requirements

    def get_ideas(self, description, model="gpt-3.5-turbo"):
        try:
            # st.write("description: ", description)
            ideas_response_text = chatcomplete("IdeasForBookSeries", description, engine=model)
            st.json(ideas_response_text, expanded=False)
            ideas_result = ideas_response_text,
        except Exception as e:
            print(e)
            ideas_response_text = "Error"
            ideas_result = "Error: " + str(e)
        return ideas_result

    def set_ideas(self, new_ideas):
        self.ideas = new_ideas

    def get_characters(self):
        return self.characters

    def set_characters(self, new_characters):
        self.characters = new_characters

    def get_locations(self):
        return self.locations

    def set_locations(self, new_locations):
        self.locations = new_locations

    def get_events(self):
        return self.events

    def set_events(self, new_events):
        self.events = new_events

    def get_themes(self):
        return self.themes

    def set_themes(self, new_themes):
        self.themes = new_themes

    def set_word_count(self, new_word_count):
        self.word_count = new_word_count

    def set_universe(self, new_universe):
        self.universe = new_universe

    def get_universe(self):
        return self.universe

    def get_mcguffins(self):
        return self.mcguffins

    def set_mcguffins(self, new_mcguffins):
        self.mcguffins = new_mcguffins

    def get_plot_twists(self):
        return self.plot_twists

    def set_plot_twists(self, new_plot_twists):
        self.plot_twists = new_plot_twists

    def get_books(self):
        return self.books

    def set_books(self, new_books):
        self.books = new_books

    def add_book(self, book):
        self.books.append(book)

    def remove_book(self, book):
        self.books.remove(book)

    def get_book_count(self):
        return len(self.books)

    def get_book_by_order(self, order):
        for book in self.books:
            if book.get_order() == order:
                return book

    def get_book_by_title(self, title):
        for book in self.books:
            if book.get_title() == title:
                return book

    def convert_ideas_result_to_dataframe(self, ideas_result, description):
        ideas = ideas_result.split("\n")
        ideas_df = pd.DataFrame(ideas, columns=['idea'])
        # drop empty rows
        ideas_df = ideas_df[ideas_df['idea'].notna()]
        words = description.split(" ")
        short_code = '-'.join(sample(words, 2))
        short_code = short_code.lower()
        short_code = short_code.replace(",", "-")
        # add three random digits
        short_code = short_code + "-" + str(randint(100, 999))
        #st.info(short_code)
        for index, row in ideas_df.iterrows():
            # if idea is a non empty string, add short code next to it
            if row['idea'] != "":
                ideas_df.loc[index, 'short_code'] = short_code
            else:
                # drop row if idea is empty
                ideas_df.drop(index, inplace=True)
        return ideas_df


def save_cumulative_idea_results(ideas_file, ideas_df):
    if os.path.exists('userdocs/cumulative_ideas.csv'):
        cumulative_ideas_df = pd.read_csv('userdocs/cumulative_ideas.csv')
        cumulative_ideas_df = pd.concat([cumulative_ideas_df, ideas_df])
    else:
        # create dataframe from ideas and series_description
        cumulative_ideas_df = ideas_df
    cumulative_ideas_df.to_csv('userdocs/cumulative_ideas.csv', index=False)

    return cumulative_ideas_df


def get_series_description(code):
    # python create a dictionary of series descriptions from code/description pairs
    series_descriptions_dict = {
        'ihatedaddysphone': "I hate $[thing that distracts my parent].  Child narrates a story about how much they wish it wouldn't interfere with their relationship. 250 words, 10 illustrations, fiction, age 4-8.",
        "oralhistories": "Oral histories of famous events deep in history or largely fictional such as the Nativity, the Trojan War, or the sinking of the Titanic. 80,000 words, 20 illustrations, fiction, trade/general."}
    return series_descriptions_dict[code]
