import streamlit as st
st.set_page_config(layout="wide")
import glob
import os

if st.secrets['environment'] == 'cloud':
    print('running on Streamlit Cloud with secrets file, gpt3 reduced fx, and no quota tracking')
    datadir = 'people_data/'
elif st.secrets['environment'] == 'local':
    print("running on Fred's mac with reduced gpt3 fx, secrets file and no quota tracking")

    datadir = 'people_data/'
elif st.secrets['environment'] == 'self-hosted':
    print('running  self-hosted on AWS instance with reduced gpt3 fx, secrets file, and no quota tracking')
    datadir = 'people_data/'

import gibberish
from gibberish import Gibberish

from numpy import extract, subtract

import pandas as pd
import datetime
from datetime import date
from gpt3_reduced_fx import gpt3complete, presets_parser, post_process_text, construct_preset_dict_for_UI_object
from nltk.corpus import wordnet as wn
import random

import requests

import csv

gib = Gibberish()

# convert the following table into an if then elif series

def randomly_assign_year_to_new_person(era):
    era_list = ['past', 'present', 'future']
    benchmark_list = [-190000, -50000, -8000, 1, 1250, 1650, 1750, 1850, 1900, 1950, 1995, 2011, 2020, 2035, 2050]
    chance_per_benchmark =  [ 67, 77, 471,698,808,835,870,895,924,970,988,1000]
    if era =='past':
        year = random.choices(species_list, cum_weights=chance_per_benchmark, k=1)
    


