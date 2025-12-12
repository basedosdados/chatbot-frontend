from typing import Iterator
from uuid import UUID, uuid4

import httpx
import jwt
from loguru import logger

from frontend.datatypes import (EventData, MessagePair, StreamEvent, Thread,
                                UserMessage)

from datetime import datetime, timedelta


class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.logger = logger.bind(classname=self.__class__.__name__)

    def _is_token_expired(self, token: str) -> bool:
        """Check if token is expired or about to expire (within 1 minute)."""
        if not token:
            return True

        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp = decoded.get("exp")
            if not exp:
                return True
            expiration = datetime.fromtimestamp(exp)
            return datetime.now() >= expiration - timedelta(seconds=60)
        except Exception:
            return True

    def _refresh_access_token(self, refresh_token: str) -> str|None:
        """Refresh the access token using refresh token."""
        try:
            response = httpx.post(
                f"{self.base_url}/chatbot/token/refresh/",
                json={"refresh": refresh_token}
            )
            response.raise_for_status()
            access_token = response.json()["access"]
            self.logger.success("[AUTH] Access token refreshed successfully")
            return access_token
        except httpx.HTTPStatusError:
            if response.status_code == httpx.codes.UNAUTHORIZED:
                self.logger.warning(f"[AUTH] Refresh token expired")
        except Exception:
            self.logger.exception("[AUTH] Failed to refresh token:")
        return None

    def _get_headers(self, access_token: str, refresh_token: str) -> dict[str, str]:
        if self._is_token_expired(access_token):
            self.logger.info("[AUTH] Access token expired, refreshing...")
            access_token = self._refresh_access_token(refresh_token)
        if access_token is not None:
            return {"Authorization": f"Bearer {access_token}"}
        return None

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
                url=f"{self.base_url}/chatbot/token/",
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
                url=f"{self.base_url}/chatbot/threads/",
                json={"title": title},
                headers=self._get_headers(access_token, refresh_token),
            )
            response.raise_for_status()
            thread = Thread(**response.json())
            self.logger.success(f"[THREAD] Thread created successfully for user {thread.account}")
            return thread
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
                url=f"{self.base_url}/chatbot/threads/",
                params={"order_by": "created_at"},
                headers=self._get_headers(access_token, refresh_token)
            )
            response.raise_for_status()
            threads = [Thread(**thread) for thread in response.json()]
            self.logger.success(f"[THREAD] Threads retrieved successfully")
            return threads
        except Exception:
            self.logger.exception(f"[THREAD] Error on threads retrieval:")
            return None

    def get_message_pairs(self, access_token: str, refresh_token: str, thread_id: UUID) -> list[MessagePair]|None:
        """Get all messages from a thread.

        Args:
            access_token (str): User access token.
            refresh_token (str): User refresh token.
            thread_id (UUID): Thread unique identifier.

        Returns:
            list[MessagePair]|None: A list of MessagePair objects if any message was found. None otherwise.
        """
        self.logger.info(f"[MESSAGE] Retrieving message pairs for thread {thread_id}")
        try:
            response = httpx.get(
                url=f"{self.base_url}/chatbot/threads/{thread_id}/messages/",
                params={"order_by": "created_at"},
                headers=self._get_headers(access_token, refresh_token)
            )
            response.raise_for_status()
            message_pairs = [MessagePair(**pair) for pair in response.json()]
            self.logger.success(f"[MESSAGE] Message pairs retrieved successfully for thread {thread_id}")
            return message_pairs
        except Exception:
            self.logger.exception(f"[MESSAGE] Error on message pairs retrieval for thread {thread_id}:")
            return None

    def send_message(self, access_token: str, refresh_token: str, message: str, thread_id: UUID) -> Iterator[StreamEvent]:
        """Send a user message and stream the assistant's response.

        Args:
            access_token (str): User access token.
            refresh_token (str): User refresh token.
            message (str): The message sent by the user.
            thread_id (UUID):Thread unique identifier.

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
                url=f"{self.base_url}/chatbot/threads/{thread_id}/messages/",
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
                data=EventData(run_id=uuid4())
            )

    def send_feedback(self, access_token: str, refresh_token: str, message_pair_id: UUID, rating: int, comments: str) -> bool:
        """Send a feedback.

        Args:
            access_token (str): User access token.
            refresh_token (str): User refresh token.
            message_pair_id (UUID): The message pair unique identifier.
            rating (int): The rating (0 or 1).
            comments (str): The comments.

        Returns:
            bool: Whether the operation succeeded or not.
        """
        self.logger.info(f"[FEEDBACK] Sending feedback ({rating}) for message pair {message_pair_id}")

        try:
            response = httpx.put(
                url=f"{self.base_url}/chatbot/message-pairs/{message_pair_id}/feedbacks/",
                json={"rating": rating, "comment": comments},
                headers=self._get_headers(access_token, refresh_token)
            )
            response.raise_for_status()
            self.logger.success(f"[FEEDBACK] Feedback sent successfully")
            return True
        except Exception:
            self.logger.exception(f"[FEEDBACK] Error on sending feedback:")
            return False

    def delete_thread(self, access_token: str, refresh_token: str, thread_id: UUID) -> bool:
        """Soft delete a thread and hard delete all its checkpoints.

        Args:
            access_token (str): User access token.
            refresh_token (str): User refresh token.
            thread_id (UUID): Thread unique identifier.

        Returns:
            bool: Whether the operation succeeded or not.
        """
        self.logger.info(f"""[CLEAR] Clearing assistant memory""")

        try:
            response = httpx.delete(
                url=f"{self.base_url}/chatbot/threads/{thread_id}/",
                headers=self._get_headers(access_token, refresh_token),
                timeout=httpx.Timeout(5.0, read=60.0)
            )
            response.raise_for_status()
            self.logger.success(f"[CLEAR] Assistant memory cleared successfully")
            return True
        except Exception:
            self.logger.exception("[CLEAR] Error on clearing assistant memory:")
            return False
