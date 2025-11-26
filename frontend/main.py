import sys
import time
from functools import cache

import streamlit as st
from loguru import logger

from frontend.api import APIClient
from frontend.components.chat_page import ChatPage
from frontend.utils.constants import (BASE_URL, LOG_BACKTRACE, LOG_DIAGNOSE,
                                      LOG_ENQUEUE, LOG_LEVEL, NEW_CHAT)
from frontend.utils.logos import BD_LOGO


@cache
def _setup_logger():
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
        sink=sys.stdout,
        level=LOG_LEVEL,
        format=_format,
        backtrace=LOG_BACKTRACE,
        diagnose=LOG_DIAGNOSE,
        enqueue=LOG_ENQUEUE
    )

_setup_logger()

st.set_page_config(
    page_title="Chatbot BD",
    page_icon=BD_LOGO
)

api = APIClient(BASE_URL)

def login():
    st.title("Entrar")
    st.caption("Por favor, insira seu e-mail e senha para continuar")

    access_token = None
    message = None

    with st.form("register_form"):
        email = st.text_input("E-mail")
        password = st.text_input("Senha", type="password")

        col1, _ = st.columns(2)

        if col1.form_submit_button("Entrar", type="primary"):
            access_token, message = api.authenticate(email, password)

    if access_token is not None:
        threads = api.get_threads(access_token)

        if threads is not None:
            st.session_state["chat_pages"] = [
                ChatPage(api, title=thread.title, thread_id=str(thread.id))
                for thread in threads
            ]
        else:
            st.session_state["chat_pages"] = []

        st.session_state["email"] = email
        st.session_state["user_avatar"] = f"https://api.dicebear.com/9.x/initials/svg?seed={email[0]}&backgroundColor=7ec876&radius=50"
        st.session_state["logged_in"] = True
        st.session_state["access_token"] = access_token
        st.success(message, icon=":material/check:")
        time.sleep(0.5)
        st.rerun()
    elif message is not None:
        st.error(message, icon=":material/error:")

def logout():
    st.title("Tem certeza que deseja sair?")
    st.caption("Clique no botão abaixo para confirmar")

    if st.button("Sair", type="primary"):
        st.session_state.clear()
        st.success("Desconectado com sucesso!", icon=":material/check:")
        time.sleep(0.5)
        st.rerun()

def about():
    st.title("Chatbot BD")
    st.caption("Para consultas em bases de dados utilizando linguagem natural")

    st.write("\n")

    st.subheader("Bem Vindo(a)! 👋")
    st.write(f"Bem vindo(a) ao chatbot da BD! Ele vai te ajudar a conversar com seus dados! Basta entrar na página de chat no menu à esquerda e começar a conversa. Faça perguntas sobre os dados disponíveis e o chatbot dará o seu melhor para respondê-las!", unsafe_allow_html=True)

    st.write("\n")

    # Available models
    st.subheader("Modelo 🧠")
    st.write("O modelo por trás do chatbot é o Gemini, do Google.")

    st.write("\n")

    # Available features
    st.subheader("Funcionalidades 🛠️")
    st.write("""
        - **Feedback (:material/thumb_up: ou :material/thumb_down:):** Clique nos botões de feedback para avaliar as respostas, com comentários opcionais.
        - **Excluir Conversa (:material/delete:):** Clique no botão de excluir conversa para excluir a conversa com o chatbot. As mensagens permanecerão salvas em nosso banco de dados para análise e melhoria do produto."""
    )
    st.write("\n")

    # Prompting guide
    st.subheader("Guia de Prompt 📋")
    st.write("A forma como você conversa com o chatbot pode influenciar na qualidade das respostas! Por isso, abaixo estão listadas algumas dicas para te ajudar a elaborar suas perguntas. Elas podem ser úteis caso as respostas fornecidas estejam incorretas ou não sejam boas o suficiente!")
    st.write("""
        1. Tente fazer uma pergunta por vez. Caso sua pergunta seja muito complexa, ou talvez seja um conjunto de várias perguntas, tente separá-la em perguntas menores e mais simples.
        2. Tente utilizar termos como "**por**" ou "**total**" quando precisar de informações agregadas segundo alguma variável.
        3. Caso saiba os nomes das colunas das tabelas, tente mencioná-los nas suas perguntas. Por exemplo, se você sabe que uma tabela possui a coluna "**município**", tente usar a palavra **município** ao invés de "cidade". Isso não significa que você não possa usar palavras parecidas, mas usar os nomes das colunas ajuda!
        4. Caso o chatbot não esteja encontrando uma resposta para a sua pergunta e você saiba em qual tabela estão os dados necessários para respondê-la, você pode tentar pedir explicitamente para procurar nessa tabela específica."""
    )
    st.write("\n")

    # Important information
    st.subheader("Importante 📌")
    st.info("⏳ Depois de enviar uma pergunta ao chatbot, aguarde a resposta completa antes de trocar de página ou clicar em botões. Você pode alternar entre abas do navegador normalmente.")

if st.session_state.get("logged_in"):
    about_page = st.Page(page=about, title="Conheça o App", icon=":material/lightbulb_2:")
    logout_page = st.Page(page=logout, title="Sair", icon=":material/logout:")

    if not st.session_state.get(NEW_CHAT):
        new_chat = ChatPage(api)
        st.session_state[NEW_CHAT] = new_chat
    else:
        new_chat = st.session_state[NEW_CHAT]

    new_chat_page = st.Page(
        page=new_chat.render, title="Nova conversa", icon=":material/add:", default=True
    )

    chat_pages: list[ChatPage] = st.session_state.get("chat_pages", [])

    user_chat_pages = [
        st.Page(
            page=chat_page.render,
            title=chat_page.title,
            url_path=str(chat_page.thread_id)
        ) for chat_page in reversed(chat_pages)
    ]

    sections = {
        "Sobre": [about_page],
        "Sua conta": [logout_page],
        "Suas conversas": [new_chat_page] + user_chat_pages,
    }

    page = st.navigation(sections)
else:
    login_page = st.Page(page=login, title="Entrar", icon=":material/login:")
    page = st.navigation(pages=[login_page], position="hidden")

page.run()
