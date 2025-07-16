import time
from functools import cache
from pathlib import Path

import streamlit as st
from loguru import logger

from frontend.api import APIClient
from frontend.components.chat_page import ChatPage
from frontend.utils.constants import *
from frontend.utils.icons import AVATARS


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

st.set_page_config(
    page_title="Chatbot BD",
    page_icon=AVATARS["assistant"]
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

    st.subheader("Bem Vindo(a)! :wave:")
    st.write(f"Bem vindo(a) ao chatbot da BD! Ele vai te ajudar a conversar com seus dados! Basta entrar na página de chat no menu à esquerda e começar a conversa. Faça perguntas sobre os dados disponíveis e o chatbot dará o seu melhor para respondê-las!", unsafe_allow_html=True)

    st.write("\n")

    # Available models
    st.subheader("Modelo :brain:")
    st.write("O modelo por trás do chatbot é o Gemini, do Google.")

    st.write("\n")

    # Available features
    st.subheader("Funcionalidades :memo:")
    st.write("""
            - **Botão de Reset (:blue[:material/refresh:]):** clique no botão de reset para reiniciar a conversa com o chatbot, limpando a sua memória e o histórico de conversa, sem precisar sair da aplicação.
            - **Botão de Download (:blue[:material/download:]):** clique no botão de download para exportar a **conversa** para um arquivo CSV. Apenas a **conversa** é exportada, e não os dados/tabelas disponíveis.
            - **Botão de Gráfico (:blue[:material/bar_chart:]):** clique no botão de gráfico para exibir ou ocultar o gráfico gerado pelo chatbot. Ele pode gerar gráficos de barras verticais e horizontais, linhas, setores e de dispersão.
            - **Botão de Código (:blue[:material/code:]):** clique no botão de código para exibir ou ocultar como o chatbot está fazendo as consultas nas bases de dados. O chatbot faz consultas em bases de dados armazenadas na nuvem usando linguagem SQL.
            - **Botões de Feedback (:blue[:material/thumb_up:] ou :blue[:material/thumb_down:]):** clique nos botões de feedback para enviar feedbacks sobre as respostas recebidas, com comentários opcionais. É necessário clicar no botão de envio (:material/send:) para que o feedback seja enviado.""")

    st.write("\n")

    # Prompting guide
    st.subheader("Guia de Prompt :clipboard:")
    st.write("A forma como você conversa com o chatbot pode influenciar na qualidade das respostas! Por isso, abaixo estão listadas algumas dicas para te ajudar a elaborar suas perguntas. Elas podem ser úteis caso as respostas fornecidas estejam incorretas ou não sejam boas o suficiente!")
    st.write("""
            1. Tente fazer uma pergunta por vez. Caso sua pergunta seja muito complexa, ou talvez seja um conjunto de várias perguntas, tente separá-la em perguntas menores e mais simples.
            2. Tente utilizar termos como "**por**" ou "**total**" quando precisar de informações agregadas segundo alguma variável.
            3. Caso saiba os nomes das colunas das tabelas, tente mencioná-los nas suas perguntas. Por exemplo, se você sabe que uma tabela possui a coluna "**município**", tente usar a palavra **município** ao invés de "cidade". Isso não significa que você não possa usar palavras parecidas, mas usar os nomes das colunas ajuda o chatbot.
            4. Caso o chatbot não esteja encontrando uma resposta para a sua pergunta e você saiba em qual tabela estão os dados necessários para respondê-la, você pode tentar pedir explicitamente ao chatbot para procurar nessa tabela específica.""")

    st.write("\n")

    # Important information
    st.subheader(":gray[:material/info:] Importante")
    st.write("""
            - Quando enviar uma pergunta ao chatbot, espere até que uma resposta seja fornecida antes de trocar de página ou clicar em qualquer botão dentro da aplicação. Você pode alternar entre as abas do seu navegador normalmente.
            - Após sair da aplicação ou fechá-la, o histórico de conversa e a memória do chatbot serão deletados.""")

login_page = st.Page(page=login, title="Entrar", icon=":material/login:")

if st.session_state.get("logged_in"):
    about_page = st.Page(page=about, title="Conheça o App", icon=":material/lightbulb_2:")
    logout_page = st.Page(page=logout, title="Sair", icon=":material/logout:")

    new_chat_page = st.Page(
        page=ChatPage(api).render,
        title="Nova conversa",
        icon=":material/add:",
        url_path="chat",
        default=True
    )

    chat_pages: list[ChatPage] = st.session_state.get("chat_pages", [])

    user_chat_pages = [
        st.Page(
            page=chat_page.render,
            title=chat_page.title,
            url_path=f"{chat_page.thread_id}"
        ) for chat_page in reversed(chat_pages)
    ]

    sections = {
        "Sobre": [about_page],
        "Sua conta": [logout_page],
        "Suas conversas": [new_chat_page] + user_chat_pages,
    }

    page = st.navigation(sections)
else:
    page = st.navigation(pages=[login_page], position="hidden")

page.run()
