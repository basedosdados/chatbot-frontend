import time
from functools import cache
from pathlib import Path

import streamlit as st
from loguru import logger

from frontend.api import APIClient
from frontend.utils.constants import *


@cache
def _setup_logger():
    # Create log directory
    log_path = Path(LOG_FILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove default handler
    logger.remove()

    # Formatting function
    def _format(record):
        if "classname" in record["extra"]:
            keyname = record["extra"]["classname"]
        else:
            keyname = record["name"]

        return (
            "<g>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | "
            "<lvl>{level:<8}</> | "
            "<c>%s:{function}:{line}</> - {message}\n{exception}" % keyname
        )

    # Add handler to logger
    logger.add(
        sink=LOG_FILE_PATH,
        level=LOG_LEVEL,
        format=_format,
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        backtrace=LOG_BACKTRACE,
        diagnose=LOG_DIAGNOSE,
        enqueue=LOG_ENQUEUE
    )

_setup_logger()

def login():
    api = APIClient(BASE_URL)

    st.title("Entrar")
    st.caption("Por favor, insira seu email e senha para continuar")

    access_token = None
    message = None

    with st.form("register_form"):
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")

        col1, col2, _ = st.columns([1.1, 1.5, 6.86])

        if col1.form_submit_button("Entrar", type="primary"):
            access_token, message = api.authenticate(email, password)

    if access_token is not None:
        st.session_state["logged_in"] = True
        st.session_state["access_token"] = access_token
        st.success(message, icon=":material/check:")
        time.sleep(0.5)
        st.rerun()
    elif message is not None:
        st.error(message, icon=":material/error:")

def logout():
    st.title("Sair")
    st.caption("Todas as conversas serão reiniciadas")
    st.markdown("")

    if st.button("Sair"):
        for key in st.session_state:
            del st.session_state[key]
        st.success("Desconectado com sucesso!", icon=":material/check:")
        time.sleep(0.5)
        st.rerun()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

login_page = st.Page(page=login, title="Entrar", icon=":material/login:")
logout_page = st.Page(page=logout, title="Sair", icon=":material/logout:")

home = st.Page(page="pages/home.py", title="Início", icon=":material/home:", default=True)
chat = st.Page(page="pages/chat.py", title="Chat", icon=":material/chat:")

if st.session_state["logged_in"]:
    pg = st.navigation([home, chat, logout_page])
else:
    pg = st.navigation([login_page])

pg.run()
