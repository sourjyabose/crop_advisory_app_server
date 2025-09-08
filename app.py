# app.py
import os
import httpx
import streamlit as st
from dotenv import load_dotenv

# -----------------------------
# Load API keys
# -----------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # multilingual model

# -----------------------------
# Streamlit page setup
# -----------------------------
st.set_page_config(page_title="Multilingual Chatbot", layout="centered")
st.title("🌐 Multilingual Chatbot")
st.markdown("Ask any question in any language. The chatbot will automatically detect the language and reply accordingly.")

# -----------------------------
# Session state for chat history
# -----------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# -----------------------------
# User input form
# -----------------------------
with st.form(key="chat_form"):
    user_message = st.text_input("Your question:")
    submit_button = st.form_submit_button("Send")

# -----------------------------
# Helper function: call GPT
# -----------------------------
def call_llm(user_message: str) -> str:
    if not OPENAI_API_KEY:
        return "No LLM API key provided."

    system_prompt = """
You are a helpful multilingual chatbot. Automatically detect the language of the user's message
and reply in the same language. Be clear, concise, and friendly.
"""

    try:
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        body = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.2
        }

        r = httpx.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body, timeout=30)
        r.raise_for_status()
        data = r.json()
        reply = data["choices"][0]["message"]["content"]
        return reply
    except Exception as e:
        return f"Error: {e}"

# -----------------------------
# Process submission
# -----------------------------
if submit_button and user_message:
    st.session_state["messages"].append(("user", user_message))
    reply = call_llm(user_message)
    st.session_state["messages"].append(("bot", reply))

# -----------------------------
# Display chat history
# -----------------------------
for role, content in st.session_state["messages"]:
    if role == "user":
        st.markdown(f"👤 **You:** {content}")
    else:
        st.markdown(f"🤖 **Bot:** {content}")
