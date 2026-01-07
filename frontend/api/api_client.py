import uuid
from datetime import datetime, timedelta
from typing import Iterator

import httpx
import jwt
import streamlit as st
from loguru import logger
from pydantic import UUID4

from frontend.datatypes import (EventData, Message, StreamEvent, Thread,
                                UserMessage)
from frontend.exceptions import SessionExpiredException


class APIClient:
    def __init__(self, base_website_url: str, base_chatbot_url: str):
        self.base_website_url = base_website_url
        self.base_chatbot_url = base_chatbot_url
        self.logger = logger.bind(classname=self.__class__.__name__)

    def _is_token_expired(self, token: str) -> bool:
        """Check if a JWT token is expired or about to expire (within 1 minute).

        Args:
            token (str): The token.

        Returns:
            bool: Whether the token is expired or not.
        """
        if not token:
            return True

        try:
            payload: dict = jwt.decode(token, options={"verify_signature": False})
            exp = payload.get("exp")
            if not exp:
                return True
            expiration = datetime.fromtimestamp(exp)
            return datetime.now() >= expiration - timedelta(seconds=60)
        except Exception:
            return True

    def _refresh_access_token(self, refresh_token: str) -> str:
        """Refresh the access token using a refresh token.

        Args:
            refresh_token (str): The refresh token.

        Returns:
            str: A refreshed access token.
        """
        response = httpx.post(
            f"{self.base_website_url}/chatbot/token/refresh/",
            json={"refresh": refresh_token}
        )
        response.raise_for_status()
        access_token = response.json()["access"]
        return access_token

    def _get_headers(self, access_token: str, refresh_token: str) -> dict[str, str]:
        """Get authorization headers, refreshing access token as needed.

        Args:
            access_token (str): The access token.
            refresh_token (str): The refresh token.

        Raises:
            SessionExpiredException: If refresh token is expired (401).

        Returns:
            dict[str, str]: The authorization headers,
        """
        if self._is_token_expired(access_token):
            self.logger.info("[AUTH] Access token expired, refreshing...")
            try:
                access_token = self._refresh_access_token(refresh_token)
                st.session_state["access_token"] = access_token
                self.logger.success("[AUTH] Access token refreshed successfully")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == httpx.codes.UNAUTHORIZED:
                    self.logger.info("[AUTH] Refresh token expired")
                    raise SessionExpiredException from e
                raise  # Re-raise other HTTP errors

        return {"Authorization": f"Bearer {access_token}"}

    def authenticate(self, email: str, password: str) -> tuple[str|None, str|None, str]:
        """Send a post request to the authentication endpoint.

        Args:
            email (str): The email.
            password (str): The password.

        Returns:
            tuple[str|None, str|None, str]:
                A tuple containing the access token, the refresh token and a status message.
        """
        access_token = None
        refresh_token = None
        message = "Ops! Ocorreu um erro durante o login. Por favor, tente novamente."

        try:
            response = httpx.post(
                url=f"{self.base_website_url}/chatbot/token/",
                data={
                    "email": email,
                    "password": password
                }
            )
            response.raise_for_status()

            access_token = response.json().get("access")
            refresh_token = response.json().get("refresh")

            if access_token and refresh_token:
                self.logger.success(f"[AUTH] Successfully logged in")
                message = "Conectado com sucesso!"
            else:
                self.logger.error(f"[AUTH] No access and refresh tokens returned")
        except httpx.HTTPStatusError:
            if response.status_code == httpx.codes.UNAUTHORIZED:
                self.logger.warning(f"[AUTH] Invalid credentials")
                message = "Usuário ou senha incorretos."
            else:
                self.logger.exception(f"[AUTH] HTTP error:")
        except Exception:
            self.logger.exception(f"[AUTH] Login error:")

        return access_token, refresh_token, message

    def create_thread(self, access_token: str, refresh_token: str, title: str) -> Thread|None:
        """Create a thread.

        Args:
            access_token (str): User access token.
            refresh_token (str): User refresh token.
            title (str): The thread title.

        Returns:
            Thread|None: A Thread object if the thread was created successfully. None otherwise.
        """
        self.logger.info("[THREAD] Creating thread")

        try:
            response = httpx.post(
                url=f"{self.base_chatbot_url}/api/v1/chatbot/threads/",
                json={"title": title},
                headers=self._get_headers(access_token, refresh_token),
            )
            response.raise_for_status()
            thread = Thread(**response.json())
            self.logger.success(f"[THREAD] Thread created successfully for user {thread.user_id}")
            return thread
        except SessionExpiredException:
            raise
        except Exception:
            self.logger.exception(f"[THREAD] Error on thread creation:")
            return None

    def get_threads(self, access_token: str, refresh_token: str) -> list[Thread]|None:
        """Get all threads from a user.

        Args:
            access_token (str): User access token.
            refresh_token (str): User refresh token.

        Returns:
            list[Thread]|None: A list of Thread objects if any thread was found. None otherwise.
        """
        self.logger.info("[THREAD] Retrieving threads")
        try:
            response = httpx.get(
                url=f"{self.base_chatbot_url}/api/v1/chatbot/threads/",
                params={"order_by": "created_at"},
                headers=self._get_headers(access_token, refresh_token)
            )
            self.logger.info(f"{response.json() = }")
            response.raise_for_status()
            threads = [Thread(**thread) for thread in response.json()]
            self.logger.success(f"[THREAD] Threads retrieved successfully")
            return threads
        except SessionExpiredException:
            raise
        except Exception:
            self.logger.exception(f"[THREAD] Error on threads retrieval:")
            return None

    def get_messages(self, access_token: str, refresh_token: str, thread_id: UUID4) -> list[Message]|None:
        """Get all messages from a thread.

        Args:
            access_token (str): User access token.
            refresh_token (str): User refresh token.
            thread_id (UUID4): Thread unique identifier.

        Returns:
            list[Message]|None: A list of Message objects if any message was found. None otherwise.
        """
        self.logger.info(f"[MESSAGE] Retrieving messages for thread {thread_id}")
        try:
            response = httpx.get(
                url=f"{self.base_chatbot_url}/api/v1/chatbot/threads/{thread_id}/messages/",
                params={"order_by": "created_at"},
                headers=self._get_headers(access_token, refresh_token)
            )
            response.raise_for_status()
            messages = [Message(**msg) for msg in response.json()]
            self.logger.success(f"[MESSAGE] Messages retrieved successfully for thread {thread_id}")
            return messages
        except SessionExpiredException:
            raise
        except Exception:
            self.logger.exception(f"[MESSAGE] Error on messages retrieval for thread {thread_id}:")
            return None

    def send_message(self, access_token: str, refresh_token: str, message: str, thread_id: UUID4) -> Iterator[StreamEvent]:
        """Send a user message and stream the assistant's response.

        Args:
            access_token (str): User access token.
            refresh_token (str): User refresh token.
            message (str): The message sent by the user.
            thread_id (UUID4):Thread unique identifier.

        Yields:
            Iterator[StreamEvent]: Iterator of `StreamEvent` objects.
        """
        user_message = UserMessage(content=message)

        self.logger.info(f"[MESSAGE] Sending message {user_message.id} in thread {thread_id}")

        error_message = None
        stream_completed = False

        try:
            with httpx.stream(
                method="POST",
                url=f"{self.base_chatbot_url}/api/v1/chatbot/threads/{thread_id}/messages/",
                headers=self._get_headers(access_token, refresh_token),
                json=user_message.model_dump(mode="json"),
                timeout=httpx.Timeout(5.0, read=300.0),
            ) as response:
                response.raise_for_status()

                self.logger.success(f"[MESSAGE] User message sent successfully")

                for line in response.iter_lines():
                    if not line:
                        continue

                    event = StreamEvent.model_validate_json(line)

                    if event.type == "complete":
                        stream_completed = True

                    yield event
        except SessionExpiredException:
            raise
        except httpx.ReadTimeout:
            self.logger.exception(f"[MESSAGE] Timeout error on sending user message:")
            error_message=(
                "Ops, parece que a solicitação expirou! Por favor, tente novamente. "
                "Se o problema persistir, avise-nos. Obrigado pela paciência!"
            )
        except Exception:
            self.logger.exception(f"[MESSAGE] Error on sending user message:")
            error_message=(
                "Ops, algo deu errado! Por favor, tente novamente. "
                "Se o problema persistir, avise-nos. Obrigado pela paciência!"
            )

        # Safeguard for unexpected stream termination. Handles cases where the server
        # crashes and the httpx.stream() call ends silently without raising an exception.
        if not stream_completed:
            if not error_message:
                self.logger.error("[MESSAGE] Stream terminated without a 'complete' status")
                error_message=(
                    "Ops, a conexão com o servidor foi interrompida inesperadamente! "
                    "Por favor, tente novamente mais tarde. Se o problema persistir, avise-nos."
                )

            yield StreamEvent(
                type="error",
                data=EventData(error_details={"message": error_message})
            )

            yield StreamEvent(
                type="complete",
                data=EventData(run_id=uuid.uuid4())
            )

    def send_feedback(self, access_token: str, refresh_token: str, message_id: UUID4, rating: int, comments: str) -> bool:
        """Send a feedback.

        Args:
            access_token (str): User access token.
            refresh_token (str): User refresh token.
            message_id (UUID4): The message unique identifier.
            rating (int): The rating (0 or 1).
            comments (str): The comments.

        Returns:
            bool: Whether the operation succeeded or not.
        """
        self.logger.info(f"[FEEDBACK] Sending feedback ({rating}) for message pair {message_id}")

        try:
            response = httpx.put(
                url=f"{self.base_chatbot_url}/api/v1/chatbot/messages/{message_id}/feedbacks/",
                json={"rating": rating, "comments": comments},
                headers=self._get_headers(access_token, refresh_token)
            )
            response.raise_for_status()
            self.logger.success(f"[FEEDBACK] Feedback sent successfully")
            return True
        except SessionExpiredException:
            raise
        except Exception:
            self.logger.exception(f"[FEEDBACK] Error on sending feedback:")
            return False

    def delete_thread(self, access_token: str, refresh_token: str, thread_id: UUID4) -> bool:
        """Soft delete a thread and hard delete all its checkpoints.

        Args:
            access_token (str): User access token.
            refresh_token (str): User refresh token.
            thread_id (UUID4): Thread unique identifier.

        Returns:
            bool: Whether the operation succeeded or not.
        """
        self.logger.info(f"""[CLEAR] Clearing assistant memory""")

        try:
            response = httpx.delete(
                url=f"{self.base_chatbot_url}/api/v1/chatbot/threads/{thread_id}/",
                headers=self._get_headers(access_token, refresh_token),
                timeout=httpx.Timeout(5.0, read=60.0)
            )
            response.raise_for_status()
            self.logger.success(f"[CLEAR] Assistant memory cleared successfully")
            return True
        except SessionExpiredException:
            raise
        except Exception:
            self.logger.exception("[CLEAR] Error on clearing assistant memory:")
            return False
