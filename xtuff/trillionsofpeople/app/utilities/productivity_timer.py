import time

import streamlit as st

with st.form("timer_widget"):
    time_minutes = st.number_input("Enter the time in minutes ", min_value=1, value=4)
    goal = st.text_input("Enter the goal ", value="Goal")
    time_in_seconds = time_minutes * 60
    submitted = st.form_submit_button("Start counting!")
    if submitted:
        st.info("counting up now!")
        with st.empty():
            for seconds in range(time_in_seconds):
                st.write(f"⏳ {seconds} seconds have passed")
                time.sleep(1)
                # if seconds == time_in_seconds:
                #    st.write("✔️ timer finished!")
