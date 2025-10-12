import streamlit as st
from general_assessor import Assessor

def main():
    st.title('General Purpose Assessor')

    topics = st.text_input('Enter topics separated by commas:')
    if st.button('Initialize Assessor'):
        if topics:  # Check if topics is not empty
            topic_list = [topic.strip() for topic in topics.split(',')]
            st.session_state.assessor = Assessor(topic_list)
            st.success('Assessor initialized with topics!')
            st.write(st.session_state.assessor.topics)
            st.session_state.assessor.initialized = True
        else:
            st.error('Please enter at least one topic.')

    # Gather information

    if 'assessor' in st.session_state and st.session_state.assessor.initialized:
        if st.button('Gather Information'):

            for topic in st.session_state.assessor.topics:
                st.info(f'Gathering information for {topic}')
                st.session_state.assessor.gather_info()
            st.success('Information gathered!')

        # Gather topic information
        if st.button('Gather Topic Info'):
            for topic in st.session_state.assessor.topics:
                key_info = st.text_input(f'Enter key information for {topic}:')  # Unique input for each topic
                st.session_state.assessor.data[topic] = key_info
            st.success('Topic information gathered!')

        # Analyze information
        if st.button('Analyze'):
            st.session_state.assessor.analyze()
            st.success('Analysis complete!')

        # Create status schedule
        if st.button('Create Status Schedule'):
            st.session_state.assessor.create_status_schedule()

        # Display analysis results
        st.header('Analysis Results')
        for topic, result in st.session_state.assessor.analysis_results.items():
            st.write(f'{topic}: {result}')

if __name__ == '__main__':
    main()