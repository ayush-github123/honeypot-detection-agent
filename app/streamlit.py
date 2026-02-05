import streamlit as st
import requests
import uuid
from datetime import datetime

# -------------------------
# CONFIG
# -------------------------
BASE_URL = "http://127.0.0.1:8000/message"
API_KEY = "dev-secret-key"


# -------------------------
# SESSION STATE INIT
# -------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "conversation" not in st.session_state:
    st.session_state.conversation = []

if "intelligence" not in st.session_state:
    st.session_state.intelligence = {}

if "scam_detected" not in st.session_state:
    st.session_state.scam_detected = False

if "completeness" not in st.session_state:
    st.session_state.completeness = 0.0

if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0


# -------------------------
# PAGE HEADER
# -------------------------
st.title("🕵️ Honeypot Scam Agent Tester")

st.caption(f"Session ID: `{st.session_state.session_id}`")


# -------------------------
# SIDEBAR METRICS
# -------------------------
with st.sidebar:
    st.header("📊 Intelligence Dashboard")

    st.metric("Scam Detected", st.session_state.scam_detected)
    st.metric("Completeness Score", st.session_state.completeness)
    st.metric("Turns", st.session_state.turn_count)

    st.divider()

    st.subheader("Extracted Intelligence")

    if st.session_state.intelligence:
        st.json(st.session_state.intelligence)
    else:
        st.info("No intelligence extracted yet.")

    st.divider()

    if st.button("🔄 Reset Session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.conversation = []
        st.session_state.intelligence = {}
        st.session_state.scam_detected = False
        st.session_state.completeness = 0.0
        st.session_state.turn_count = 0
        st.rerun()


# -------------------------
# CHAT DISPLAY
# -------------------------
st.subheader("💬 Conversation")

for msg in st.session_state.conversation:
    if msg["sender"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["text"])
    else:
        with st.chat_message("user"):
            st.write(msg["text"])


# -------------------------
# MESSAGE INPUT
# -------------------------
user_input = st.chat_input("Type scammer message...")

if user_input:

    # Add scammer message locally
    scammer_msg = {
        "sender": "scammer",
        "text": user_input,
        "timestamp": datetime.utcnow().isoformat()
    }

    st.session_state.conversation.append(scammer_msg)

    # Prepare request payload
    payload = {
        "sessionId": st.session_state.session_id,
        "message": scammer_msg,
        "conversationHistory": st.session_state.conversation[:-1],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }

    # Send request
    try:
        response = requests.post(BASE_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        reply = data["reply"]

        # Save assistant reply
        st.session_state.conversation.append({
            "sender": "assistant",
            "text": reply,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Update dashboard data
        st.session_state.scam_detected = data.get("scam_detected", False)
        st.session_state.intelligence = data.get("intelligence", {})
        st.session_state.completeness = data.get("completeness_score", 0.0)
        st.session_state.turn_count = data.get("turn_count", 0)

        st.rerun()

    except Exception as e:
        st.error(f"Backend Error: {str(e)}")
