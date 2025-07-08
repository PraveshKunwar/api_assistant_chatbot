import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time
import re

load_dotenv()

st.title("🌽 University of Michigan API Assistant")
st.write(
    "This is a chatbot that connects to the University of Michigan's Maizey AI assistant. "
    "Ask any questions and Maizey will help you with information about U-M!"
)

url = 'https://umgpt.umich.edu'
project_pk = os.getenv("PROJECT_PK")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

if not ACCESS_TOKEN:
    st.error("❌ 'ACCESS_TOKEN' not found in environment variables. Please check your .env file.")
    st.info("💡 Your .env file should contain: ACCESS_TOKEN=your_maizey_api_token_here")
    st.stop()

if not project_pk:
    st.error("❌ 'PROJECT_PK' not found in environment variables. Please check your .env file.")
    st.info("💡 Your .env file should contain: PROJECT_PK=your_project_guid_here")
    st.stop()

if "conversation_pk" not in st.session_state:
    st.session_state.conversation_pk = None

if "messages" not in st.session_state:
    st.session_state.messages = []

def create_conversation():
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }
    
    new_convo = f'{url}/maizey/api/projects/{project_pk}/conversation/'
    
    try:
        response = requests.post(new_convo, headers=headers, json={})
        
        if response.status_code == 201:
            conversation_data = response.json()
            return conversation_data["pk"]
        else:
            st.error(f"❌ Failed to create conversation. Status: {response.status_code}")
            st.error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        st.error(f"❌ Error creating conversation: {str(e)}")
        return None

def send_message_to_maizey(user_question):
    if not st.session_state.conversation_pk:
        st.session_state.conversation_pk = create_conversation()
        if not st.session_state.conversation_pk:
            return "❌ Could not start conversation with Maizey. Please try again."
    
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }
    
    new_msg = f'{url}/maizey/api/projects/{project_pk}/conversation/{st.session_state.conversation_pk}/messages/'
    
    try:
        response = requests.post(new_msg, headers=headers, json={
            "query": user_question
        })
        
        if response.status_code == 201:
            message_data = response.json()
            return message_data.get('response', 'Sorry, no response received.')
        else:
            return f"❌ Failed to send message. Status: {response.status_code}\nResponse: {response.text}"
            
    except Exception as e:
        return f"❌ Error sending message: {str(e)}"

def format_maizey_response(response_text):
    parts = re.split(r'```(\w+)?\n(.*?)```', response_text, flags=re.DOTALL)
    
    formatted_parts = []
    for i, part in enumerate(parts):
        if i % 3 == 0:
            if part.strip():
                formatted_parts.append(('text', part.strip()))
        elif i % 3 == 1:
            language = part.lower() if part else 'python'
            formatted_parts.append(('language', language))
        elif i % 3 == 2:
            if part.strip():
                formatted_parts.append(('code', part.strip()))
    
    return formatted_parts

def display_formatted_response(response_text):
    formatted_parts = format_maizey_response(response_text)
    
    i = 0
    while i < len(formatted_parts):
        part_type, content = formatted_parts[i]
        
        if part_type == 'text':
            st.markdown(content)
        elif part_type == 'language' and i + 1 < len(formatted_parts):
            language = content
            if i + 1 < len(formatted_parts) and formatted_parts[i + 1][0] == 'code':
                code_content = formatted_parts[i + 1][1]
                st.code(code_content, language=language, line_numbers=True)
                i += 1
        elif part_type == 'code':
            st.code(content, language='python', line_numbers=True)
        
        i += 1

def stream_response(text):
    words = text.split()
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        time.sleep(0.03)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            display_formatted_response(message["content"])
        else:
            st.markdown(message["content"])

if prompt := st.chat_input("Ask Maizey anything about University of Michigan..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Maizey is thinking..."):
            response = send_message_to_maizey(prompt)
        
        display_formatted_response(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

with st.sidebar:
    st.header("🌽 Maizey AI Assistant")
    
    if st.session_state.conversation_pk:
        st.success("✅ Connected")
        st.caption(f"Conv ID: {st.session_state.conversation_pk}...")
    else:
        st.info("🆕 Ready to Connect")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_pk = None
            st.rerun()
    
    with col2:
        if st.button("🧪 Test API", use_container_width=True):
            with st.spinner("Testing..."):
                test_headers = {
                    'accept': 'application/json',
                    'Authorization': 'Bearer ' + ACCESS_TOKEN,
                    'Content-Type': 'application/json'
                }
                test_url = f'{url}/maizey/api/projects/{project_pk}/conversation/'
                
                try:
                    test_response = requests.post(test_url, headers=test_headers, json={})
                    if test_response.status_code == 201:
                        st.success("✅ API Connected")
                    else:
                        st.error(f"❌ Status: {test_response.status_code}")
                except Exception as e:
                    st.error(f"❌ Connection Failed")
    
    st.divider()
    
    st.subheader("🔧 Configuration")
    with st.expander("Connection Details"):
        st.text(f"Endpoint: umgpt.umich.edu")
        st.text(f"Project: {project_pk[:12]}...")
        st.text(f"Token: {'✅ Valid' if ACCESS_TOKEN else '❌ Missing'}")
        st.text(f"Status: {'🟢 Active' if st.session_state.conversation_pk else '🟡 Standby'}")
    
    st.divider()
    
    st.subheader("💡 Maizey Capabilities")
    capabilities = [
        "🔍 Student & Faculty Search",
        "🏢 Building & Room Info", 
        "📚 Course Data & Enrollment",
        "🔗 API Endpoint Generation",
        "💻 Code Examples (Python/JS)",
        "📄 Documentation & Guides"
    ]
    
    for capability in capabilities:
        st.markdown(f"• {capability}")
    
    st.divider()
    
    st.subheader("🎯 Quick Examples")
    examples = [
        "Get student info by uniqname",
        "Find rooms in Shapiro building", 
        "Course enrollment API",
        "Faculty directory search",
        "Building capacity data"
    ]
    
    for example in examples:
        if st.button(f"� {example}", key=f"ex_{hash(example)}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": example})
            with st.chat_message("user"):
                st.markdown(example)
            
            with st.chat_message("assistant"):
                with st.spinner("Maizey is thinking..."):
                    response = send_message_to_maizey(example)
                display_formatted_response(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
