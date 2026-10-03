"""
frontend.py — your app's face.

This file contains EVERYTHING to do with how the app looks and behaves on
screen: the page layout, the colors, the chat bubbles, the buttons, the
side panel with past chats, and the dark/light mode switch. It contains
NO AI logic at all, and you don't need to edit it for your capstone —
everything you build lives in ai_backend.py.

All the "brains" (the personality, the settings, the code that talks to
Gemini) live in ai_backend.py — we just import what we need from there.

Run the app with:  streamlit run frontend.py
"""

import streamlit as st

import chat_store
from ai_backend import (
    ask_ai,
    APP_NAME,
    APP_DESCRIPTION,
    WELCOME_MESSAGE,
    SUGGESTED_PROMPTS,
)


def login_is_configured() -> bool:
    """
    True when Google login details exist in Streamlit's secrets — that's
    how a deployed, public copy of this app runs. On a student's own
    machine there are no secrets, so there's no login screen at all.
    """
    try:
        return "auth" in st.secrets
    except Exception:
        return False

# ---------------------------------------------------------------------
# Page setup — title in the browser tab, icon, layout
# ---------------------------------------------------------------------
st.set_page_config(
    page_title=f"{APP_NAME} — Your AI Sidekick",
    page_icon="✨",
    layout="centered",
)

# ---------------------------------------------------------------------
# Dark / light mode
# ---------------------------------------------------------------------
# Streamlit reads its colors from a "theme" (normally a config file that
# can't change while the app runs). To let the user flip modes with a
# switch, we override the theme colors at runtime and rerun the app.

LIGHT_THEME = {
    "theme.base": "light",
    "theme.primaryColor": "#722DEA",
    "theme.backgroundColor": "#FDFCFFE1",
    "theme.secondaryBackgroundColor": "#F3EFFBE6",
    "theme.textColor": "#181527",
}

DARK_THEME = {
    "theme.base": "dark",
    "theme.primaryColor": "#A48AF3",
    "theme.backgroundColor": "#181525",
    "theme.secondaryBackgroundColor": "#1A1A1B",
    "theme.textColor": "#D2D1D3",
}

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Apply the chosen theme at the very start of every rerun, so the whole
# page (including Streamlit's own widgets) is drawn in the right colors.
for option, value in (DARK_THEME if st.session_state.dark_mode else LIGHT_THEME).items():
    st._config.set_option(option, value)

# Accent colors for our own custom styling, matched to the current mode
ACCENT = "#9A81E4" if st.session_state.dark_mode else "#7131E0"
ACCENT_HOVER_TEXT = "#0D0A17" if st.session_state.dark_mode else "#FFFFFF"

# Chat bubble colors: the user's bubble is always bold purple with white
# text; the AI's bubble matches the theme's secondary background.
USER_BUBBLE = "#7C3AED"
AI_BUBBLE = "#221B38" if st.session_state.dark_mode else "#F3EFFB"

# ---------------------------------------------------------------------
# Styling — a splash of color so the app doesn't look like default gray
# ---------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    /* Trim Streamlit's large default top padding so the header banner
       is fully visible without scrolling */
    [data-testid="stMainBlockContainer"], .block-container {{
        padding-top: 2.2rem;
    }}

    /* The big gradient banner at the top */
    .capstone-header {{
        background: linear-gradient(120deg, #7C3AED 0%, #DB2777 100%);
        border-radius: 18px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.2rem;
        color: white;
    }}
    .capstone-header h1 {{
        color: white;
        font-size: 2rem;
        margin: 0 0 0.3rem 0;
        padding: 0;
    }}
    .capstone-header p {{
        color: rgba(255, 255, 255, 0.92);
        font-size: 1.05rem;
        margin: 0;
    }}

    /* The welcome message card shown before the first message */
    .capstone-welcome {{
        background: rgba(124, 58, 237, 0.10);
        border: 1px solid rgba(124, 58, 237, 0.35);
        border-radius: 14px;
        padding: 1rem 1.3rem;
        margin-bottom: 1rem;
        font-size: 1.02rem;
    }}

    /* Suggested-prompt chips: rounded, outlined, fill with color on hover.
       Scoped to the "chips" container so other buttons aren't affected. */
    .st-key-chips .stButton > button {{
        border-radius: 999px;
        border: 1.5px solid {ACCENT};
        color: {ACCENT};
        background: transparent;
        font-size: 0.88rem;
        padding: 0.45rem 0.9rem;
        transition: all 0.15s ease-in-out;
    }}
    .st-key-chips .stButton > button:hover {{
        background: {ACCENT};
        color: {ACCENT_HOVER_TEXT};
        border-color: {ACCENT};
    }}

    /* Past-chat buttons in the sidebar: flat, left-aligned, full width */
    [data-testid="stSidebar"] .stButton > button {{
        justify-content: flex-start;
        text-align: left;
    }}

    /* ---- ChatGPT-style chat bubbles ----
       Each message row is avatar + content. Both get a rounded bubble
       that hugs its text; the user's row is mirrored so their avatar
       and bubble sit on the RIGHT, while the AI's stay on the LEFT. */
    /* Streamlit tints the whole row behind user messages — turn that off
       so only our bubbles carry color */
    [data-testid="stChatMessage"] {{
        background: transparent;
    }}

    [data-testid="stChatMessageContent"] {{
        border-radius: 18px;
        padding: 0.7rem 1.1rem;
        flex-grow: 0;
        width: fit-content;
        max-width: 80%;
        margin: 0;  /* Streamlit auto-centers bubbles; keep them by the avatar */
    }}

    /* The AI's bubble: left side, subtle background, small "tail" corner */
    [data-testid="stChatMessageContent"][aria-label="Chat message from assistant"] {{
        background: {AI_BUBBLE};
        border-bottom-left-radius: 6px;
    }}
  
    /* The user's row: flip it so avatar + bubble sit on the right */
    [data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) {{
        flex-direction: row-reverse;
    }}

    /* The user's bubble: bold purple with white text, tail on the right */
    [data-testid="stChatMessageContent"][aria-label="Chat message from user"] {{
        background: {USER_BUBBLE};
        border-bottom-right-radius: 6px;
    }}
    [data-testid="stChatMessageContent"][aria-label="Chat message from user"] p,
    [data-testid="stChatMessageContent"][aria-label="Chat message from user"] li {{
        color: #FFFFFF;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# Sign in (hosted mode only) — who is using the app?
# ---------------------------------------------------------------------
# On the public URL, students sign in with their school Google account, and
# their email becomes their identity: it decides which chats they see and
# counts their daily messages. On a local install, none of this appears.
if login_is_configured():
    if not st.user.is_logged_in:
        st.markdown(
            f"""
            <div class="capstone-header">
                <h1>✨ {APP_NAME} — Your AI Sidekick</h1>
                <p>{APP_DESCRIPTION}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("Sign in with your school Google account to start chatting.")
        st.button(
            "Sign in with Google", icon=":material/login:", on_click=st.login
        )
        st.stop()  # nothing below runs until they're signed in

    # Optionally only allow school accounts (set allowed_email_domain
    # in secrets to switch this on)
    allowed_domain = st.secrets.get("allowed_email_domain", None)
    if allowed_domain and not st.user.email.endswith(f"@{allowed_domain}"):
        st.warning(
            f"Sorry, {APP_NAME} is only available to @{allowed_domain} "
            "accounts. Please sign in with your school account."
        )
        st.button("Sign out", on_click=st.logout)
        st.stop()

    USER_ID = st.user.email
else:
    # Local install: no login, everyone is the same "local" user
    USER_ID = chat_store.LOCAL_USER_ID

# ---------------------------------------------------------------------
# Session state — which chat is open right now
# ---------------------------------------------------------------------
# The conversations themselves live in the database (see chat_store.py),
# so they survive refreshes and restarts. st.session_state only tracks
# what THIS browser tab is doing right now:
#   active_id -> the id of the open chat (None = a fresh chat that isn't
#                saved yet — we only save a chat once it has a message)
#   messages  -> the open chat's messages, as a working copy
if "messages" not in st.session_state:
    st.session_state.active_id = None
    st.session_state.messages = []


def start_new_chat():
    """Switch to a fresh, empty conversation (saved once it gets a message)."""
    st.session_state.active_id = None
    st.session_state.messages = []

# ---------------------------------------------------------------------
# Sidebar — new chat, past conversations, dark mode, about
# ---------------------------------------------------------------------
with st.sidebar:
    if st.button("New chat", icon=":material/add:", type="secondary", width="stretch"):
        start_new_chat()
        st.rerun()

    st.caption("Chats")

    # List every saved conversation, newest first — click one to reopen it
    # and keep chatting, exactly like the ChatGPT side panel.
    for chat in chat_store.list_chats(USER_ID):
        is_active = chat["id"] == st.session_state.active_id

        title_col, delete_col = st.columns([5, 1])
        if title_col.button(
            chat["title"],
            key=f"open_{chat['id']}",
            type="primary" if is_active else "tertiary",
            width="stretch",
        ):
            st.session_state.active_id = chat["id"]
            st.session_state.messages = chat_store.load_messages(chat["id"])
            st.rerun()
        if delete_col.button(
            "",
            key=f"delete_{chat['id']}",
            icon=":material/delete:",
            type="tertiary",
            help="Delete this chat",
        ):
            chat_store.delete_chat(chat["id"])
            # If we deleted the open chat, fall back to a fresh one
            if is_active:
                start_new_chat()
            st.rerun()

    st.divider()

    # The dark/light mode switch — flips the theme colors and redraws
    dark_mode = st.toggle(":material/dark_mode: Dark mode", value=st.session_state.dark_mode)
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()

    # Signed-in students see who they are and can sign out (hosted mode)
    if login_is_configured() and st.user.is_logged_in:
        st.caption(f":material/account_circle: {st.user.email}")
        st.button("Sign out", icon=":material/logout:", on_click=st.logout)

    with st.expander(f"About {APP_NAME}"):
        st.markdown(APP_DESCRIPTION)
        st.markdown(
            f"{APP_NAME} is an example of an **AI-powered application**: a "
            "simple web page (built with Streamlit) connected to a large "
            "language model (Google's Gemini). This one was built by "
            "customizing `ai_backend.py` — the same file you're using for "
            "your own capstone project."
        )

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
st.markdown(
    f"""
    <div class="capstone-header">
        <h1>✨ {APP_NAME} — Your AI Sidekick</h1>
        <p>{APP_DESCRIPTION}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# Chat history — redraw every message in the open conversation
# ---------------------------------------------------------------------
for message in st.session_state.messages:
    avatar = "✨" if message["role"] == "assistant" else "🙋"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# ---------------------------------------------------------------------
# Empty state — welcome message + suggested prompt chips
# ---------------------------------------------------------------------
# Whether typed or clicked, the prompt ends up in this one variable so both
# paths are handled by the exact same code below.
prompt = None

if not st.session_state.messages:
    st.markdown(f'<div class="capstone-welcome">👋 {WELCOME_MESSAGE}</div>', unsafe_allow_html=True)
    st.caption("Try one of these to get started:")
    with st.container(key="chips"):
        columns = st.columns(2)
        for i, suggestion in enumerate(SUGGESTED_PROMPTS):
            # Alternate chips between the two columns to form a grid
            if columns[i % 2].button(suggestion, key=f"chip_{i}", width="stretch"):
                prompt = suggestion

# ---------------------------------------------------------------------
# Chat input — pinned to the bottom of the screen
# ---------------------------------------------------------------------
typed = st.chat_input(f"Ask {APP_NAME} anything...")
if typed:
    prompt = typed

# ---------------------------------------------------------------------
# Handle a new message (from the input box OR a suggested-prompt chip)
# ---------------------------------------------------------------------
# On the shared public app, stop here (kindly) if today's messages are
# used up — every AI reply costs real money. Local installs have no limit.
if prompt and chat_store.IS_HOSTED:
    if chat_store.messages_sent_today(USER_ID) >= chat_store.DAILY_MESSAGE_LIMIT:
        st.warning(
            f"🌙 You've used all {chat_store.DAILY_MESSAGE_LIMIT} of today's "
            f"messages — {APP_NAME} will be recharged and ready tomorrow!"
        )
        prompt = None

if prompt:
    # A fresh chat gets saved to the database on its first message,
    # with that message (shortened) as its title in the side panel
    if st.session_state.active_id is None:
        title = prompt[:40] + ("…" if len(prompt) > 40 else "")
        st.session_state.active_id = chat_store.create_chat(USER_ID, title)

    # Show the user's message straight away
    with st.chat_message("user", avatar="🙋"):
        st.markdown(prompt)

    # Ask the AI, showing a "thinking" indicator while we wait.
    # We pass the FULL history — trimming happens inside ai_backend.py.
    # ask_ai() is student-written code, so we catch errors HERE (a missing
    # API key, a typo, a network hiccup) rather than showing a scary
    # traceback on screen during a live demo.
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner(f"{APP_NAME} is thinking..."):
            try:
                reply = ask_ai(prompt, st.session_state.messages)
            except Exception as e:
                print(f"[{APP_NAME} error] {e}", flush=True)  # visible in the terminal
                reply = (
                    f"Oops, {APP_NAME} hit a snag — check the terminal for "
                    "details, then try again."
                )
        st.markdown(reply)

    # Add both messages to the working copy, then save the whole chat to
    # the database so it survives refreshes and restarts
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": reply})
    chat_store.save_messages(st.session_state.active_id, st.session_state.messages)
    chat_store.record_message(USER_ID)  # counts toward the daily limit

    # Redraw the page cleanly (updates the side panel title, removes chips)
    st.rerun()
