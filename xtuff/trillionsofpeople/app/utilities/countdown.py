import time

import streamlit as st


def countdown(mins, secs=0):
    t = (mins*60) + secs
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        infomessage = timer + '\r'
        st.info(infomessage)
        time.sleep(1)
        t -= 1
