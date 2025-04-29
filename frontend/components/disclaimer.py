import streamlit as st
from streamlit_extras.bottom_container import bottom


def render_disclaimer():
    with bottom():
        _, center, _ = st.columns((1, 6, 1))

        center.markdown(
            """
                <style>
                    .disclaimer {
                        text-align: center;
                        font-size: 14px;
                        color: #9c9d9f;
                    }
                </style>
                <div class="disclaimer">
                    O assistente pode cometer erros. Considere verificar informações importantes.<br/>
                    Todas as informações aqui enviadas são registradas para análise e melhoria do produto.
                </div>
            """,
            unsafe_allow_html=True
        )
