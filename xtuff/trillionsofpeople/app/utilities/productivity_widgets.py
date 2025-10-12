"""
productivity widget functions
"""
import os
from datetime import datetime

import streamlit as st


def get_filenames_only(file_path):
    filenames = os.listdir(file_path)
    return filenames


def display_filenames(filenames, maxstringlength=30):
    truncated_filenames = []
    if ".DS_Store" in filenames:
        filenames.remove(".DS_Store")
    if maxstringlength is not None:
        for f in filenames:
            f = f[:maxstringlength] + " …"
            truncated_filenames.append(f)
        return truncated_filenames
    return filenames


def get_heatmap_metadata(listname):
    heatmap_metadata = {
        "tooltip": {"position": "top"},
        "visualMap": {
            "min": 0,
            "max": 3000,
            "calculable": True,
            "orient": "horizontal",
        "left": "center",
        "top": "top",
    },
    "calendar": [
        {"range": "2022", "cellSize": ["auto", 20]},
        #{"top": 260, "range": "2019", "cellSize": ["auto", 20]},
        #{"top": 450, "range": "2018", "cellSize": ["auto", 20], "right": 5},
    ],
    "series": [
        {

            "type": "heatmap",
            "coordinateSystem": "calendar",
            "calendarIndex": 0,
            "data":get_heatmap_data(listname),
        },
    ],
    }
    return heatmap_metadata

def get_heatmap_data(listname):
    with open('notes_and_reports/healthinfo/' + listname + '.csv', 'r') as f:

        if listname == 'calories':
            # read calories.csv line by line
            lines = f.readlines()
            # add each line to a list
            lines = [line.strip().split(',') for line in lines]  
            calories = lines
            return calories
        else:
            print('couldna find data set named', listname)
            return

def save_heatmap_data(listname, value):
    now = datetime.now()
    if listname == 'calories':
        with open('notes_and_reports/healthinfo/calories.csv', 'a') as f:
            # append date and value to calories.csv
            f.write(str(now.date()) + ',' + str(value) + '\n')
        return 

    return "can't find data set"

def listoffiles(file_path):
    listoffiles = get_filenames(file_path)
    listoffiles = remove_DS_store(listoffiles)
    return listoffiles
    
def get_filenames(file_path, maxstringlength=36):
    """
    Select a file from a directory
    """
    files = os.listdir(file_path)
    for f in files:
        # break long strings into two lines
        if len(f) > maxstringlength:
            f = f[:maxstringlength] + "\n" + f[maxstringlength:]
    if '.DS_Store' in files:
        files.remove('.DS_Store')
    return files

def remove_DS_store(list):
    if '.DS_Store' in list:
        list.remove('.DS_Store')
    return list 

def headline(text):
    st.markdown("_" + text + "_")
    return None
