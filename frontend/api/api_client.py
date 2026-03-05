import uuid
from datetime import datetime, timedelta
from typing import Iterator

import httpx
import jwt
import streamlit as st
from loguru import logger
from pydantic import UUID4

from frontend.datatypes import EventData, Message, StreamEvent, Thread, UserMessage
from frontend.exceptions import AccessForbiddenException, SessionExpiredException

_AUTH_QUERY = """
mutation getToken($email: String!,  $password: String!) {
    tokenAuth(email: $email, password: $password) {
        token
    }
}
"""

_AUTH_REFRESH_QUERY = """
mutation refreshToken($token: String!) {
    refreshToken(token: $token) {
        token
    }
}
"""

_VERIFY_TOKEN_QUERY = """
mutation verifyToken($token: String!) {
    verifyToken(token: $token) {
        payload
    }
}
"""


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

    def _refresh_access_token(self, access_token: str) -> str:
        """Refresh the access token.

        Args:
            access_token (str): The access token.

        Returns:
            str: A refreshed access token.
        """
        response = httpx.post(
            f"{self.base_website_url}/graphql",
            json={"query": _AUTH_REFRESH_QUERY, "variables": {"token": access_token}},
        )
        response.raise_for_status()

        payload = response.json()["data"]["refreshToken"]

        if payload is None:
            return None

        return payload["token"]

    def _verify_token(self, access_token: str) -> bool:
        """Check if a user has chatbot access.

        Args:
            access_token (str): The user's access token.

        Returns:
            bool: Whether the user has chatbot access or not.
        """
        response = httpx.post(
            url=f"{self.base_website_url}/graphql",
            json={
                "query": _VERIFY_TOKEN_QUERY,
                "variables": {"token": access_token},
            },
        )
        response.raise_for_status()

        payload = response.json()["data"]["verifyToken"]["payload"]
        return payload["has_chatbot_access"]

    def _get_headers(self, access_token: str) -> dict[str, str]:
        """Get authorization headers, refreshing access token as needed.

        Args:
            access_token (str): The access token.

        Raises:
            SessionExpiredException: If refresh token is None.
            AccessForbiddenException: If the user does not have chatbot access.

        Returns:
            dict[str, str]: The authorization headers,
        """
        if self._is_token_expired(access_token):
            self.logger.info("[AUTH] Access token expired, refreshing...")
            access_token = self._refresh_access_token(access_token)

            if access_token is not None:
                if not self._verify_token(access_token):
                    self.logger.info("[AUTH] Access forbidden")
                    raise AccessForbiddenException
                st.session_state["access_token"] = access_token
                self.logger.success("[AUTH] Access token refreshed successfully")
            else:
                self.logger.info("[AUTH] Refresh token expired")
                raise SessionExpiredException

        return {"Authorization": f"Bearer {access_token}"}

    @staticmethod
    def _raise_for_status(response: httpx.Response):
        """Raise for HTTP errors, converting 403 into AccessForbiddenException.

        Args:
            response (httpx.Response): The HTTP response.

        Raises:
            AccessForbiddenException: If the response status code is 403 (Forbidden).
            httpx.HTTPStatusError: If the response status code indicates any other error.
        """
        if response.status_code == httpx.codes.FORBIDDEN:
            raise AccessForbiddenException
        response.raise_for_status()

    def authenticate(self, email: str, password: str) -> tuple[str | None, str]:
        """Send a post request to the authentication endpoint.

        Args:
            email (str): The email.
            password (str): The password.

        Returns:
            tuple[str|None, str]:
                A tuple containing the access token and a status message.
        """
        access_token = None
        message = "Ops! Ocorreu um erro durante o login. Por favor, tente novamente."

        try:
            response = httpx.post(
                url=f"{self.base_website_url}/graphql",
                json={
                    "query": _AUTH_QUERY,
                    "variables": {"email": email, "password": password},
                },
            )
            response.raise_for_status()

            access_token = (
                response.json().get("data", {}).get("tokenAuth", {}).get("token")
            )

            if access_token:
                if not self._verify_token(access_token):
                    raise AccessForbiddenException
                self.logger.success("[AUTH] Successfully logged in")
                message = "Conectado com sucesso!"
            else:
                self.logger.error("[AUTH] No access token returned")
        except httpx.HTTPStatusError:
            access_token = None
            if response.status_code == httpx.codes.UNAUTHORIZED:
                self.logger.info("[AUTH] Invalid credentials")
                message = "Usuário ou senha incorretos."
            else:
                self.logger.exception("[AUTH] HTTP error:")
        except AccessForbiddenException:
            access_token = None
            message = "Você não possui acesso ao chatbot. Para mais informações, contate um administrador."
            self.logger.info("[AUTH] Access forbidden")
        except Exception:
            access_token = None
            self.logger.exception("[AUTH] Login error:")

        return access_token, message

    def create_thread(self, access_token: str, title: str) -> Thread | None:
        """Create a thread.

        Args:
            access_token (str): User access token.
            title (str): The thread title.

        Returns:
            Thread|None: A Thread object if the thread was created successfully. None otherwise.
        """
        self.logger.info("[THREAD] Creating thread")

        try:
            response = httpx.post(
                url=f"{self.base_chatbot_url}/api/v1/chatbot/threads",
                json={"title": title},
                headers=self._get_headers(access_token),
            )
            self._raise_for_status(response)
            thread = Thread(**response.json())
            self.logger.success(
                f"[THREAD] Thread created successfully for user {thread.user_id}"
            )
            return thread
        except (SessionExpiredException, AccessForbiddenException):
            raise
        except Exception:
            self.logger.exception("[THREAD] Error on thread creation:")
            return None

    def get_threads(self, access_token: str) -> list[Thread] | None:
        """Get all threads from a user.

        Args:
            access_token (str): User access token.

        Returns:
            list[Thread]|None: A list of Thread objects if any thread was found. None otherwise.
        """
        self.logger.info("[THREAD] Retrieving threads")
        try:
            response = httpx.get(
                url=f"{self.base_chatbot_url}/api/v1/chatbot/threads",
                params={"order_by": "created_at"},
                headers=self._get_headers(access_token),
            )
            self._raise_for_status(response)
            threads = [Thread(**thread) for thread in response.json()]
            self.logger.success("[THREAD] Threads retrieved successfully")
            return threads
        except (SessionExpiredException, AccessForbiddenException):
            raise
        except Exception:
            self.logger.exception("[THREAD] Error on threads retrieval:")
            return None

    def get_messages(self, access_token: str, thread_id: UUID4) -> list[Message] | None:
        """Get all messages from a thread.

        Args:
            access_token (str): User access token.
            thread_id (UUID4): Thread unique identifier.

        Returns:
            list[Message]|None: A list of Message objects if any message was found. None otherwise.
        """
        self.logger.info(f"[MESSAGE] Retrieving messages for thread {thread_id}")
        try:
            response = httpx.get(
                url=f"{self.base_chatbot_url}/api/v1/chatbot/threads/{thread_id}/messages",
                params={"order_by": "created_at"},
                headers=self._get_headers(access_token),
            )
            self._raise_for_status(response)
            messages = [Message(**msg) for msg in response.json()]
            self.logger.success(
                f"[MESSAGE] Messages retrieved successfully for thread {thread_id}"
            )
            return messages
        except (SessionExpiredException, AccessForbiddenException):
            raise
        except Exception:
            self.logger.exception(
                f"[MESSAGE] Error on messages retrieval for thread {thread_id}:"
            )
            return None

    def send_message(
        self, access_token: str, message: str, thread_id: UUID4
    ) -> Iterator[StreamEvent]:
        """Send a user message and stream the assistant's response.

        Args:
            access_token (str): User access token.
            message (str): The message sent by the user.
            thread_id (UUID4):Thread unique identifier.

        Yields:
            Iterator[StreamEvent]: Iterator of `StreamEvent` objects.
        """
        user_message = UserMessage(content=message)

        self.logger.info(
            f"[MESSAGE] Sending message {user_message.id} in thread {thread_id}"
        )

        error_message = None
        stream_completed = False

        try:
            with httpx.stream(
                method="POST",
                url=f"{self.base_chatbot_url}/api/v1/chatbot/threads/{thread_id}/messages",
                headers=self._get_headers(access_token),
                json=user_message.model_dump(mode="json"),
                timeout=httpx.Timeout(5.0, read=300.0),
            ) as response:
                self._raise_for_status(response)

                self.logger.success("[MESSAGE] User message sent successfully")

                for line in response.iter_lines():
                    if not line:
                        continue

                    event = StreamEvent.model_validate_json(line)

                    if event.type == "complete":
                        stream_completed = True

                    yield event
        except (SessionExpiredException, AccessForbiddenException):
            raise
        except httpx.ReadTimeout:
            self.logger.exception("[MESSAGE] Timeout error on sending user message:")
            error_message = (
                "Ops, parece que a solicitação expirou! Por favor, tente novamente. "
                "Se o problema persistir, avise-nos. Obrigado pela paciência!"
            )
        except Exception:
            self.logger.exception("[MESSAGE] Error on sending user message:")
            error_message = (
                "Ops, algo deu errado! Por favor, tente novamente. "
                "Se o problema persistir, avise-nos. Obrigado pela paciência!"
            )

        # Safeguard for unexpected stream termination. Handles cases where the server
        # crashes and the httpx.stream() call ends silently without raising an exception.
        if not stream_completed:
            if not error_message:
                self.logger.error(
                    "[MESSAGE] Stream terminated without a 'complete' status"
                )
                error_message = (
                    "Ops, a conexão com o servidor foi interrompida inesperadamente! "
                    "Por favor, tente novamente mais tarde. Se o problema persistir, avise-nos."
                )

            yield StreamEvent(
                type="error", data=EventData(error_details={"message": error_message})
            )

            yield StreamEvent(type="complete", data=EventData(run_id=uuid.uuid4()))

    def send_feedback(
        self, access_token: str, message_id: UUID4, rating: int, comments: str
    ) -> bool:
        """Send a feedback.

        Args:
            access_token (str): User access token.
            message_id (UUID4): The message unique identifier.
            rating (int): The rating (0 or 1).
            comments (str): The comments.

        Returns:
            bool: Whether the operation succeeded or not.
        """
        self.logger.info(
            f"[FEEDBACK] Sending feedback ({rating}) for message pair {message_id}"
        )

        try:
            response = httpx.put(
                url=f"{self.base_chatbot_url}/api/v1/chatbot/messages/{message_id}/feedback",
                json={"rating": rating, "comments": comments},
                headers=self._get_headers(access_token),
            )
            self._raise_for_status(response)
            self.logger.success("[FEEDBACK] Feedback sent successfully")
            return True
        except (SessionExpiredException, AccessForbiddenException):
            raise
        except Exception:
            self.logger.exception("[FEEDBACK] Error on sending feedback:")
            return False

    def delete_thread(self, access_token: str, thread_id: UUID4) -> bool:
        """Soft delete a thread and hard delete all its checkpoints.

        Args:
            access_token (str): User access token.
            thread_id (UUID4): Thread unique identifier.

        Returns:
            bool: Whether the operation succeeded or not.
        """
        self.logger.info("""[CLEAR] Clearing assistant memory""")

        try:
            response = httpx.delete(
                url=f"{self.base_chatbot_url}/api/v1/chatbot/threads/{thread_id}",
                headers=self._get_headers(access_token),
                timeout=httpx.Timeout(5.0, read=60.0),
            )
            self._raise_for_status(response)
            self.logger.success("[CLEAR] Assistant memory cleared successfully")
            return True
        except (SessionExpiredException, AccessForbiddenException):
            raise
        except Exception:
            self.logger.exception("[CLEAR] Error on clearing assistant memory:")
            return False
