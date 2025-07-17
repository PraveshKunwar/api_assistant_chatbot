import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time
import re
from datetime import datetime
import uuid

load_dotenv()

st.set_page_config(
    page_title="U-M Maizey Assistant", 
    page_icon="🌽",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

def initialize_session_state():
    if "conversations" not in st.session_state:
        st.session_state.conversations = {}
    
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = None
    
    if "conversation_pk" not in st.session_state:
        st.session_state.conversation_pk = None
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "user_stats" not in st.session_state:
        st.session_state.user_stats = {
            "total_conversations": 0,
            "total_messages": 0,
            "session_start": datetime.now()
        }

def create_new_conversation():
    conversation_id = str(uuid.uuid4())
    st.session_state.conversations[conversation_id] = {
        "id": conversation_id,
        "title": "New Chat",
        "created_at": datetime.now(),
        "messages": [],
        "maizey_conversation_pk": None
    }
    st.session_state.current_conversation_id = conversation_id
    st.session_state.messages = []
    st.session_state.conversation_pk = None
    st.session_state.user_stats["total_conversations"] += 1
    return conversation_id

def get_current_conversation():
    if st.session_state.current_conversation_id:
        return st.session_state.conversations.get(st.session_state.current_conversation_id)
    return None

def save_message_to_conversation(role, content):
    current_conv = get_current_conversation()
    if current_conv:
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
            "id": str(uuid.uuid4())
        }
        current_conv["messages"].append(message)
        st.session_state.user_stats["total_messages"] += 1
        
        if role == "user" and current_conv["title"] == "New Chat":
            current_conv["title"] = content[:50] + "..." if len(content) > 50 else content

def load_conversation(conversation_id):
    if conversation_id in st.session_state.conversations:
        st.session_state.current_conversation_id = conversation_id
        conv = st.session_state.conversations[conversation_id]
        st.session_state.messages = [{"role": msg["role"], "content": msg["content"]} for msg in conv["messages"]]
        st.session_state.conversation_pk = conv["maizey_conversation_pk"]

def delete_conversation(conversation_id):
    if conversation_id in st.session_state.conversations:
        del st.session_state.conversations[conversation_id]
        if st.session_state.current_conversation_id == conversation_id:
            st.session_state.current_conversation_id = None
            st.session_state.messages = []
            st.session_state.conversation_pk = None

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
            pk = conversation_data["pk"]
            
            current_conv = get_current_conversation()
            if current_conv:
                current_conv["maizey_conversation_pk"] = pk
            
            return pk
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

initialize_session_state()

if not st.session_state.current_conversation_id:
    create_new_conversation()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            display_formatted_response(message["content"])
        else:
            st.markdown(message["content"])

if prompt := st.chat_input("Ask Maizey anything about University of Michigan..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message_to_conversation("user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Maizey is thinking..."):
            response = send_message_to_maizey(prompt)
        
        display_formatted_response(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    save_message_to_conversation("assistant", response)

with st.sidebar:
    st.header("🌽 Maizey AI Assistant")
    
    if st.session_state.conversation_pk:
        st.success("✅ Connected")
        st.caption(f"Conv ID: {st.session_state.conversation_pk}")
    else:
        st.info("🆕 Ready to Connect")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Chat", use_container_width=True):
            create_new_conversation()
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
    
    st.subheader("💬 Chat History")
    if st.session_state.conversations:
        for conv_id, conv in sorted(st.session_state.conversations.items(), 
                                  key=lambda x: x[1]["created_at"], reverse=True):
            is_current = conv_id == st.session_state.current_conversation_id
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(
                    f"{'🟢' if is_current else '💬'} {conv['title'][:30]}...",
                    key=f"load_{conv_id}",
                    use_container_width=True,
                    disabled=is_current
                ):
                    load_conversation(conv_id)
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"del_{conv_id}", help="Delete conversation"):
                    delete_conversation(conv_id)
                    st.rerun()
            
            st.caption(f"{len(conv['messages'])} messages • {conv['created_at'].strftime('%m/%d %H:%M')}")
    else:
        st.info("No conversations yet")
    
    if st.button("🗑️ Clear All History", use_container_width=True):
        st.session_state.conversations = {}
        st.session_state.current_conversation_id = None
        st.session_state.messages = []
        st.session_state.conversation_pk = None
        st.session_state.user_stats = {
            "total_conversations": 0,
            "total_messages": 0,
            "session_start": datetime.now()
        }
        st.rerun()
    
    st.divider()
    
    st.subheader("🔧 Configuration")
    with st.expander("Connection Details"):
        st.text(f"Endpoint: umgpt.umich.edu")
        st.text(f"Project: {project_pk[:12]}...")
        st.text(f"Token: {'✅ Valid' if ACCESS_TOKEN else '❌ Missing'}")
        st.text(f"Status: {'🟢 Active' if st.session_state.conversation_pk else '🟡 Standby'}")
    
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
        if st.button(f"💡 {example}", key=f"ex_{hash(example)}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": example})
            save_message_to_conversation("user", example)
            
            with st.chat_message("user"):
                st.markdown(example)
            
            with st.chat_message("assistant"):
                with st.spinner("Maizey is thinking..."):
                    response = send_message_to_maizey(example)
                display_formatted_response(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            save_message_to_conversation("assistant", response)
            st.rerun()
