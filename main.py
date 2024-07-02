import streamlit as st
import requests
import json
import sseclient
import re


def get_ai_response(user_input):
    url = "https://duckduckgo.com/duckchat/v1/chat"

    headers = {
        'accept': 'text/event-stream',
        'accept-language': 'en-GB,en;q=0.8',
        'content-type': 'application/json',
        'cookie': 'dcm=1',
        'origin': 'https://duckduckgo.com',
        'priority': 'u=1, i',
        'referer': 'https://duckduckgo.com/',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Brave";v="126"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
        'x-vqd-4': '4-17083453430632415906084007210612747928'
    }

    data = {
        "model": "claude-3-haiku-20240307",
        "messages": [
            {
                "role": "user",
                "content": user_input
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)
    client = sseclient.SSEClient(response)

    full_response = ""
    for event in client.events():
        if event.data != '[DONE]':
            try:
                parsed_data = json.loads(event.data)
                if 'message' in parsed_data:
                    full_response += parsed_data['message']
            except json.JSONDecodeError:
                pass

    return full_response


def format_message(message):
    # Function to format code blocks
    def replace_code_block(match):
        code = match.group(2)
        language = match.group(1) if match.group(1) else ""
        return f"```{language}\n{code}\n```"

    # Replace ```language\ncode``` blocks
    formatted = re.sub(r'```(\w*)\n(.*?)```', replace_code_block, message, flags=re.DOTALL)

    # Replace single backticks with inline code format
    formatted = re.sub(r'`([^`\n]+)`', r'`\1`', formatted)

    return formatted


def extract_code_blocks(message):
    code_blocks = []
    code_pattern = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
    matches = code_pattern.finditer(message)

    for i, match in enumerate(matches, 1):
        language = match.group(1) if match.group(1) else "text"
        code = match.group(2)
        filename = f"code_snippet_{i}.{language}" if language != "text" else f"code_snippet_{i}.txt"
        code_blocks.append((filename, language, code))

    return code_blocks


st.title("Chat with DuckDuckGo AI")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize a key for the input field
if "user_input_key" not in st.session_state:
    st.session_state.user_input_key = 0

# Display chat messages from history
for message in st.session_state.messages:
    role = message["role"]
    content = format_message(message["content"])

    if role == "user":
        st.markdown(f"**You:** {content}")
    else:
        st.markdown(f"**Assistant:** {content}")

        # Extract and display code blocks
        code_blocks = extract_code_blocks(message["content"])
        for filename, language, code in code_blocks:
            with st.expander(f"Code: {filename}"):
                st.code(code, language=language)

    st.markdown("---")

# User input
user_input = st.text_input("Your question:", key=f"user_input_{st.session_state.user_input_key}")

if st.button("Send"):
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Get AI response
        ai_response = get_ai_response(user_input)

        # Add AI response to chat history
        st.session_state.messages.append({"role": "assistant", "content": ai_response})

        # Increment the key to reset the input field
        st.session_state.user_input_key += 1

        # Rerun the app to update the chat display
        st.experimental_rerun()

st.markdown("---")
st.markdown("This app uses the DuckDuckGo Chat API with Claude 3 Haiku.")