import streamlit as st
import requests
import base64

# ==== صفحة التطبيق ====
st.set_page_config(page_title="🛡️ PioNeer+")

# ==== القيم الافتراضية من TL;DR ====
DEFAULT_API_URL = "https://25bddf9208eb.ngrok-free.app"

# ==== الشريط الجانبي ====
with st.sidebar:
    st.title("🛡️ PioNeer+")
    st.write("واجهة محادثة لواجهة GRC الذاتية الاستضافة.")

    api_url = st.text_input("🔗 API Base URL", value=DEFAULT_API_URL)

    st.markdown("**Authentication (اختياري)**")
    use_api_key = st.checkbox("Send X-API-Key header", value=False)
    api_key = st.text_input("API Key", type="password") if use_api_key else ""

    use_basic = st.checkbox("Use Basic Auth (Ngrok)", value=False)
    basic_user = st.text_input("Basic user") if use_basic else ""
    basic_pass = st.text_input("Basic password", type="password") if use_basic else ""

    st.markdown("---")
    endpoint = st.radio(
        "Endpoint",
        ["Model-only (/generate)", "RAG (/rag)"],
        index=0,
    )

    # التكوين الحتمي: do_sample=false في السيرفر – لا نعرض temperature/top_p
    max_tokens = st.slider("Max Tokens", 64, 2048, 320, 32)

    # إعدادات RAG لكل طلب
    rag_enabled = True
    if endpoint == "RAG (/rag)":
        rag_enabled = st.checkbox("Enable retrieval for this call", value=True)

    if st.button("🔄 Clear Chat History"):
        st.session_state.messages = []
        st.session_state.session_id = None

# ==== حالة الجلسة ====
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# ==== عرض المحادثة ====
if not st.session_state.messages:
    st.session_state.messages.append(
        {"role": "assistant", "content": "👋 أهلا بك! اسألني أي شيء في حوكمة وإدارة المخاطر والالتزام."}
    )

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ==== دالة النداء ====
def call_backend(user_query: str) -> str:
    # الهيدرز
    headers = {"Content-Type": "application/json"}

    # X-API-Key اختياري
    if use_api_key and api_key:
        headers["X-API-Key"] = api_key

    # Basic Auth اختياري
    if use_basic and basic_user and basic_pass:
        token = base64.b64encode(f"{basic_user}:{basic_pass}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"

    # اختيار المسار وبناء الحمولة حسب الوثائق
    is_rag = endpoint.startswith("RAG")
    path = "/rag" if is_rag else "/generate"

    payload = {
        "user_query": user_query,
        "session_id": st.session_state.session_id,  # قد تكون None؛ السيرفر سيعيد واحدة
        "max_tokens": max_tokens,
        # ملاحظة: السيرفر حتمي (do_sample=false) لذا temperature/top_p غير مستخدمة
    }

    if is_rag:
        # تمكين/تعطيل الاسترجاع لكل طلب
        payload["use_retrieval"] = bool(rag_enabled)

    try:
        resp = requests.post(f"{api_url}{path}", headers=headers, json=payload, timeout=60)
    except Exception as e:
        return f"❌ Connection error: {e}"

    if resp.status_code != 200:
        return f"❌ Error {resp.status_code}: {resp.text}"

    data = resp.json()

    # نتوقع هيكلًا مثل:
    # { "response": "...", "session_id": "..." }
    if isinstance(data, dict):
        if data.get("session_id"):
            st.session_state.session_id = data["session_id"]
        return data.get("response", "⚠️ No 'response' field in server reply.")
    else:
        return "⚠️ Unexpected server response format."

# ==== إدخال المستخدم ====
if prompt := st.chat_input("اكتب سؤالك في GRC..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Generating..."):
            result = call_backend(prompt)
            st.markdown(result)
            st.session_state.messages.append({"role": "assistant", "content": result})

# ==== تلميحات سريعة ====
with st.expander("ℹ️ Notes"):
    st.markdown(
        """
- الخادم مضبوط على مخرجات **حتمية** (`do_sample=false`) لذا **temperature/top_p** يتم تجاهلهما.
- يمكنك تشغيل الذاكرة القصيرة عبر **session_id**؛ إن لم ترسله، سيُعاد من الخادم ونخزّنه تلقائيا.
- اختر **/rag** لتعزيز الإجابة بالاسترجاع، ويمكنك تعطيله لكل طلب من الخيار الجانبي.
- المصادقة:
  - محليًا: لا شيء.
  - Ngrok Basic Auth: فعّل خيار Basic وادخل المستخدم/كلمة المرور.
  - API Key: فعّل خيار X-API-Key وأدخل المفتاح إن كانت الخلفية مفعّلة له.
"""
    )
