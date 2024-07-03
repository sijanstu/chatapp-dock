import asyncio
import json
import requests
import streamlit as st
import sseclient
import urllib3
import re
from streamlit_ace import st_ace

from tts import text_to_speech

st.title("Chat with Advanced Coding Assistant 🤖")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize code snippets state
if "code_snippets" not in st.session_state:
    st.session_state.code_snippets = []


# Function to extract code snippets from markdown text
def extract_code_snippets(markdown_text):
    code_snippets = re.findall(r'```(?:[a-zA-Z]*\n)?([\s\S]*?)```', markdown_text)
    return code_snippets


# Function to get the vqd4 token
def vqd4():
    url = "https://duckduckgo.com/duckchat/v1/status"
    vqd4payload = {}
    headers = {
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/126.0.0.0 Safari/537.36',
        'x-vqd-accept': '1'
    }
    response = requests.request("GET", url, headers=headers, data=vqd4payload)
    return response.headers['X-Vqd-4']


# Function to get AI response from DuckDuckGo
def get_ai_response(user_input):
    url = 'https://duckduckgo.com/duckchat/v1/chat'
    headers = {
        'accept': 'text/event-stream',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/126.0.0.0 Safari/537.36',
        'x-vqd-4': vqd4() if not st.session_state.get('vqd4l') else st.session_state.vqd4l,
        'Content-Type': 'application/json'
    }
    data = {
        "model": "claude-3-haiku-20240307",
        "messages": [{"role": "user", "content": "provide short and sweet answers for: " + user_input}]
    }
    response = with_requests(url, headers, json.dumps(data))
    client = sseclient.SSEClient(response)
    ai_full_response = ""
    temp_response = st.empty()
    for event in client.events():
        if event.data != '[DONE]':
            try:
                parsed_data = json.loads(event.data)
                if 'message' in parsed_data:
                    ai_full_response += parsed_data['message']
                    temp_response.markdown(ai_full_response)
            except json.JSONDecodeError:
                pass
        else:
            temp_response.empty()

    return ai_full_response


def get_audio_and_add_to_chat(ai_full_response):
    audiofile = text_to_speech(ai_full_response)
    st.audio(audiofile, format='audio/mp3', start_time=0, autoplay=True)


# Function to make a request using the requests library
def with_requests(url, headers, data):
    return requests.post(url, headers=headers, data=data, stream=True)


# Function to display chat messages
def display_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            content = message["content"]
            if message["role"] == "assistant" and 'code_snippet' in message:
                file_name = f"Code Snippet {message['code_snippet'] + 1}"
                if st.button(file_name, key=f"snippet_{message['code_snippet']}"):
                    st.session_state.selected_code_snippet = st.session_state.code_snippets[message['code_snippet']]
                    st.session_state.show_editor = True
            else:
                st.markdown(content)


# Function to handle user input
def handle_input():
    prompt = st.chat_input("What is up?")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                assistant_response = get_ai_response(prompt)
                st.markdown(assistant_response)
            except urllib3.exceptions.MaxRetryError:
                assistant_response = ("I am sorry, I am unable to process your request at the moment. Please try again "
                                      "later.")
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        new_code_snippets = extract_code_snippets(assistant_response)
        for code_snippet in new_code_snippets:
            st.session_state.code_snippets.append(code_snippet)
            # snippet_index = len(st.session_state.code_snippets) - 1
            # st.session_state.messages.append({"role": "assistant", "content": assistant_response, "code_snippet": snippet_index})
        get_audio_and_add_to_chat(assistant_response)


# Display the chat messages
display_messages()

# Handle user input
handle_input()


# Sidebar to display selected code snippet
# st.sidebar.header("Code Snippet")
# if st.session_state.get("show_editor", False):
#     st_ace(
#         value=st.session_state.selected_code_snippet,
#         language='java' if 'public class' in st.session_state.selected_code_snippet else 'python',
#         theme='monokai',
#         key='ace-editor'
#     )


# Display code snippet cards in the chat
def add_code_snippet(snippet):
    file_name = get_ai_response(
        "Generate a code file name with extension for the code snippet below, provide me a file name and extension only nothitng else. snippet: " + snippet)
    # st.sidebar.markdown(f"```{file_name}```")
    # make it copyable
    st.sidebar.code(file_name, language='python')
    st.sidebar.code(snippet, language='java' if 'public class' in snippet else 'python')


if st.session_state.code_snippets:
    st.sidebar.header("Code Snippets")
    st.markdown(
        """
        <style>
        .sidebar .sidebar-content {
            transition: margin-left .3s;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    for idx, code_snippet in enumerate(st.session_state.code_snippets):
        # check if code has multiple lines, only display if it has more than 1 line
        if code_snippet.count('\n') > 1:
            add_code_snippet(code_snippet)
        else:
            st.sidebar.code(code_snippet, language='java' if 'public class' in code_snippet else 'python')
