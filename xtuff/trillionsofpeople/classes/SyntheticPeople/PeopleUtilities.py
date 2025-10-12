"""
Classes for Operating on Synthetic People
"""
import csv
import glob
import random

import gibberish as gib
import numpy as np
import pandas as pd
import requests

from app.utilities.gpt3complete import gpt3complete, chatcomplete
from app.utilities.utilities import statcounter

# from trillionsofpeople import species

gib = gib.Gibberish()


def cacheaware_gpt3complete(preset, prompt, username="trillions"):
    response = gpt3complete(preset, prompt, username)
    return response


def load_people():
    all_people_data = pd.DataFrame()
    csvtarget = 'trillions-deploy/people_data/' + '*.csv'
    for i in glob.glob(csvtarget):
        print("reading file ", i)
        i_df = pd.read_csv(i, index_col=0, squeeze=True)
        all_people_data = all_people_data.append(i_df)
    return all_people_data


def import_data(dfname):
    df = pd.read_csv(dfname, index_col=0, squeeze=True)
    # fill missing fourwordsname with fourwordsnames
    df['fourwordsname'] = df['fourwordsname'].fillna(df['fourwordsname'].apply(fourwordsname))
    # for each row in df, if species is missing, fill with a different random species

    random_species = random.choice(['sapiens', 'neanderthalensis', 'denisovan', 'floresiensis'])
    df['species'] = df['species'].fillna(random_species)
    # for each row in df, fill in OCEAN tuple consistent with random species
    df['OCEAN_tuple'] = df['OCEAN_tuple'].fillna(df['species'].apply(OCEANtuple))
    df = df.fillna(value=np.nan)
    return df


def browse_people(filename):
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        people = list(reader)
    return people


def create_shortname(species):
    if species == 'sapiens':
        shortname = gib.generate_word()
    elif species == 'neanderthalensis':
        # add subprocess to call short names
        shortname = gib.generate_word(start_vowel=False)
    else:
        shortname = gib.generate_word()
    # name='Sapiens'
    shortname = shortname.title()
    return shortname


def fourwordsname():
    # verdant apples luxuriating fiercely

    with open('app/utilities/moby_pos/adjectives_clean.txt') as f:
        adjectives = f.readlines()
        f.close()
    with open('app/utilities/moby_pos/nouns_clean.txt') as f:
        nouns = f.readlines()
        f.close()
    with open('app/utilities/moby_pos/verbs_clean.txt') as f:
        verbs = f.readlines()
        f.close()
    with open('app/utilities/moby_pos/adverbs_clean.txt') as f:
        adverbs = f.readlines()
        f.close()

    words = adjectives
    short_adjectives = [word for word in words if 4 < len(word) < 9]
    adjective = random.choice(short_adjectives).strip()
    noun = random.choice(nouns).strip()
    verb = random.choice(verbs).strip()
    adverb = random.choice(adverbs).strip()

    print(adjective, noun, verb, adverb)
    fourwordsname = adjective + '-' + noun + '-' + verb + '-' + adverb
    return fourwordsname


def OCEANtuple(species):
    openness = random.random()
    conscientiousness = random.random()
    extraversion = random.random()
    agreeableness = random.random()
    emotional_range = random.random()
    OCEANtuple = (openness, conscientiousness, extraversion, agreeableness, emotional_range)
    return OCEANtuple


def get_species_info(species_name):
    known_species = ['sapiens', 'neanderthalensis', 'denisovan', 'floresiensis']
    # specifies_info_dict
    return known_species


def get_timeline_info(timeline):
    timelines = ['ours', 'RCP 8.5', 'Earth-616', 'Earth-1218', 'ODNI2040']
    # convert timelines to dictionary
    return timelines


def assign_realness_status(data_source):
    if data_source == 'OpenAI':
        realness = 'synthetic'
    elif data_source == 'historical':
        realness = 'authenticated'
    elif data_source == 'fictional':
        realness = 'fictional'
    elif data_source == 'random':
        realness = random.choice(['synthetic', 'authenticated', 'fictional'])
    else:
        realness = 'unknown'
    return realness


def create_new_people_df(country, selected_country_code, j, target_year, latitude,
                         longitude, nearest_city, year):
    peopledf_columns = ['name', 'image', 'born', 'gender', 'species', 'timeline', 'realness', 'latitude', 'longitude',
                        'nearest_city', 'country', 'backstory', 'fourwordsname', 'source', 'comments',
                        'status']  # 'OCEANtuple'])

    peopledf = pd.DataFrame(columns=peopledf_columns)
    peopledata = []
    card_columns = ['Attributes']
    card_df = pd.DataFrame(columns=card_columns)
    card_df['Attributes'] = peopledf_columns
    # with form info in hand, create personas
    for i in range(j):

        species = 'sapiens'
        gender = random.choice(['male', 'female'])
        shortname = create_shortname(species)
        year_of_birth_in_CE = target_year
        thisperson4name = fourwordsname()
        timeline = 'ours'
        realness = 'synthetic'  # ['synthetic', 'authenticated', 'fictional']
        # OCEAN_tuple =  'test' # OCEANtuple()
        if year < 0:
            prompt = shortname + ' was born ' + str(
                year_of_birth_in_CE) + 'years ago in  the area now known as ' + country + '.'
        if year == 0:
            prompt = shortname + ' was born in the area now known as ' + country + '.'
        if year > 0:
            prompt = shortname + ' will be born in the area now known as ' + country + '.'
        else:
            prompt = shortname
        source = 'TOP.info'
        username = 'trillions'
        latitude, longitude, nearest_city = random_spot(selected_country_code)
        prompt = prompt + '\n\n'
        response = chatcomplete('CreatePersonBackstory', prompt, 'gpt-3.5-turbo')
        openai_response = response
        backstory = openai_response['choices'][0]['message']['content']
        image_filename = "<img src=" + '"' + fetch_fake_face_api(gender) + '"' + ' height=90' + ">"
        # st.write(backstory)
        comments = None
        status = 'active'

        values = [shortname, image_filename, year_of_birth_in_CE, gender, species, timeline, realness, latitude,
                  longitude, nearest_city, country, backstory, thisperson4name, source, comments, status]  # ,
        card_df[shortname] = values
        zipped = zip(peopledf_columns, values)
        people_dict_i = dict(zipped)
        row = pd.Series(people_dict_i)
    pd.set_option('display.max_colwidth', 70)

    peopledf = pd.concat([peopledf, row], axis=1)
    return peopledf, card_df


def random_spot(country):
    latitude, longitude, nearest_city = "Unknown", "Unknown", "Unknown"
    try:
        request_uri = "https://api.3geonames.org/?randomland=" + country + '&json=1'
        print(request_uri)
        resp = requests.get(request_uri)
        json = resp.json()
        print(json)
        nearest_city = json['nearest']['name']
        latitude = json['nearest']['latt']
        longitude = json['nearest']['longt']
        print(nearest_city, latitude, longitude)
    except Exception as e:
        print(e)
        nearest_city = 'Unknown'
        latitude = 'Unknown'
        longitude = 'Unknown'
    return latitude, longitude, nearest_city


def migration_to(latitude, longitude, nearest_city):
    # migration function -- typically least travel cost + 20-500 km
    to_latitude_offset, to_longitude_offset, to_nearest_city_offset = 0, 0, 0
    current_location = latitude + to_latitude_offset, longitude + to_longitude_offset, nearest_city + to_nearest_city_offset
    return current_location


def select_fake_face_file(datadir):
    fakefiledir = datadir + '/' + 'fake'
    fakefilepath = fakefiledir + '/' + '*.jpg'
    fake_face_files = glob.glob(fakefilepath)
    # st.write(fake_face_files)
    image_filename = random.choice(fake_face_files)
    return image_filename


def fetch_fake_face_api(gender, min_age=10, max_age=70):
    baseuri = "https://fakeface.rest/thumb/view?"
    gender = gender
    noise = str(random.randint(1, 99))
    face_thumb_uri = baseuri + noise + '/' + gender

    return face_thumb_uri


# def create_single_person(preset, target_year, country):

statcounter(0, 0)
