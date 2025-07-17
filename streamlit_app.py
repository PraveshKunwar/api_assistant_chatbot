import streamlit as st
from PIL import Image
import requests
import os
from dotenv import load_dotenv
import re
import base64
import streamlit.components.v1 as components

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
def create_favicon():
    img = Image.open("umich.png")
    img = img.resize((32, 32)) 
    return img
    
load_dotenv()

# Configure page
st.set_page_config(
    page_title="UM API Assistant",
    page_icon=create_favicon(),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for U-M styling
st.markdown("""
<style>
    /* Import U-M colors and fonts */
    :root {
        --um-maize: #FFCB05;
        --um-blue: #00274C;
        --um-light-blue: #0066CC;
        --um-gray: #F5F5F5;
        --um-dark-gray: #333333;
    }
    
    /* Hide default Streamlit styling */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp > header {visibility: hidden;}
    
    /* Main container styling */
    .main-header {
        background: var(--um-blue);
        padding: 0.1rem 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 39, 76, 0.2);
    }
    
    .main-header h1 {
        color: var(--um-maize) !important;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        color: white !important;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        opacity: 0.9;
    }
    
    /* Chat container styling */
    # .chat-container {
    #     background: white;    
    #     border-radius: 15px;
    #     padding: 1.5rem;
    #     box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    #     margin-bottom: 2rem;
    # }
    
    /* Button styling */
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
    
    /* Sidebar styling */
    .css-1d391kg {
        background: var(--um-gray);
    }
    
    .sidebar-header {
        background: var(--um-blue);
        color: var(--um-maize);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    /* Status indicators */
    .status-connected {
        background: #28a745;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        font-size: 0.9rem;
        margin: 0.5rem 0;
    }
    
    .status-ready {
        background: var(--um-light-blue);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        font-size: 0.9rem;
        margin: 0.5rem 0;
    }
    
    /* Quick action buttons */
    .quick-action {
        background: white;
        border: 2px solid var(--um-blue);
        color: var(--um-blue);
        border-radius: 20px;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }
    
    .quick-action:hover {
        background: var(--um-blue);
        color: white;
    }
    
    /* Capability cards */
    .capability-card {
        background: white;
        border-left: 4px solid var(--um-maize);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Chat messages */
    .chat-message {
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 15px;
        background: var(--um-gray);
    }
    
    .user-message {
        background: var(--um-blue);
        color: white;
        margin-left: 20%;
    }
    
    .assistant-message {
        background: white;
        border: 2px solid var(--um-maize);
        margin-right: 20%;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid var(--um-blue);
        padding: 0.75rem 1.5rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--um-maize);
        box-shadow: 0 0 0 0.2rem rgba(255, 203, 5, 0.25);
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-top-color: var(--um-maize) !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: var(--um-blue);
        color: var(--um-maize);
        border-radius: 10px;
    }
    
    /* Code blocks */
    .stCodeBlock {
        border-radius: 10px;
        border: 1px solid var(--um-maize);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        border-radius: 10px;
    }
    
    .stError {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        border-radius: 10px;
    }
    
    /* University branding */
    .um-logo {
        width: 40px;
        height: 40px;
        background: var(--um-maize);
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: var(--um-blue);
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Main header with U-M branding
st.markdown("""
<div class="main-header">
    <h1><img src="data:image/png;base64,{}" width="50" height="50" style="vertical-align: middle; margin-right: 15px;">UM API Assistant</h1>
</div>
""".format(get_base64_image("umich.png")), unsafe_allow_html=True)

# API Configuration
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
    
    if st.button(" Copy Response", key=f"copy_{hash(response_text)}"):
        copy_js = f"""
        <script>
        navigator.clipboard.writeText(`{response_text.replace('`', '\\`')}`).then(function() {{
            console.log('Copied to clipboard');
        }});
        </script>
        """
        components.html(copy_js, height=0)
        st.toast(" Copied!")

# Main chat interface
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Display chat history
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

if prompt := st.chat_input("Ask Maizey anything about University of Michigan..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=f"data:image/png;base64,{assistant_avatar}"):
        with st.spinner("Maizey is thinking..."):
            response = send_message_to_maizey(prompt)
        
        display_formatted_response(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown('</div>', unsafe_allow_html=True)

# Sidebar with U-M styling
with st.sidebar:
    umich_icon = get_base64_image("umich.png")
    # st.markdown(f"""
    # <div class="sidebar-header">
    #     <img src="data:image/png;base64,{umich_icon}" width="30" height="30" style="vertical-align: middle; margin-right: 10px;">
    #     <strong>Maizey API Assistant!</strong>
    # </div>
    # """, unsafe_allow_html=True)
    
    # Connection Status
    if st.session_state.conversation_pk:
        # st.caption(f" Conversation ID: {str(st.session_state.conversation_pk)[:12]}...")
        st.markdown('<div class="status-connected"> Connected to Maizey</div>', unsafe_allow_html=True)
        
    # else:
    #     st.markdown('<div class="status-ready"> Start a Conversation</div>', unsafe_allow_html=True)
    
    # Action buttons
    st.markdown("###  Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(" New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_pk = None
            st.rerun()
    
    with col2:
        if st.button(" Test API", use_container_width=True):
            with st.spinner("Testing connection..."):
                test_headers = {
                    'accept': 'application/json',
                    'Authorization': 'Bearer ' + ACCESS_TOKEN,
                    'Content-Type': 'application/json'
                }
                test_url = f'{url}/maizey/api/projects/{project_pk}/conversation/'
                
                try:
                    test_response = requests.post(test_url, headers=test_headers, json={})
                    if test_response.status_code == 201:
                        st.toast(" API Connected")
                    else:
                        st.toast(f"Status: {test_response.status_code}")
                except Exception as e:
                    st.toast(f"Connection Failed")
    
    st.divider()
    
    # Configuration Details
    st.markdown("### System Configuration")
    with st.expander(" Connection Details", expanded=False):
        st.markdown(f"""
        **Endpoint:** `umgpt.umich.edu`  
        **Project:** `{project_pk[:12]}...`  
        **Token:** {' Valid' if ACCESS_TOKEN else 'Missing'}  
        **Status:** {' Active Chat' if st.session_state.conversation_pk else 'Standby'}
        """)
        
        if st.session_state.conversation_pk:
            st.markdown(f"**🔗 Conversation ID:** `{str(st.session_state.conversation_pk)}`")
    
    st.divider()
    
    # Quick Examples
    st.markdown("### Try These Examples")
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
        if st.button(f" {example}", key=f"ex_{hash(example)}", use_container_width=True):
            st.session_state['auto_input'] = example
            st.rerun()
    
    st.divider()
    # Maizey Capabilities
    # st.markdown("### Maizey Capabilities")
    # capabilities = [
    #     "Student & Faculty Directory",
    #     "Building & Room Information", 
    #     "Course Data & Enrollment",
    #     "API Endpoint Generation",
    #     "Code Examples & Documentation",
    #     "University Policies & Procedures"
    # ]
    
    # for capability in capabilities:
    #     st.markdown(f"""
    #     <div class="capability-card">
    #         {capability}
    #     </div>
    #     """, unsafe_allow_html=True)
    
    # st.divider()
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding: 1rem; background: var(--um-blue); color: var(--um-maize); border-radius: 10px;">
        <strong>〽️ Go Blue!</strong><br>
        <small>University of Michigan<br>Powered by Maizey AI</small>
    </div>
    """, unsafe_allow_html=True)