import streamlit as st
from PIL import Image
import requests
import os
from dotenv import load_dotenv
import re
import base64
import streamlit.components.v1 as components
import json
import uuid
from datetime import datetime

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

load_dotenv()

def get_session_id():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def create_favicon():
    img = Image.open("umich.png")
    img = img.resize((32, 32)) 
    return img

def get_redis_client():
    if not REDIS_AVAILABLE:
        return None
    
    try:
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            return redis.Redis.from_url(redis_url)
        else:
            return None
    except Exception as e:
        return None

def test_redis_connection():
    redis_client = get_redis_client()
    if not redis_client:
        return False, "Redis client not available"
    
    try:
        test_key = f"test_{uuid.uuid4()}"
        redis_client.set(test_key, "test_value")
        result = redis_client.get(test_key)
        redis_client.delete(test_key)
        
        if isinstance(result, bytes):
            result = result.decode('utf-8')
        
        if result == "test_value":
            return True, "Redis connection successful"
        else:
            return False, "Redis test failed"
    except Exception as e:
        return False, f"Redis error: {str(e)}"

def save_chat_to_redis(conversation_id, messages):
    if not conversation_id or not messages:
        return
        
    redis_client = get_redis_client()
    if not redis_client:
        return
    
    try:
        chat_data = {
            'messages': messages,
            'timestamp': datetime.now().isoformat(),
            'conversation_id': conversation_id
        }
        redis_client.setex(
            f"um_chat:{conversation_id}", 
            604800, 
            json.dumps(chat_data)
        )
    except Exception as e:
        pass

def load_chat_from_redis(conversation_id):
    if not conversation_id:
        return []
        
    redis_client = get_redis_client()
    if not redis_client:
        return []
    
    try:
        data = redis_client.get(f"um_chat:{conversation_id}")
        if data:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            chat_data = json.loads(data)
            return chat_data.get('messages', [])
        return []
    except Exception as e:
        return []

def get_chat_history_list():
    redis_client = get_redis_client()
    if not redis_client:
        return []
    
    try:
        keys = redis_client.keys("um_chat:*")
        chat_list = []
        
        for key in keys:
            try:
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                data = redis_client.get(key)
                if data:
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    chat_data = json.loads(data)
                    session_id = key.replace("um_chat:", "")
                    timestamp = chat_data.get('timestamp', '')
                    messages = chat_data.get('messages', [])
                    
                    if messages:
                        first_user_msg = next((msg['content'] for msg in messages if msg['role'] == 'user'), 'New Chat')
                        title = first_user_msg[:50] + "..." if len(first_user_msg) > 50 else first_user_msg
                        
                        chat_list.append({
                            'session_id': session_id,
                            'title': title,
                            'timestamp': timestamp,
                            'message_count': len(messages)
                        })
            except:
                continue
        
        chat_list.sort(key=lambda x: x['timestamp'], reverse=True)
        return chat_list[:10]
    except Exception as e:
        return []

def load_chat_history(session_id):
    messages = load_chat_from_redis(session_id)
    if messages:
        st.session_state.messages = messages
        st.session_state.session_id = session_id
        st.session_state.conversation_pk = None
        st.rerun()

def clear_all_chat_history():
    redis_client = get_redis_client()
    if not redis_client:
        return False
    
    try:
        keys = redis_client.keys("um_chat:*")
        if keys:
            for key in keys:
                redis_client.delete(key)
        return True
    except Exception as e:
        return False

def delete_specific_chat(session_id):
    redis_client = get_redis_client()
    if not redis_client:
        return False
    
    try:
        redis_client.delete(f"um_chat:{session_id}")
        return True
    except Exception as e:
        return False

if 'messages' not in st.session_state:
    st.session_state.messages = []

session_id = get_session_id()

if not st.session_state.messages:
    saved_messages = load_chat_from_redis(session_id)
    if saved_messages:
        st.session_state.messages = saved_messages

st.set_page_config(
    page_title="UM API Assistant",
    page_icon=create_favicon(),
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    :root {
        --um-maize: #FFCB05;
        --um-blue: #00274C;
        --um-light-blue: #0066CC;
        --um-gray: #F5F5F5;
        --um-dark-gray: #333333;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp > header {visibility: hidden;}
    
    .main-header {
        background: var(--um-blue);
        padding: 0.8rem 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 39, 76, 0.2);
        position: sticky;
        top: 0;
        z-index: 999;
        border: 2px solid var(--um-maize);
    }
    
    .main-header h1 {
        color: var(--um-maize) !important;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .stButton > button {
        background: var(--um-maize);
        color: var(--um-blue);
        border: none;
        border-radius: 25px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 203, 5, 0.3);
    }
    
    .stButton > button:hover {
        background: #E6B800;
        color: var(--um-blue) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 203, 5, 0.4);
    }
    
    .status-connected {
        background: #28a745;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        font-size: 0.9rem;
        margin: 0.5rem 0;
    }
    
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 10px;
        padding: 0.75rem;
        margin: 1rem 0;
        color: #856404;
        font-size: 0.9rem;
    }
    
    .copy-button {
        background: var(--um-maize) !important;
        color: var(--um-blue) !important;
        border: 1px solid var(--um-blue) !important;
        border-radius: 20px !important;
        padding: 0.25rem 0.75rem !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
    }
    
    .copy-button:hover {
        background: #E6B800 !important;
        transform: translateY(-1px) !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1><img src="data:image/png;base64,{}" width="50" height="50" style="vertical-align: middle; margin-right: 15px;">UM API Assistant</h1>
</div>
""".format(get_base64_image("umich.png")), unsafe_allow_html=True)

url = 'https://umgpt.umich.edu'
project_pk = os.getenv("PROJECT_PK")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

if not ACCESS_TOKEN:
    st.error("🔴 **ACCESS_TOKEN** not found in environment variables")
    st.info(" Add to your .env file: `ACCESS_TOKEN=your_maizey_api_token_here`")
    st.stop()

if not project_pk:
    st.error("🔴 **PROJECT_PK** not found in environment variables")
    st.info(" Add to your .env file: `PROJECT_PK=your_project_guid_here`")
    st.stop()

if "conversation_pk" not in st.session_state:
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
            return conversation_data["pk"]
        else:
            st.error(f"🔴 Failed to create conversation. Status: {response.status_code}")
            st.error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        st.error(f"🔴 Error creating conversation: {str(e)}")
        return None

def send_message_to_maizey(user_question):
    if not st.session_state.conversation_pk:
        st.session_state.conversation_pk = create_conversation()
        if not st.session_state.conversation_pk:
            return "🔴 Could not start conversation with Maizey. Please try again."
    
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
            return f"🔴 Failed to send message. Status: {response.status_code}\nResponse: {response.text}"
            
    except Exception as e:
        return f"🔴 Error sending message: {str(e)}"

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
    
    st.markdown("---")
    
    col1, col2 = st.columns([6, 1])
    with col2:
        copy_key = f"copy_{hash(response_text)}"
        if st.button("📋 Copy", key=copy_key, help="Copy full response to clipboard", use_container_width=True):
            if PYPERCLIP_AVAILABLE:
                try:
                    pyperclip.copy(response_text)
                    st.success("✅ Copied to clipboard!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Copy failed: {str(e)}")
                    st.session_state[f'show_fallback_{copy_key}'] = True
            else:
                st.warning("⚠️ pyperclip not available. Install with: pip install pyperclip")
                st.session_state[f'show_fallback_{copy_key}'] = True
    
    if st.session_state.get(f'show_fallback_{copy_key}', False):
        st.markdown("**Manual Copy (Fallback):**")
        st.text_area(
            "Select all and copy (Ctrl+A, Ctrl+C):",
            value=response_text,
            height=100,
            key=f"fallback_area_{copy_key}",
            help="pyperclip failed, copy manually from here"
        )
        if st.button("❌ Close", key=f"close_{copy_key}"):
            st.session_state[f'show_fallback_{copy_key}'] = False
            st.rerun()
    
    st.markdown("---")

assistant_avatar = get_base64_image("umich.png")
for message in st.session_state.messages:
    if message["role"] == "assistant":
        with st.chat_message("assistant", avatar=f"data:image/png;base64,{assistant_avatar}"):
            display_formatted_response(message["content"])
    else:
        with st.chat_message("user"):
            st.markdown(message["content"])

if 'auto_input' in st.session_state:
    prompt = st.session_state.auto_input
    del st.session_state.auto_input
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=f"data:image/png;base64,{assistant_avatar}"):
        with st.spinner("Maizey is thinking..."):
            response = send_message_to_maizey(prompt)
        display_formatted_response(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    save_chat_to_redis(session_id, st.session_state.messages)

if prompt := st.chat_input("Ask Maizey anything about University of Michigan..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=f"data:image/png;base64,{assistant_avatar}"):
        with st.spinner("Maizey is thinking..."):
            response = send_message_to_maizey(prompt)
        
        display_formatted_response(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    save_chat_to_redis(session_id, st.session_state.messages)

with st.sidebar:
    redis_client = get_redis_client()
    
    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ Important Notice:</strong><br>
        Chat history is not permanently saved. Your conversation will be lost when you refresh the page or start a new session.
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.conversation_pk:
        st.markdown('<div class="status-connected">🟢 Connected to Maizey</div>', unsafe_allow_html=True)
    
    st.markdown("### 🔗 Connection Details")
    with st.expander("Developer Info", expanded=False):
        st.markdown(f"""
        **Endpoint:** `umgpt.umich.edu`  
        **Project:** `{project_pk[:12]}...`  
        **Token:** {'✅ Valid' if ACCESS_TOKEN else '❌ Missing'}  
        **Status:** {'🟢 Active Chat' if st.session_state.conversation_pk else '⏸️ Standby'}  
        **Storage:** {'☁️ Redis' if redis_client else '💾 Session'}
        """)
        
        if st.session_state.conversation_pk:
            st.markdown(f"**Conversation ID:** `{str(st.session_state.conversation_pk)}`")
    
    st.divider()
    
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🆕 New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_pk = None
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    
    st.divider()
    
    st.markdown("### 💡 Try These Examples")
    examples = [
        "Find student info by uniqname",
        "List rooms in Shapiro Library", 
        "Course enrollment API example",
        "Faculty directory search",
        "Building capacity information",
        "Campus dining hours",
        "Library study spaces"
    ]
    
    for example in examples:
        if st.button(f"💬 {example}", key=f"ex_{hash(example)}", use_container_width=True):
            st.session_state['auto_input'] = example
            st.rerun()
    
    st.divider()
    
    st.markdown("### 🔗 Helpful Links")
    
    st.markdown("**📁 API Directory**")
    st.markdown("🔗 [UMich API Directory](https://dir.api.it.umich.edu/)")
    
    st.markdown("**📋 Additional Information**")
    st.markdown("🔗 [Location Abbreviations](https://ro.umich.edu/calendars/schedule-classes/location-abbreviations)")
    
    st.markdown("**⚠️ Error Code Explanations**")
    with st.expander("HTTP Status Codes", expanded=False):
        st.markdown("""
        **2xx Success Codes:**
        - `200 OK` - Request successful
        - `201 Created` - Resource created successfully
        - `204 No Content` - Request successful, no content returned
        
        **4xx Client Errors:**
        - `400 Bad Request` - Invalid request syntax
        - `401 Unauthorized` - Authentication required
        - `403 Forbidden` - Access denied
        - `404 Not Found` - Resource not found
        - `429 Too Many Requests` - Rate limit exceeded
        
        **5xx Server Errors:**
        - `500 Internal Server Error` - Server encountered an error
        - `502 Bad Gateway` - Invalid response from upstream server
        - `503 Service Unavailable` - Server temporarily unavailable
        """)
    
    st.markdown("🔗 [MDN HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)")
    
    st.divider()
    
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding: 1rem; background: var(--um-blue); color: var(--um-maize); border-radius: 10px;">
        <strong>〽️ Go Blue!</strong><br>
        <small>University of Michigan<br>Powered by Maizey AI</small>
    </div>
    """, unsafe_allow_html=True)