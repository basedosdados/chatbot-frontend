import json
import uuid
from typing import Any

import sqlparse
import streamlit as st
from loguru import logger
from streamlit_extras.stylable_container import stylable_container

from frontend.api import APIClient
from frontend.components import *
from frontend.datatypes import MessagePair, StreamEvent
from frontend.utils.constants import NEW_CHAT
from frontend.utils.logos import BD_LOGO


class ChatPage:
    chat_history_key = "chat_history"
    delete_btn_key = "delete_btn"
    feedbacks_key = "feedbacks"
    feedback_clicked_key = "feedback_clicked"
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

    def _handle_send_feedback(self, feedback_id: str, message_pair_id: uuid.UUID):
        """Handle feedback sending.

        Args:
            feedback_id (str): The feedback button identifier.
            message_pair_id (uuid.UUID): The message pair identifier.
        """
        def reset_feedback_state():
            page_feedbacks: dict = st.session_state[self.page_id][self.feedbacks_key]
            st.session_state[feedback_id] = page_feedbacks.get(feedback_id)
            st.session_state[self.page_id][self.feedback_clicked_key] = False

        @st.dialog("Feedback", on_dismiss=reset_feedback_state)
        def show_feedback_popup():
            feedback = st.session_state[feedback_id]
            access_token = st.session_state["access_token"]

            if feedback:
                placeholder = "O que foi satisfatório na resposta?"
            else:
                placeholder = "O que foi insatisfatório na resposta?"

            comments = st.text_area(
                label=":gray[Comentários adicionais (opcional)]",
                placeholder=placeholder,
                value=None,
            )

            with stylable_container(
                key="feedback_dialog_buttons",
                css_styles="""
                    button {
                        white-space: nowrap;
                    }
                """
            ):
                _, col1, col2 = st.columns([0.64, 0.18, 0.22])

                if col1.button("Enviar", type="primary"):
                    if self.api.send_feedback(
                        access_token=access_token,
                        message_pair_id=message_pair_id,
                        rating=feedback,
                        comments=comments
                    ):
                        page_feedbacks = st.session_state[self.page_id][self.feedbacks_key]
                        page_feedbacks[feedback_id] = feedback
                        st.session_state[self.page_id][self.feedback_clicked_key] = False
                        st.rerun()
                    else:
                        st.error("Não foi possível enviar o feedback.", icon=":material/error:")

                if col2.button("Cancelar"):
                    reset_feedback_state()
                    st.rerun()

        show_feedback_popup()

    def _handle_click_feedback(self, feedback_id: str, message_pair_id: uuid.UUID):
        """Handle feedback buttons click and open the feedback dialog.

        Args:
            feedback_id (str): The feedback button identifier.
            message_pair_id (uuid.UUID): The message pair identifier.
        """
        feedback = st.session_state[feedback_id]

        page_feedbacks: dict = st.session_state[self.page_id][self.feedbacks_key]

        # If feedback is None *after* a button click, it means Streamlit
        # is resetting the button state, which we don’t want. In this case,
        # restore it to its previous value.
        if feedback is None:
            st.session_state[feedback_id] = page_feedbacks.get(feedback_id)

        # Finally, set the feedback clicked flag and open the feedback dialog
        st.session_state[self.page_id][self.feedback_clicked_key] = True
        self._handle_send_feedback(feedback_id, message_pair_id)

    def _render_message_buttons(self, message_pair: MessagePair):
        """Render the feedback buttons on assistant's messages.

        Args:
            message_pair (MessagePair):
                A MessagePair object containing:
                    - id: unique identifier.
                    - user_message: user message.
                    - assistant_message: assistant message.
                    - error_message: error message.
                    - events: list of streamed events.
        """
        # Checks if the model is still answering the question.
        # If so, all message buttons are disabled
        waiting_for_answer = st.session_state[self.page_id][self.waiting_key]

        # Unique identifier for the feedback buttons widget
        feedback_id = f"feedback_{message_pair.id}"

        # Look for the feedback buttons widget in the session state
        page_feedbacks = st.session_state[self.page_id][self.feedbacks_key]

        # Restore previous feedback state if it already exists in the session
        # and no feedback was clicked in this run, to persist state across reruns
        if (
            feedback_id in page_feedbacks and
            not st.session_state[self.page_id][self.feedback_clicked_key]
        ):
            last_feedback = page_feedbacks[feedback_id]
            st.session_state[feedback_id] = last_feedback

        # Render the feedback buttons
        st.feedback(
            "thumbs",
            key=feedback_id,
            on_change=self._handle_click_feedback,
            args=(feedback_id, message_pair.id),
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
        # Placeholder for the subheader message
        subheader = st.empty()

        # Initialize page session state
        if self.page_id not in st.session_state:
            st.session_state[self.page_id] = {}

        page_session_state = st.session_state[self.page_id]

        # Initialize feedback history
        if self.feedbacks_key not in page_session_state:
            page_session_state[self.feedbacks_key] = {}

        # Initialize flag to check if the feedback button is clicked
        if self.feedback_clicked_key not in page_session_state:
            page_session_state[self.feedback_clicked_key] = False

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

        user_avatar = st.session_state.get("user_avatar")

        # Display chat messages from history on app rerun
        for message_pair in chat_history:
            with st.chat_message("user", avatar=user_avatar):
                st.write(message_pair.user_message)

            with st.chat_message("assistant", avatar=BD_LOGO):
                st.empty()

                if message_pair.assistant_message is not None:
                    label, state = "Concluído!", "complete"
                else:
                    label, state = "Erro", "error"

                with st.status(label=label, state=state) as status:
                    for event in message_pair.events:
                        _display_tool_event(event)

                if message_pair.assistant_message is not None:
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
            with st.chat_message("user", avatar=user_avatar):
                st.write(user_prompt)

            # Create thread only in the first message
            if (
                self.thread_id is None and not
                self._create_thread_and_register(title=user_prompt)
            ):
                _clear_new_chat_page()
                return

            # Display assistant response in chat message container
            with st.chat_message("assistant", avatar=BD_LOGO):
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

                if message_pair.assistant_message is not None:
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
    sql_query: str = args.get("sql_query", "")

    if not sql_query:
        return json.dumps(args, indent=2, ensure_ascii=False)

    sql_query = sqlparse.format(
        sql_query.strip(),
        reindent=True,
        keyword_case="upper"
    )

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
                if tool_output.metadata and tool_output.metadata.get("truncated"):
                    st.info("Resposta muito extensa. Exibindo resultados parciais.", icon=":material/info:")
                tool_outputs = _format_tool_outputs(tool_output.output)
                _display_code_block(f"Resposta:\n{tool_outputs}")
