from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from frontend.api import APIClient
from frontend.components import *
from frontend.datatypes import MessagePair
from frontend.loguru_logging import get_logger
from frontend.utils.icons import AVATARS


class ChatPage:
    chat_history_key = "chat_history"
    chat_buttons_key = "chat_buttons"
    feedbacks_key = "feedbacks"
    waiting_key = "waiting_for_answer"

    example_prompts = [
        {"icon": "auto_stories", "text": "Qual foi a porcentagem de alunos leitores por raça/cor nas avaliações de saída de 2023?"},
        {"icon": "auto_stories", "text": "Qual foi o ideb médio em 2023 nos municípios onde temos EpV para os anos iniciais?"},
        {"icon": "school", "text": "Qual a porcentagem de egressos que ocupam posições de autoridade formal, por organização?"},
    ]

    def __init__(self, api: APIClient, title: str):
        self.api = api
        self.title = title
        self.page_name = title.lower()
        self.logger = get_logger(self.__class__.__name__)

        st.set_page_config(
            page_title=self.title,
            page_icon=AVATARS["assistant"]
        )

    def _handle_click_feedback(self, feedback_id: str, show_comments_id: str):
        """Update the feedback buttons state and the comments text input flag on session state

        Args:
            feedback_id (str): The feedback button identifier
            show_comments_id (str): The comments text input flag identifier
        """
        feedback = st.session_state[feedback_id]

        page_feedbacks = st.session_state[self.page_name][self.feedbacks_key]

        # The _handle_click_feedback method is being called sometimes when changing
        # pages and then coming back, so some guard clauses had to be used
        # to avoid empty or duplicated feedbacks sending

        # First, we must check if the feedback is None
        if feedback is None:
            return

        # Then, we must check if the feedback is the same as the last sent feedback
        if feedback_id in page_feedbacks and page_feedbacks[feedback_id] == feedback:
            return

        # Finally, we update it on the session state
        page_feedbacks[feedback_id] = feedback

        # And show the comments text input
        st.session_state[show_comments_id] = True

    def _handle_send_feedback(
        self,
        feedback_id: str,
        message_pair_id: str,
        show_comments_id: str,
        comments: str
    ):
        """Handle feedback sending

        Args:
            feedback_id (str): The feedback id
            message_pair_id (str): The message pair id
            show_comments_id (str): The show_comments flag id
            comments (str): The comments
        """
        rating = st.session_state[feedback_id]
        access_token = st.session_state["access_token"]

        if not self.api.send_feedback(
            access_token=access_token,
            message_pair_id=message_pair_id,
            rating=rating,
            comments=comments
        ):
            show_error_popup("Não foi possível enviar o feedback.")

        st.session_state[show_comments_id] = False

    @staticmethod
    def _plot_chart(placeholder: DeltaGenerator, message_pair: MessagePair):
        data = pd.DataFrame(message_pair.chart_data.data)
        data = data.fillna("N/A")

        metadata = message_pair.chart_metadata

        human_friendly_labels = {
            metadata.x_axis: metadata.x_axis_title,
            metadata.y_axis: metadata.y_axis_title,
        }

        if metadata.valid_label is not None:
            human_friendly_labels[metadata.valid_label] = metadata.label_title

        kwargs = {
            "x": metadata.x_axis,
            "y": metadata.y_axis,
            "color": metadata.valid_label,
            "labels": human_friendly_labels,
            "title": metadata.title
        }

        match metadata.chart_type:
            case "bar":
                fig = px.bar(data, **kwargs)
            case "horizontal_bar":
                fig = px.bar(data, orientation="h", **kwargs)
            case "line":
                fig = px.line(data, markers=True, **kwargs)
            case "pie":
                kwargs["names"] = kwargs.pop("x")
                kwargs["values"] = kwargs.pop("y")
                fig = px.pie(data, hole=0.5, **kwargs)
            case "scatter":
                fig = px.scatter(data, **kwargs)
            case _:
                raise NotImplementedError(f"{metadata.chart_type} chart is not implemented")

        fig.update_layout(margin={"b": 0})

        placeholder.plotly_chart(fig)

    def _toggle_flag(self, flag_id: str):
        """Toggle a flag on session state

        Args:
            flag_id (str): The flag identifier
        """
        st.session_state[flag_id] = not st.session_state[flag_id]

    def _render_message_buttons(self, message_pair: MessagePair):
        """Render the code-showing button and all the feedback related widgets on assistant's messages

        Args:
            message_pair (MessagePair):
                A MessagePair object containing:
                    - id: unique identifier
                    - thread_id: thread unique identifier
                    - model_uri: uri for the assistant's model
                    - user_message: user message
                    - assistant_message: assistant message
                    - generated_queries: generated sql queries
                    - generated_chart: generated data for visualization
                    - created_at: message pair creation timestamp
        """
        # Placeholder for showing the generated chart
        chart_placeholder = st.empty()

        # Placeholder for showing the generated SQL queries
        code_placeholder = st.empty()

        # Container for feedback widgets
        feedback_container = st.container()

        # Creates four columns:
        # the first one is for the code-showing button
        # the second one is for the feedback buttons
        # the third one is for the comments input
        # the fourth one is for the feedback sending button
        col0, col1, col2, col3, col4 = feedback_container.columns(
            (0.06, 0.06, 0.12, 0.86, 0.1),
            vertical_alignment="center"
        )

        # Checks if the model is still answering the last question.
        # If yes, all message buttons and comments inputs will be disabled
        waiting_for_answer = st.session_state[self.page_name][self.waiting_key]

        # Unique flag and button key for chart-showing
        show_chart_id = f"show_chart_{message_pair.id}"
        show_chart_btn_id = f"show_chart_btn_{message_pair.id}"

        # Unique flag and button key for code-showing
        show_code_id = f"show_code_{message_pair.id}"
        show_code_btn_id = f"show_code_btn_{message_pair.id}"

        # Unique identifiers for the feedback buttons widget
        # and for a flag that determines if the comments input should be shown
        feedback_id = f"feedback_{message_pair.id}"
        comments_input_id = f"comments_input_{message_pair.id}"
        show_comments_id = f"show_comments_{message_pair.id}"
        send_comments_id = f"send_comments_{message_pair.id}"

        # By default, the codes should be hidden
        if show_code_id not in st.session_state:
            st.session_state[show_code_id] = False

        # By default, the charts should be displayed if any are available
        if show_chart_id not in st.session_state:
            st.session_state[show_chart_id] = message_pair.has_valid_chart

        # By default, the comments input should be hidden
        if show_comments_id not in st.session_state:
            st.session_state[show_comments_id] = False

        # Look for the feedback buttons widget in the session state
        page_feedbacks = st.session_state[self.page_name][self.feedbacks_key]

        # And keep its state if it already existed in the session
        if feedback_id in page_feedbacks:
            last_feedback = page_feedbacks[feedback_id]
            st.session_state[feedback_id] = last_feedback

        # Renders the chart-showing button
        with col0:
            with chart_button_container():
                st.button(
                    " ",
                    key=show_chart_btn_id,
                    on_click=self._toggle_flag,
                    args=(show_chart_id,),
                    disabled=waiting_for_answer
                )

        # If the chart-showing flag is set, shows the generated chart
        if st.session_state[show_chart_id]:
            if message_pair.has_valid_chart:
                try:
                    self._plot_chart(chart_placeholder, message_pair)
                except Exception:
                    self.logger.exception(f"Error on plotting chart for message pair {message_pair.id}:")
                    chart_placeholder.error("Ops! Algo deu errado na exibição do gráfico.")
            elif message_pair.has_chart:
                chart_placeholder.error("Ops! Ocorreu um erro na criação do gráfico.")
            else:
                chart_placeholder.info("Nenhum gráfico foi gerado.")

        # Renders the code-showing button
        with col1:
            with code_button_container():
                st.button(
                    " ",
                    key=show_code_btn_id,
                    on_click=self._toggle_flag,
                    args=(show_code_id,),
                    disabled=waiting_for_answer
                )

        # If the code-showing flag is set, shows the generated sql queries
        if st.session_state[show_code_id]:
            if message_pair.generated_queries is not None:
                code_placeholder.write(message_pair.formatted_sql_queries)
            else:
                code_placeholder.info("Nenhuma consulta SQL foi gerada.")

        # Renders the feedback buttons
        col2.feedback(
            "thumbs",
            key=feedback_id,
            on_change=self._handle_click_feedback,
            args=(feedback_id, show_comments_id),
            disabled=waiting_for_answer
        )

        # If the flag is set, shows the comments input and the sending button
        if st.session_state[show_comments_id]:
            comments = col3.text_input(
                "comments",
                key=comments_input_id,
                value=None,
                placeholder="Comentários adicionais (opcional)",
                label_visibility="collapsed",
                disabled=waiting_for_answer
            )

            # If the sending button is pressed, sends the feedback and comments
            # to the backend and hides the comments input and the sending button
            col4.button(
                ":material/send:",
                key=send_comments_id,
                on_click=self._handle_send_feedback,
                args=(
                    feedback_id,
                    message_pair.id,
                    show_comments_id,
                    comments
                ),
                disabled=waiting_for_answer
            )

    def _chat_to_csv(self) -> bytes:
        """Create a csv file containing the chat history questions and answers

        Returns:
            bytes: The utf-8 encoded csv file
        """
        page_session_state = st.session_state[self.page_name]
        chat_history: list[MessagePair] = page_session_state[self.chat_history_key]

        models = []
        user_messages = []
        assistant_messages = []
        generated_queries = []

        for message_pair in chat_history:
            models.append(message_pair.model_uri)
            user_messages.append(message_pair.user_message)
            assistant_messages.append(message_pair.assistant_message)

            if message_pair.generated_queries is not None:
                queries = "\n\n".join(message_pair.generated_queries)
            else:
                queries = None

            generated_queries.append(queries)

        return pd.DataFrame({
            "modelo": models,
            "pergunta": user_messages,
            "resposta": assistant_messages,
            "consulta": generated_queries,
        }).to_csv(index=False).encode("utf-8")

    def _reset_page(self):
        """Reset the page session state and delete everything related to its
        chat history from the app session state. Also clears the assistant memory
        """
        page_session_state = st.session_state[self.page_name]

        _ = self.api.clear_thread(
            access_token=st.session_state["access_token"],
            thread_id=page_session_state["thread_id"]
        )

        chat_history: list[MessagePair] = page_session_state[self.chat_history_key]

        for message_pair in chat_history:
            for k, v in st.session_state.items():
                if message_pair.id in k:
                    del st.session_state[k]

        del st.session_state[self.page_name]

    def _handle_user_interaction(self):
        """Disable all chat message buttons, comments inputs and the chat input while the model
        is answering a question and enable the chat reset and download buttons rendering
        """
        st.session_state[self.page_name][self.chat_buttons_key] = False
        st.session_state[self.page_name][self.waiting_key] = True

    def _render_chat_buttons(self):
        """Render the chat reset and download buttons"""
        page_session_state = st.session_state[self.page_name]
        chat_reset_disabled = page_session_state[self.chat_buttons_key]

        if chat_reset_disabled:
            return

        container = st.container()

        col1, col2, _ = container.columns((1, 1, 13))

        col1.button(
            ":material/refresh:",
            on_click=self._reset_page,
        )

        col2.download_button(
            ":material/download:",
            data=self._chat_to_csv(),
            file_name=f"{self.page_name.replace(' ', '_')}_{datetime.now().strftime('%F_%T')}.csv"
        )

    def render(self):
        """Render the chat page"""
        # Show three example prompts
        columns = st.columns(3)
        for col, example in zip(columns, self.example_prompts):
            with col:
                render_card(
                    icon=example["icon"],
                    text=example["text"],
                )

        # Unfortunately, this is necessary for the code-showing button customization
        st.markdown(
            """<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>""",
            unsafe_allow_html=True
        )

        # Placeholder for the subheader message
        subheader = st.empty()

        # Initialize page session state
        if self.page_name not in st.session_state:
            st.session_state[self.page_name] = {}

        page_session_state = st.session_state[self.page_name]

        # Get thread id
        if "thread_id" not in page_session_state:
            thread_id = self.api.create_thread(
                access_token=st.session_state["access_token"]
            )
            if thread_id is not None:
                page_session_state["thread_id"] = thread_id
            else:
                show_error_popup("Não foi possível criar a thread.")

        # Initialize the waiting key, which is used to prevent users from
        # interacting with the app while the model is answering a question
        if self.waiting_key not in page_session_state:
            page_session_state[self.waiting_key] = False

        # Initialize chat history state
        if self.chat_history_key not in page_session_state:
            page_session_state[self.chat_history_key] = []

        # Initialize feedback history
        if self.feedbacks_key not in page_session_state:
            page_session_state[self.feedbacks_key] = {}

        # Initialize reset flag state
        if self.chat_buttons_key not in page_session_state:
            page_session_state[self.chat_buttons_key] = True

        chat_history: list[MessagePair] = page_session_state[self.chat_history_key]

        # Display the subheader message only if the chat history is empty
        if not chat_history:
            with subheader:
                typewrite("Como posso ajudar?")

        # Display chat messages from history on app rerun
        for message_pair in chat_history:
            with st.chat_message("user", avatar=AVATARS["user"]):
                st.write(message_pair.user_message)

            with st.chat_message("assistant", avatar=AVATARS["assistant"]):
                st.empty()
                st.write(message_pair.assistant_message)
                self._render_message_buttons(message_pair)

        # Accept user input
        if user_prompt := st.chat_input(
            "Faça uma pergunta!",
            on_submit=self._handle_user_interaction,
            disabled=page_session_state[self.waiting_key]
        ):
            # Clear subheader message
            subheader.empty()

            # Display user message in chat message container
            with st.chat_message("user", avatar=AVATARS["user"]):
                st.write(user_prompt)

            # Display assistant response in chat message container
            with st.chat_message("assistant", avatar=AVATARS["assistant"]):
                three_dots_placeholder = st.empty()

                with three_dots_placeholder:
                    three_pulsing_dots()

                message_pair = self.api.send_message(
                    access_token=st.session_state["access_token"],
                    message=user_prompt,
                    thread_id=page_session_state["thread_id"]
                )

                three_dots_placeholder.empty()

                _ = st.write_stream(message_pair.stream_words)

                # Render the message buttons
                self._render_message_buttons(message_pair)

            # Add message pair to chat history
            chat_history.append(message_pair)

        # Render the chat buttons
        self._render_chat_buttons()

        # Render the disclaimer messages
        render_disclaimer()

        if page_session_state[self.waiting_key]:
            page_session_state[self.waiting_key] = False
            st.rerun()

@st.dialog("Erro")
def show_error_popup(message: str):
    st.text(message)
