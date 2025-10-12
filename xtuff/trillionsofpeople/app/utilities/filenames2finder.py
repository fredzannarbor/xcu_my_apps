# copy list of file paths to a new directory
import os

import streamlit as st

new_directory = 'working/public_domain/next_up'


# create streamlit form
st.title('Copy filenames  to a new directory')
st.write('This app copies files to a new directory.')
st.write('The new directory must already exist.')

# get file paths
# file paths are relative paths with base '/Users/fred/unity/working/public_domain/queue'

# paste list of files ino the text box
file_paths = st.text_area('Paste list of file paths here', value='', height=20, max_chars=None, key=None)
# convert string to Path objects
file_paths = file_paths.splitlines()
file_paths = [os.path.join('/Users/fred/unity/', file_path) for file_path in file_paths]
st.info('You entered {} file paths.'.format(len(file_paths)))
st.write(file_paths)
# get new directory
# base of new directory is '/Users/fred/unity/working/pulic_domain'
new_directory = st.text_input('Enter new directory', max_chars=None, key=None)
#
# append new directory to base
new_directory = '/Users/fred/unity/working/public_domain/' + new_directory
if os.path.isdir(new_directory):
    st.write(f'{new_directory} exists.')
else:

    st.write('Creating new directory {}'.format(new_directory))
    os.mkdir(new_directory)


info_box = st.empty()
if st.button('Submit'):
    # copy each file to new directory
    for file_path in file_paths:
        filename = os.path.basename(file_path)
        new_file_path = os.path.join(new_directory, filename)
        if os.path.isfile(new_file_path):
            info_box.write(f'{new_file_path} already exists.')
        else:
            try:
                os.rename(file_path, new_file_path)
                info_box.write(f'{new_file_path} copied.')
            except Exception as e:
                info_box.write(f'Error: {e}')

