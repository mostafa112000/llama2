import streamlit as st
import requests
import base64

# ==== App config ====
st.set_page_config(page_title="🛡️ PioNeer+")

# ==== Defaults ====
DEFAULT_API_URL = "https://25bddf9208eb.ngrok-free.app"

# ==== Sidebar ====
with st.sidebar:
    st.title("🛡️ PioNeer+")
    st.write("Chat interface for the self-hosted GRC Assistant API.")

    api_url = st.text_input("🔗 API Base URL", value=DEFAULT_API_URL)

    #st.markdown("**Authentication (Optional)**")
    use_api_key = None
    api_key = None

    use_basic = None
    basic_user = None
    basic_pass = None

    st.markdown("---")
    max_tokens = st.slider("Max Tokens", 64, 2048, 320, 32)

    if st.button("🔄 Clear Chat History"):
        st.session_state.messages = []
        st.session_state.session_id = None

# ==== Session state ====
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# ==== Show conversation ====
if not st.session_state.messages:
    st.session_state.messages.append(
        {"role": "assistant", "content": "👋 Hello! Ask me anything about GRC, Risk, and Compliance."}
    )

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ==== Backend call ====
def call_backend(user_query: str) -> str:
    headers = {"Content-Type": "application/json"}

    # Optional X-API-Key
    if use_api_key and api_key:
        headers["X-API-Key"] = api_key

    # Optional Basic Auth
    if use_basic and basic_user and basic_pass:
        token = base64.b64encode(f"{basic_user}:{basic_pass}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"

    payload = {
        "user_query": user_query,
        "session_id": st.session_state.session_id,  # may be None
        "max_tokens": max_tokens,
    }

    try:
        resp = requests.post(f"{api_url}/generate", headers=headers, json=payload, timeout=60)
    except Exception as e:
        return f"❌ Connection error: {e}"

    if resp.status_code != 200:
        return f"❌ Error {resp.status_code}: {resp.text}"

    data = resp.json()

    if isinstance(data, dict):
        if data.get("session_id"):
            st.session_state.session_id = data["session_id"]
        return data.get("response", "⚠️ No 'response' field in server reply.")
    else:
        return "⚠️ Unexpected server response format."

# ==== User input ====
if prompt := st.chat_input("Enter your GRC-related question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Generating..."):
            result = call_backend(prompt)
            st.markdown(result)
            st.session_state.messages.append({"role": "assistant", "content": result})


