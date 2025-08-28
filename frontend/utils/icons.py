from importlib.resources import files

import streamlit as st

import frontend

_assistant_avatar = str(
    files(frontend)
    .joinpath("images")
    .joinpath("logo_bd.svg")
)

if email := st.session_state.get("email"):
    _user_avatar = f"https://api.dicebear.com/9.x/initials/svg?seed={email.split('@')[0]}&backgroundColor=7ec876&radius=50"
else:
    _user_avatar = "https://api.dicebear.com/9.x/avataaars-neutral/svg?backgroundColor=7ec876&eyebrows=default&eyes=default&mouth=twinkle"

AVATARS = {
    "user": _user_avatar,
    "assistant": _assistant_avatar
}
