import json
import time
import uuid
from collections.abc import Generator
from typing import Any

import streamlit as st
from loguru import logger

from frontend.api import APIClient
from frontend.components import *
from frontend.datatypes import MessagePair, StreamEvent
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
            _show_error_popup("Não foi possível criar a thread. Por favor, inicie uma nova conversa.")
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
            _show_error_popup("Não foi possível enviar o feedback.")

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
                    on_click=_toggle_flag,
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

        # Initialize chat history state
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

                if message_pair.assistant_message:
                    label, state = "Concluído!", "complete"
                else:
                    label, state = "Erro", "error"

                with st.status(label=label, state=state) as status:
                    for event in message_pair.safe_events:
                        _display_tool_event(event)

                if message_pair.assistant_message:
                    st.write(message_pair.assistant_message)
                else:
                    st.error(message_pair.error_message)

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

            # Create thread only in the first message
            if (
                self.thread_id is None and not
                self._create_thread_and_register(title=user_prompt)
            ):
                _clear_new_chat_page()
                return

            # Display assistant response in chat message container
            with st.chat_message("assistant", avatar=AVATARS["assistant"]):
                events = []
                assistant_message = None
                error_message = None

                with st.status("Consultando a Base dos Dados...") as status:
                    for event in self.api.send_message(
                        access_token=st.session_state["access_token"],
                        message=user_prompt,
                        thread_id=self.thread_id
                    ):
                        events.append(event)
                        if event.type == "final_answer":
                            assistant_message = event.data.content
                            label, state = "Concluído!", "complete"
                        elif event.type == "error":
                            error_message = event.data.error_details.get("message", "Erro")
                            label, state = "Erro", "error"
                        elif event.type == "complete":
                            message_pair = MessagePair(
                                id=event.data.run_id,
                                user_message=user_prompt,
                                assistant_message=assistant_message,
                                error_message=error_message,
                                events=events
                            )
                            status.update(label=label, state=state)
                        else:
                            _display_tool_event(event)

                if message_pair.assistant_message:
                    st.write_stream(message_pair.stream_words)
                else:
                    st.error(message_pair.error_message)

                # Render buttons immediately to ensure a complete UI before the reload.
                # NOTE: These specific buttons are discarded on the st.rerun() below,
                # and then re-rendered from the chat history on the next pass.
                self._render_message_buttons(message_pair)

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
                _clear_new_chat_page()

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
def _show_error_popup(message: str):
    """Display an error message in a modal.

    Args:
        message (str): The error message.
    """
    st.text(message)


def _clear_new_chat_page():
    """Clear new chat page on session state."""
    st.session_state[NEW_CHAT] = None


def _toggle_flag(flag_id: str):
    """Toggle a flag on session state.

    Args:
        flag_id (str): The flag unique identifier.
    """
    st.session_state[flag_id] = not st.session_state[flag_id]


def _stream_words(message: str) -> Generator[str]:
    """Stream words from a message with a typing effect.

    Args:
        message (str): The message to stream.

    Yields:
        Generator[str]: The next word followed by a space.
    """
    for word in message.split(" "):
        yield word + " "
        time.sleep(0.02)


def _display_code_block(code_block: str, max_lines: int=10, max_height: int=256):
    """Display a code block in Streamlit with adaptive height.

    If the code block has more lines than `max_lines`, the display height
    is capped at `max_height`. Otherwise, the height is set to "content",
    letting Streamlit adjust dynamically.

    Args:
        code_block (str): The code content to display.
        max_lines (int, optional): Threshold for the maximum number of lines
            before capping the height. Defaults to 10.
        max_height (int, optional): Maximum height in pixels for code blocks
            exceeding `max_lines`. Defaults to 256.
    """
    n_lines = code_block.count("\n") + 1

    if n_lines > max_lines:
        height = max_height
    else:
        height = "content"

    st.code(code_block, height=height)


def _format_tool_args(args: dict[str, Any]) -> str:
    """Format tool call arguments for display.

    Expands sql queries arguments into multiline blocks for readability.
    Otherwise pretty-prints the arguments as JSON.

    Args:
        args (dict[str, Any]): Tool call arguments.

    Returns:
        str: A JSON-like string representation of the arguments.
    """
    sql_query = args.get("sql_query")

    if sql_query is None:
        return json.dumps(args, indent=2, ensure_ascii=False)

    sql_block = f'  "sql_query": `\n{sql_query}\n`'

    return "{\n" + sql_block + "\n}"


def _format_tool_outputs(results: str) -> str:
    """Pretty-print tool call outputs.

    Args:
        results (str): Tool call results as a JSON string.

    Returns:
        str: Formatted JSON string.
    """
    return json.dumps(
        json.loads(results),
        ensure_ascii=False,
        indent=2
    )


def _display_tool_event(event: StreamEvent):
    """Render a tool-related event in the Streamlit UI.

    Displays messages, tool call arguments, and tool outputs
    with appropriate formatting and code block sizing.

    Args:
        event (StreamEvent): The tool event to display.
    """
    if event.type == "tool_call":
        if event.data.content:
            st.markdown(event.data.content)
        for tool_call in event.data.tool_calls:
            st.markdown(f"**Executando ferramenta** `{tool_call.name}`")
            tool_args = _format_tool_args(tool_call.args)
            _display_code_block(f"Solicitação:\n{tool_args}")
    elif event.type == "tool_output":
        for tool_output in event.data.tool_outputs:
            if tool_output.status == "error":
                st.markdown(f"Erro na execução da ferramenta `{tool_output.tool_name}`")
            else:
                tool_outputs = _format_tool_outputs(tool_output.output)
                _display_code_block(f"Resposta:\n{tool_outputs}")
