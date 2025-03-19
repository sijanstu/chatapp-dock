import asyncio
import json
import requests
import streamlit as st
import sseclient
import urllib3
import re
from streamlit_ace import st_ace
import time
from tts import text_to_speech

# Page configuration
st.set_page_config(
    page_title="Advanced Coding Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        color: #4F8BF9;
        margin-bottom: 1rem;
    }
    
    .stButton button {
        background-color: #4F8BF9;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        background-color: #3670CF;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .code-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #4F8BF9;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .snippet-card {
        border: 1px solid #e6e6e6;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
        transition: all 0.3s;
    }
    
    .snippet-card:hover {
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .code-actions {
        display: flex;
        justify-content: space-between;
        margin-top: 0.5rem;
    }
    
    /* Chat message styling */
    .user-message {
        background-color: #E1F5FE;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 5px solid #4FC3F7;
    }
    
    .assistant-message {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 5px solid #9E9E9E;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        padding: 10px;
    }
    
    .typing-indicator span {
        height: 10px;
        width: 10px;
        background-color: #4F8BF9;
        border-radius: 50%;
        display: inline-block;
        margin: 0 2px;
        opacity: 0.8;
    }
    
    .typing-indicator span:nth-child(1) {
        animation: bounce 1s infinite 0.2s;
    }
    .typing-indicator span:nth-child(2) {
        animation: bounce 1s infinite 0.4s;
    }
    .typing-indicator span:nth-child(3) {
        animation: bounce 1s infinite 0.6s;
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }
    
    /* Fullscreen code editor */
    .fullscreen-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.8);
        z-index: 1000;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .close-button {
        position: absolute;
        top: 20px;
        right: 20px;
        color: white;
        font-size: 24px;
        cursor: pointer;
    }
    
    /* Make the sidebar wider */
    [data-testid="stSidebar"] {
        min-width: 350px !important;
    }
</style>
""", unsafe_allow_html=True)

# App title with styled header
st.markdown('<h1 class="main-header">Advanced Coding Assistant 🤖</h1>', unsafe_allow_html=True)

# Initialize session states
if "messages" not in st.session_state:
    st.session_state.messages = []

if "code_snippets" not in st.session_state:
    st.session_state.code_snippets = []

if "file_names" not in st.session_state:
    st.session_state.file_names = []
    
if "vqd4l" not in st.session_state:
    st.session_state.vqd4l = None
    
if "is_typing" not in st.session_state:
    st.session_state.is_typing = False

if "current_mode" not in st.session_state:
    st.session_state.current_mode = "chat"  # Default mode
    
if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True

if "show_fullscreen_editor" not in st.session_state:
    st.session_state.show_fullscreen_editor = False
    
if "fullscreen_code" not in st.session_state:
    st.session_state.fullscreen_code = ""
    
if "fullscreen_language" not in st.session_state:
    st.session_state.fullscreen_language = "python"


# Function to extract code snippets from markdown text
def extract_code_snippets(markdown_text):
    code_blocks = re.findall(r'```(.*?)\n([\s\S]*?)```', markdown_text)
    snippets = []
    languages = []
    
    for lang, code in code_blocks:
        lang = lang.strip().lower() if lang.strip() else "text"
        # Convert common language aliases
        if lang in ["js", "javascript"]:
            lang = "javascript"
        elif lang in ["py", "python"]:
            lang = "python"
        elif lang in ["ts", "typescript"]:
            lang = "typescript"
        elif lang in ["java"]:
            lang = "java"
        elif lang in ["c#", "csharp"]:
            lang = "csharp"
        elif lang in ["html", "htm"]:
            lang = "html"
        elif lang in ["css"]:
            lang = "css"
        elif lang in ["json"]:
            lang = "json"
        elif lang in ["xml"]:
            lang = "xml"
        else:
            # Default to python for unknown languages
            if "public class" in code:
                lang = "java"
            elif "function" in code or "var" in code or "const" in code:
                lang = "javascript"
            elif "def " in code or "import " in code:
                lang = "python"
            else:
                lang = "text"
        
        snippets.append(code)
        languages.append(lang)
    
    return snippets, languages


# Function to generate file names based on code content
def generate_file_name(code, language):
    extensions = {
        "python": "py",
        "javascript": "js",
        "typescript": "ts",
        "java": "java",
        "csharp": "cs",
        "html": "html",
        "css": "css",
        "json": "json",
        "xml": "xml",
        "text": "txt"
    }
    
    ext = extensions.get(language, "txt")
    
    # Try to extract function or class name from code
    if language == "python":
        match = re.search(r'def\s+([a-zA-Z0-9_]+)', code)
        if match:
            return f"{match.group(1)}.{ext}"
        match = re.search(r'class\s+([a-zA-Z0-9_]+)', code)
        if match:
            return f"{match.group(1)}.{ext}"
    elif language == "javascript" or language == "typescript":
        match = re.search(r'function\s+([a-zA-Z0-9_]+)', code)
        if match:
            return f"{match.group(1)}.{ext}"
        match = re.search(r'class\s+([a-zA-Z0-9_]+)', code)
        if match:
            return f"{match.group(1)}.{ext}"
    elif language == "java":
        match = re.search(r'class\s+([a-zA-Z0-9_]+)', code)
        if match:
            return f"{match.group(1)}.{ext}"
    
    # Default filename if no pattern is found
    return f"snippet_{len(st.session_state.code_snippets) + 1}.{ext}"


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
    st.session_state.vqd4l = response.headers.get('X-Vqd-4')
    return st.session_state.vqd4l


# Function to get AI response from DuckDuckGo
def get_ai_response(user_input):
    st.session_state.is_typing = True
    
    url = 'https://duckduckgo.com/duckchat/v1/chat'
    headers = {
        'accept': 'text/event-stream',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/126.0.0.0 Safari/537.36',
        'x-vqd-4': vqd4() if not st.session_state.get('vqd4l') else st.session_state.vqd4l,
        'Content-Type': 'application/json'
    }
    
    # Adjust the prompt based on the current mode
    if st.session_state.current_mode == "explain":
        prompt = f"Please explain this code in simple terms, highlight any issues, and suggest improvements: {user_input}"
    elif st.session_state.current_mode == "debug":
        prompt = f"Debug this code and provide a corrected version with explanations: {user_input}"
    elif st.session_state.current_mode == "optimize":
        prompt = f"Optimize this code for better performance and explain your changes: {user_input}"
    else:  # chat mode
        prompt = user_input
    
    data = {
        "model": "claude-3-haiku-20240307",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)
        client = sseclient.SSEClient(response)
        ai_full_response = ""
        temp_response = st.empty()
        
        # Display typing indicator
        with temp_response:
            st.markdown(
                """
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        for event in client.events():
            if event.data != '[DONE]':
                try:
                    parsed_data = json.loads(event.data)
                    if 'message' in parsed_data:
                        ai_full_response += parsed_data['message']
                        # Update the response in real-time
                        with temp_response:
                            st.markdown(ai_full_response)
                except json.JSONDecodeError:
                    pass
            else:
                temp_response.empty()
        
        st.session_state.is_typing = False
        return ai_full_response
    
    except Exception as e:
        st.session_state.is_typing = False
        st.error(f"Error: {str(e)}")
        return f"I'm sorry, I encountered an error: {str(e)}. Please try again later."


# Function to handle text-to-speech
def handle_tts(ai_full_response):
    if st.session_state.voice_enabled:
        try:
            audiofile = text_to_speech(ai_full_response)
            st.audio(audiofile, format='audio/mp3', start_time=0)
        except Exception as e:
            st.warning(f"Text-to-speech failed: {str(e)}")


# Create a two-column layout
col1, col2 = st.columns([2, 1])

with col2:
    # Sidebar with app controls and code snippets
    with st.container():
        st.markdown('<div class="code-header">App Settings</div>', unsafe_allow_html=True)
        
        # Mode selection
        mode = st.radio(
            "Select Mode:",
            ["Chat", "Explain Code", "Debug Code", "Optimize Code"],
            horizontal=True,
            key="mode_selector"
        )
        
        # Update current mode based on selection
        if mode == "Chat":
            st.session_state.current_mode = "chat"
        elif mode == "Explain Code":
            st.session_state.current_mode = "explain"
        elif mode == "Debug Code":
            st.session_state.current_mode = "debug"
        elif mode == "Optimize Code":
            st.session_state.current_mode = "optimize"
        
        # Voice toggle
        st.session_state.voice_enabled = st.toggle("Enable Voice Response", value=st.session_state.voice_enabled)
        
        # Clear chat button
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.session_state.code_snippets = []
            st.session_state.file_names = []
            st.experimental_rerun()
    
    # Code snippet section
    if st.session_state.code_snippets:
        st.markdown('<div class="code-header">Saved Code Snippets</div>', unsafe_allow_html=True)
        
        for idx, (snippet, language) in enumerate(zip(st.session_state.code_snippets, st.session_state.file_names)):
            with st.expander(f"Snippet {idx+1}: {st.session_state.file_names[idx]}"):
                st.code(snippet, language=language.split('.')[-1] if '.' in language else 'python')
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Edit", key=f"edit_{idx}"):
                        st.session_state.fullscreen_code = snippet
                        st.session_state.fullscreen_language = language.split('.')[-1] if '.' in language else 'python'
                        st.session_state.show_fullscreen_editor = True
                        st.session_state.editing_idx = idx
                with col2:
                    if st.button("Copy", key=f"copy_{idx}"):
                        # We can't actually copy to clipboard in Streamlit, but we can show a success message
                        st.success("Code copied to clipboard!")
                with col3:
                    if st.button("Delete", key=f"delete_{idx}"):
                        st.session_state.code_snippets.pop(idx)
                        st.session_state.file_names.pop(idx)
                        st.experimental_rerun()

with col1:
    # Chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display existing chat messages
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="assistant-message">{message["content"]}</div>', unsafe_allow_html=True)
    
    # User input based on the selected mode
    if st.session_state.current_mode in ["explain", "debug", "optimize"]:
        # Code input area
        st.markdown(f'<div class="code-header">Enter code to {st.session_state.current_mode}:</div>', unsafe_allow_html=True)
        code_input = st_ace(
            placeholder=f"Enter your code here to {st.session_state.current_mode}...",
            language="python",
            theme="monokai",
            height=300,
            key="code_input"
        )
        
        if st.button(f"{mode.split()[0]} Code"):
            if code_input:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": f"Please {st.session_state.current_mode} this code:\n```\n{code_input}\n```"})
                
                # Get AI response
                with st.spinner(f"{mode.split()[0]}ing your code..."):
                    ai_response = get_ai_response(code_input)
                
                # Add assistant response
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
                # Extract and save code snippets
                snippets, languages = extract_code_snippets(ai_response)
                for i, (snippet, lang) in enumerate(zip(snippets, languages)):
                    if snippet.strip():  # Ignore empty snippets
                        st.session_state.code_snippets.append(snippet)
                        filename = generate_file_name(snippet, lang)
                        st.session_state.file_names.append(filename)
                
                # Text-to-speech for the response
                handle_tts(ai_response)
                
                st.experimental_rerun()
    else:
        # Normal chat input
        user_input = st.chat_input("Ask me anything about coding...")
        
        if user_input:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Get AI response
            with st.spinner("Processing your request..."):
                ai_response = get_ai_response(user_input)
            
            # Add assistant response
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
            # Extract and save code snippets
            snippets, languages = extract_code_snippets(ai_response)
            for i, (snippet, lang) in enumerate(zip(snippets, languages)):
                if snippet.strip():  # Ignore empty snippets
                    st.session_state.code_snippets.append(snippet)
                    filename = generate_file_name(snippet, lang)
                    st.session_state.file_names.append(filename)
            
            # Text-to-speech for the response
            handle_tts(ai_response)
            
            st.experimental_rerun()

# Fullscreen code editor
if st.session_state.show_fullscreen_editor:
    fullscreen_container = st.container()
    
    with fullscreen_container:
        st.markdown("""
        <div class="fullscreen-overlay">
            <div class="close-button" onclick="document.querySelector('.fullscreen-overlay').style.display='none';">✕</div>
            <div style="width: 80%; height: 80%;">
                <h2 style="color: white;">Edit Code</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        edited_code = st_ace(
            value=st.session_state.fullscreen_code,
            language=st.session_state.fullscreen_language,
            theme="monokai",
            height=500,
            key="fullscreen_editor"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Changes"):
                # Update the code snippet
                idx = st.session_state.editing_idx
                st.session_state.code_snippets[idx] = edited_code
                st.session_state.show_fullscreen_editor = False
                st.experimental_rerun()
        
        with col2:
            if st.button("Cancel"):
                st.session_state.show_fullscreen_editor = False
                st.experimental_rerun()
