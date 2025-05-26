import streamlit as st
import requests
import json
from datetime import datetime
import pytz

st.set_page_config(
    page_title="Finance Assistant",
    page_icon="💹",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

def initialize_ui():
    st.title("🎙️ Finance Assistant")
    st.markdown("""
    Your intelligent market brief assistant. Ask questions about market conditions,
    risk exposure, and earnings surprises through voice or text.
    """)

def display_market_summary():
    st.subheader("📊 Market Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Asia Tech Allocation", 
                 value="22%",
                 delta="4%")
    
    with col2:
        st.metric(label="TSMC Earnings", 
                 value="Beat",
                 delta="4%")
    
    with col3:
        st.metric(label="Samsung Earnings",
                 value="Miss",
                 delta="-2%")

def get_current_time_asia():
    asia_tz = pytz.timezone('Asia/Tokyo')
    current_time = datetime.now(asia_tz)
    return current_time.strftime("%Y-%m-%d %H:%M:%S %Z")

def main():
    initialize_ui()
    
    # Display current time in Asia
    st.sidebar.markdown(f"**Asian Market Time**  \n{get_current_time_asia()}")
    
    # Display market summary
    display_market_summary()
    
    # Voice Input Section
    st.subheader("🎤 Voice Input")
    if st.button("Start Recording"):
        st.info("Voice recording functionality coming soon...")
    
    # Text Input Section
    st.subheader("💬 Text Input")
    user_input = st.text_input("Type your question here:", 
                              placeholder="e.g., What's our risk exposure in Asia tech stocks today?")
    
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # TODO: Replace with actual API call to orchestrator
        response = {
            "message": "Today, your Asia tech allocation is 22% of AUM, up from 18% yesterday. "
                      "TSMC beat estimates by 4%, Samsung missed by 2%. Regional sentiment is "
                      "neutral with a cautionary tilt due to rising yields."
        }
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response["message"]})
    
    # Display chat history
    st.subheader("💬 Conversation History")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

if __name__ == "__main__":
    main() 