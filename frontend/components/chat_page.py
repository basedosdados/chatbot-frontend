import uuid

import streamlit as st
from loguru import logger

from frontend.api import APIClient
from frontend.components import *
from frontend.datatypes import MessagePair, Step
from frontend.utils.constants import NEW_CHAT
from frontend.utils.icons import AVATARS


class ChatPage:
    chat_history_key = "chat_history"
    delete_btn_key = "delete_btn"
    feedbacks_key = "feedbacks"
    waiting_key = "waiting_for_answer"

    def __init__(self, api: APIClient, title: str | None = None, thread_id: str | None = None):
        self.api = api
        self.title = title
        self.thread_id = thread_id
        self.page_id = str(uuid.uuid4())
        self.logger = logger.bind(classname=self.__class__.__name__)

    def _create_thread_and_register(self, title: str) -> bool:
        """Create a thread for this chat page and add itself to the chat pages list.

        Args:
            title (str): The thread title.

        Returns:
            bool: Whether the thread creation was successful.
        """
        thread = self.api.create_thread(
            access_token=st.session_state["access_token"],
            title=title,
        )

        if thread is not None:
            self.title = thread.title
            self.thread_id = thread.id
            chat_pages: list[ChatPage] = st.session_state["chat_pages"]
            chat_pages.append(self)
            return True
        else:
            show_error_popup("Não foi possível criar a thread. Por favor, inicie uma nova conversa.")
            return False

    def _handle_click_feedback(self, feedback_id: str, show_comments_id: str):
        """Update the feedback buttons state and the comments text input flag on session state.

        Args:
            feedback_id (str): The feedback button identifier.
            show_comments_id (str): The comments text input flag identifier.
        """
        feedback = st.session_state[feedback_id]

        page_feedbacks = st.session_state[self.page_id][self.feedbacks_key]

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
        message_pair_id: uuid.UUID,
        show_comments_id: str,
        comments: str | None
    ):
        """Handle feedback sending.

        Args:
            feedback_id (str): The feedback id.
            message_pair_id (UUID): The message pair id.
            show_comments_id (str): The show_comments flag id.
            comments (str | None): The comments.
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

    def _render_message_buttons(self, message_pair: MessagePair):
        """Render the code-showing button and all the feedback related widgets on assistant's messages.

        Args:
            message_pair (MessagePair):
                A MessagePair object containing:
                    - id: unique identifier.
                    - user_message: user message.
                    - assistant_message: assistant message.
                    - error_message: error message.
                    - generated_queries: generated sql queries.
        """
        # Placeholder for showing the generated SQL queries
        code_placeholder = st.empty()

        # Container for feedback widgets
        feedback_container = st.container()

        # Creates four columns:
        # the first one is for the code-showing button
        # the second one is for the feedback buttons
        # the third one is for the comments input
        # the fourth one is for the feedback sending button
        col1, col2, col3, col4 = feedback_container.columns(
            (0.06, 0.12, 0.93, 0.1),
            vertical_alignment="center"
        )

        # Checks if the model is still answering the last question.
        # If yes, all message buttons and comments inputs will be disabled
        waiting_for_answer = st.session_state[self.page_id][self.waiting_key]

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

        # By default, the comments input should be hidden
        if show_comments_id not in st.session_state:
            st.session_state[show_comments_id] = False

        # Look for the feedback buttons widget in the session state
        page_feedbacks = st.session_state[self.page_id][self.feedbacks_key]

        # And keep its state if it already existed in the session
        if feedback_id in page_feedbacks:
            last_feedback = page_feedbacks[feedback_id]
            st.session_state[feedback_id] = last_feedback

        # Renders the code-showing button
        with col1:
            with code_button_container():
                st.button(
                    " ",
                    key=show_code_btn_id,
                    on_click=toggle_flag,
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

    def _render_delete_button(self):
        """Render the chat deletion button."""
        @st.dialog("Excluir conversa")
        def show_delete_chat_modal():
            st.markdown("") # just for spacing
            st.text("Tem certeza que deseja excluir esta conversa permanentemente?")

            col1, col2, _ = st.columns([1.1, 2.1, 2])

            if col1.button("Cancelar"):
                st.rerun()

            if col2.button("Sim, excluir", type="primary"):
                deleted = self.api.delete_thread(
                    access_token=st.session_state["access_token"],
                    thread_id=self.thread_id
                )

                if not deleted:
                    st.error("Não foi possível excluir a conversa.", icon=":material/error:")
                    return

                chat_pages: list[ChatPage] = st.session_state["chat_pages"]
                for i, chat_page in enumerate(chat_pages):
                    if chat_page.thread_id == self.thread_id:
                        chat_pages.pop(i)
                        break

                st.rerun()

        page_session_state = st.session_state[self.page_id]
        chat_delete_disabled = page_session_state[self.delete_btn_key]

        if chat_delete_disabled:
            return

        st.button(
            label="Excluir",
            icon=":material/delete:",
            on_click=show_delete_chat_modal,
        )

    def _handle_user_interaction(self):
        """Disable all chat message buttons, comments inputs and the chat input while
        the model is answering a question and enable the chat deletion button rendering.
        """
        st.session_state[self.page_id][self.delete_btn_key] = False
        st.session_state[self.page_id][self.waiting_key] = True

    def render(self):
        """Render the chat page."""
        # Unfortunately, this is necessary for the code-showing button customization
        st.markdown(
            """<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>""",
            unsafe_allow_html=True
        )

        # Placeholder for the subheader message
        subheader = st.empty()

        # Initialize page session state
        if self.page_id not in st.session_state:
            st.session_state[self.page_id] = {}

        page_session_state = st.session_state[self.page_id]

        # Initialize feedback history
        if self.feedbacks_key not in page_session_state:
            page_session_state[self.feedbacks_key] = {}

        # Initialize the waiting key, which is used to prevent users from
        # interacting with the app while the model is answering a question
        if self.waiting_key not in page_session_state:
            page_session_state[self.waiting_key] = False

        # Initialize chat deletion flag
        if self.delete_btn_key not in page_session_state:
            page_session_state[self.delete_btn_key] = self.thread_id is None

        # Initialize chat history state and chat deletion flag state
        if self.chat_history_key not in page_session_state:
            if self.thread_id is not None:
                message_pairs = self.api.get_message_pairs(
                    access_token=st.session_state["access_token"],
                    thread_id=self.thread_id
                )
            else:
                message_pairs = []
            page_session_state[self.chat_history_key] = message_pairs or []

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

                if not message_pair.error_message:
                    label = "Concluído!"
                    state = "complete"
                else:
                    label = "Erro"
                    state = "error"

                with st.status(label=label, state=state) as status:
                    for step in message_pair.safe_steps:
                        st.caption(step.content)

                if not message_pair.error_message:
                    st.write(message_pair.assistant_message)
                    self._render_message_buttons(message_pair)
                else:
                    st.error(message_pair.error_message)

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

            # Create thread only in the first message
            if (
                self.thread_id is None and not
                self._create_thread_and_register(title=user_prompt)
            ):
                clear_new_chat_page()
                return

            # Display assistant response in chat message container
            with st.chat_message("assistant", avatar=AVATARS["assistant"]):
                with st.status("Consultando banco de dados...") as status:
                    for streaming_status, message in self.api.send_message(
                        access_token=st.session_state["access_token"],
                        message=user_prompt,
                        thread_id=self.thread_id
                    ):
                        if streaming_status == "running":
                            step: Step = message
                            status.update(label=step.label)
                            st.caption(step.content)
                        elif streaming_status == "complete":
                            message_pair: MessagePair = message
                            if not message_pair.error_message:
                                label = "Concluído!"
                                state = "complete"
                            else:
                                label = "Erro"
                                state = "error"
                            status.update(label=label, state=state)

                if not message_pair.error_message:
                    # Render the assistant message and message buttons
                    _ = st.write_stream(message_pair.stream_words)
                    self._render_message_buttons(message_pair)
                else:
                    st.error(message_pair.error_message)

            # Add message pair to chat history
            chat_history.append(message_pair)

        # Render the chat deletion button
        self._render_delete_button()

        # Render the disclaimer messages
        render_disclaimer()

        if page_session_state[self.waiting_key]:
            page_session_state[self.waiting_key] = False

            new_chat: ChatPage | None = st.session_state[NEW_CHAT]

            # If this page is a new chat page, switch to it
            if new_chat and new_chat.page_id == self.page_id:
                clear_new_chat_page()

                current_page = st.Page(
                    page=self.render,
                    title=self.title,
                    url_path=str(self.thread_id)
                )

                st.switch_page(current_page)
            # Otherwise, we're already on it, so just rerun
            else:
                st.rerun()

@st.dialog("Erro")
def show_error_popup(message: str):
    """Display an error message in a modal.

    Args:
        message (str): The error message.
    """
    st.text(message)

def clear_new_chat_page():
    """Clear new chat page on session state.
    """
    st.session_state[NEW_CHAT] = None

def toggle_flag(flag_id: str):
    """Toggle a flag on session state.

    Args:
        flag_id (str): The flag identifier.
    """
    st.session_state[flag_id] = not st.session_state[flag_id]
