from openai import OpenAI


from dotenv import load_dotenv
import os
import streamlit as st

# Initialize OpenAI client
load_dotenv()
client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)


class Assessor:
    def __init__(self, topics):
        self.topics = topics
        self.data = {}
        self.analysis_results = {}
        self.status_schedule = None
        self.last_checklist_date = None
        self.initial_assessment_done = False
        self.next_checklist_date = None
        self.recommendations = {}
        self.actions = {}






    def gather_info(self):
        for topic in self.topics:

            try:
                # Prompt the LLM to recommend key information to gather
                key_info_prompt = f'What key information should be gathered for {topic}?'
                st.info(f'Gathering information for {topic}')
                key_info = self._get_key_info_from_llm(key_info_prompt)
                self.data[topic] = key_info
                # Create an analysis prompt
                self.analysis_results[topic] = f'Analyze the following key information for {topic}: {key_info}'
            except Exception as e:
                st.error(f'Error gathering information for {topic}: {e}')

    def _get_key_info_from_llm(self, prompt):
        try:
            # Call the OpenAI-compatible LLM client to get key information
            response = client.chat.completions.create(
                model='grok-3-latest',
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f'Error fetching key information: {e}')
            return None

    def analyze(self):
        for topic, key_info in self.data.items():
            try:
                analysis_prompt = self.analysis_results[topic]
                analysis_result = self._analyze_with_llm(analysis_prompt, key_info)
                self.analysis_results[topic] = analysis_result
                st.write(f'Analysis for {topic}: {analysis_result}')
            except Exception as e:
                st.error(f'Error analyzing data for {topic}: {e}')

    def _analyze_with_llm(self, analysis_prompt, key_info):
        try:
            # Check if using OpenAI client
            response = client.chat.completions.create(model='grok-3-latest',
            messages=[{'role': 'user', 'content': f'{analysis_prompt} {key_info}'}])
            return response.choices[0].message.content
        except Exception as e:
            st.error(f'Error analyzing with LLM: {e}')
            # Fallback to Ollama client if OpenAI fails
            try:
                import ollama
                response = ollama.chat(
                    model='mistral',
                    messages=[{'role': 'user', 'content': f'{analysis_prompt} {key_info}'}]
                )
                return response.content
            except Exception as e:
                st.error(f'Error with Ollama client: {e}')
                return None

        for topic in self.topics:
            # Prompt the LLM to recommend key information to gather
            key_info_prompt = f'What key information should be gathered for {topic}?'
            key_info = self._get_key_info_from_llm(key_info_prompt)
            self.data[topic] = key_info
            # Create an analysis prompt
            self.analysis_results[topic] = f'Analyze the following key information for {topic}: {key_info}'

        for topic in self.topics:
            # Implement dynamic information gathering based on the topic
            print(f'Gathering information for: {topic}')
            # Placeholder for actual gathering logic
            self.data[topic] = self._gather_topic_info(topic)

    def _gather_topic_info(self, topic):
        # Gather key information from the user using Streamlit
        import streamlit as st
        st.header(f'Gathering information for {topic}')
        key_info = st.text_input(f'Enter key information for {topic}:')  # Example input
        return key_info

    def _analyze_with_llm(self, analysis_prompt, key_info):
        try:
            # Check if using OpenAI client
            response = client.chat.completions.create(model='grok-3-latest',
            messages=[{'role': 'user', 'content': f'{analysis_prompt} {key_info}'}])
            return response.choices[0].message.content
        except:
            # Fallback to Ollama client if OpenAI fails
            import ollama
            response = ollama.chat(
                model='your-ollama-model',
                messages=[{'role': 'user', 'content': f'{analysis_prompt} {key_info}'}]
            )
            return response.content

    def analyze(self):
        for topic, key_info in self.data.items():
            analysis_prompt = self.analysis_results[topic]
            analysis_result = self._analyze_with_llm(analysis_prompt, key_info)
            self.analysis_results[topic] = analysis_result
            import streamlit as st
            st.write(f'Analysis for {topic}: {analysis_result}')

        # Implement analysis of the gathered data
        for topic, info in self.data.items():
            print(f'Analyzing data for {topic}: {info}')
            # Placeholder for actual analysis logic

    def monitor(self):
        # Implement monitoring logic
        print('Monitoring status...')
        # Placeholder for actual monitoring logic

    def create_status_schedule(self):
        import streamlit as st
        st.header('Status Checking Schedule')
        frequency = st.selectbox('Select frequency for status updates:', ['Daily', 'Weekly', 'Monthly'])
        status_data = st.data_editor('Update your status:', data={}, num_rows='dynamic')
        # Save the status data and frequency
        self.status_schedule = {'frequency': frequency, 'status_data': status_data}
        st.success('Status schedule created successfully!')

    def recommend_actions(self):
        # Provide recommendations based on analysis
        print('Recommending actions based on analysis...')
        # Placeholder for actual recommendation logic


