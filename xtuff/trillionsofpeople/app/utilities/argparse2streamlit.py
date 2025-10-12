import random


def streamlitify(parser):
    """
    loop over argparse arguments for current program
    list each argument as a streamlit UI object
    """
    args = parser.parse_args()
    for index, arg in enumerate(vars(args)):
        print(arg)
        print(getattr(args, arg))

        if isinstance(getattr(args, arg), bool):
            st.checkbox(arg, getattr(args, arg), key=index)
        elif isinstance(getattr(args, arg), int):
            st.number_input(arg, getattr(args, arg), key=index)
        elif isinstance(getattr(args, arg), str):
            st.text_input(arg, getattr(args, arg), key=random.randint(0, 1000000))
    return


import argparse
import subprocess

import streamlit as st

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id", help="user_id for command line runs", default='37')
    parser.add_argument("--year", help="single year scope for report", default="2022")
    parser.add_argument("--frontlist_window", help="number of months to look back for frontlist", default=18.0)
    args = parser.parse_args()
    arg_vars = vars(args)
    # st.write(arg_vars)
    st.write("### Streamlit UI for ", parser.prog)
    # create streamlit form
    formic = st.form(key='my_form')
    # loop through all arguments and get all defined attributes for each
    for arg in vars(args):
        # st.write('arg', arg)
        formic.text_input(arg, args.__getattribute__(arg))
    submitted = formic.form_submit_button(label='Submit')
    st.write(submitted)

    if submitted:
        # use subprocess to run prog

        output = subprocess.run(["echo", "--user_id", str(args.user_id), "--year", str(args.year), "--frontlist_window",
                                 str(args.frontlist_window)])
        st.write(output)
        #

    # st.write(args)
    # test_object = create_streamlit_objects(args)
    # st.write(test_object)
