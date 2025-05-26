import streamlit as st
import requests
import json
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
from datetime import datetime
import time

# Configure the page
st.set_page_config(
    page_title="Finance Assistant",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    .main {
        padding: 2rem;
    }
    .stAudio {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None

initialize_session_state()

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    input_type = st.radio("Input Type", ["Text", "Voice"])
    output_type = st.radio("Output Type", ["Text", "Voice"])
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This Finance Assistant helps you get real-time market insights and analysis through natural conversation.
    
    **Features:**
    - Real-time market data
    - Voice interaction
    - Smart analysis
    - Multi-source information
    """)

# Main content
st.title("💹 Finance Assistant")

# Chat container
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Input section
input_container = st.container()
with input_container:
    if input_type == "Text":
        user_input = st.text_input("Ask me anything about the markets:", key="text_input")
        send_button = st.button("Send")
        
        if send_button and user_input:
            # Add user message to chat
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Send request to backend
            try:
                response = requests.post(
                    "http://localhost:8000/process",
                    json={
                        "query": user_input,
                        "input_type": "text",
                        "response_type": output_type.lower()
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Add assistant response to chat
                    st.session_state.messages.append(
                        {"role": "assistant", "content": result["response"]}
                    )
                    st.rerun()
                else:
                    st.error("Failed to get response from the assistant.")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    else:  # Voice input
        col1, col2 = st.columns(2)
        
        with col1:
            if not st.session_state.recording:
                if st.button("🎤 Start Recording"):
                    st.session_state.recording = True
                    st.rerun()
            else:
                if st.button("⏹️ Stop Recording"):
                    st.session_state.recording = False
                    # TODO: Implement voice recording logic
                    st.rerun()
        
        with col2:
            if st.session_state.audio_file:
                st.audio(st.session_state.audio_file)

# Footer
st.markdown("---")
st.markdown(
    "Made with ❤️ using Streamlit | [GitHub](https://github.com/yourusername/multi-agent-finance-assistant)"
) 