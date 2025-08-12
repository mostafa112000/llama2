import streamlit as st
import requests

# Set page title
st.set_page_config(page_title="🛡️ PioNeer+")

# Pre-filled API URL and key
DEFAULT_API_URL = "https://623f34fd1aac.ngrok-free.app"
DEFAULT_API_KEY = "01012025"

# Sidebar setup
with st.sidebar:
    st.title('🛡️ PioNeer+')
    st.write('Interact with our self-hosted GRC LLM (fine-tuned model).')

    api_url = st.text_input('🔗 API Base URL', value=DEFAULT_API_URL)
    api_key = st.text_input('🔑 API Key', type='password', value=DEFAULT_API_KEY)

    st.subheader('⚙️ Parameters')
    temperature = st.slider('Temperature', 0.0, 1.0, 0.7, 0.01)
    top_p = st.slider('Top-p (nucleus sampling)', 0.0, 1.0, 0.9, 0.01)
    max_tokens = st.slider('Max Tokens', 100, 2048, 1024, 50)
    format_type = st.selectbox("Output Format", ["plain", "markdown", "structured"], index=0)

    if st.button("🔄 Clear Chat History"):
        st.session_state.messages = [{"role": "assistant", "content": "👋 Hello! How can I help you with GRC today?"}]

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "👋 Hello! How can I help you with GRC today?"}]

# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Function to call GRC API
def call_grc_api(prompt_text):
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    payload = {
        "prompt": prompt_text,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "format": format_type,
        "use_cache": True
    }
    try:
        response = requests.post(f"{api_url}/generate", headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"❌ Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"❌ Exception: {str(e)}"

# Chat input
if prompt := st.chat_input("Enter your GRC-related prompt..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Generating response..."):
            result = call_grc_api(prompt)
            st.markdown(result)
            st.session_state.messages.append({"role": "assistant", "content": result})
