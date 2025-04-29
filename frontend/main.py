import time

import streamlit as st

from frontend.api import APIClient
from frontend.loguru_logging import get_logger
from frontend.utils import BASE_URL

api = APIClient(BASE_URL)
logger = get_logger()

def login():
    st.title("Entrar")
    st.caption("Por favor, insira seu usuário e senha para continuar")

    access_token = None
    message = None

    with st.form("register_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")

        col1, col2, _ = st.columns([1.1, 1.5, 6.86])

        if col1.form_submit_button("Entrar", type="primary"):
            access_token, message = api.authenticate(username, password)

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
