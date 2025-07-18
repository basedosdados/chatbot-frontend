import json
from typing import Iterator
from uuid import UUID

import httpx
from loguru import logger

from frontend.datatypes import MessagePair, Step, Thread, UserMessage


class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.logger = logger.bind(classname=self.__class__.__name__)

    def authenticate(self, email: str, password: str) -> tuple[str|None, str]:
        """Send a post request to the authentication endpoint.

        Args:
            email (str): The email.
            password (str): The password.

        Returns:
            tuple[str|None, str]: A tuple containing the access token and a status message.
        """
        access_token = None

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

            if access_token:
                self.logger.success(f"[LOGIN] Successfully logged in")
                message = "Conectado com sucesso!"
            else:
                self.logger.error(f"[LOGIN] No access token returned")
        except httpx.HTTPStatusError:
            if response.status_code == httpx.codes.UNAUTHORIZED:
                self.logger.warning(f"[LOGIN] Invalid credentials")
                message = "Usuário ou senha incorretos."
            else:
                self.logger.exception(f"[LOGIN] HTTP error:")
        except Exception:
            self.logger.exception(f"[LOGIN] Login error:")

        return access_token, message

    def create_thread(self, access_token: str, title: str) -> Thread|None:
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
                url=f"{self.base_url}/chatbot/threads/",
                json={"title": title},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            thread = Thread(**response.json())
            self.logger.success(f"[THREAD] Thread created successfully for user {thread.account}")
            return thread
        except Exception:
            self.logger.exception(f"[THREAD] Error on thread creation:")
            return None

    def get_threads(self, access_token: str) -> list[Thread]|None:
        """Get all threads from a user.

        Args:
            access_token (str): User access token.

        Returns:
            list[Thread]|None: A list of Thread objects if any thread was found. None otherwise.
        """
        self.logger.info("[THREAD] Retrieving threads")
        try:
            response = httpx.get(
                url=f"{self.base_url}/chatbot/threads/",
                params={"order_by": "created_at"},
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            threads = [Thread(**thread) for thread in response.json()]
            self.logger.success(f"[THREAD] Threads retrieved successfully")
            return threads
        except Exception:
            self.logger.exception(f"[THREAD] Error on threads retrieval:")
            return None

    def get_message_pairs(self, access_token: str, thread_id: UUID) -> list[MessagePair]|None:
        self.logger.info(f"[MESSAGE] Retrieving message pairs for thread {thread_id}")
        try:
            response = httpx.get(
                url=f"{self.base_url}/chatbot/threads/{thread_id}/messages/",
                params={"order_by": "created_at"},
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            message_pairs = [MessagePair(**pair) for pair in response.json()]
            self.logger.success(f"[MESSAGE] Message pairs retrieved successfully for thread {thread_id}")
            return message_pairs
        except Exception:
            self.logger.exception(f"[MESSAGE] Error on message pairs retrieval for thread {thread_id}:")
            return None

    def send_message(self, access_token: str, message: str, thread_id: UUID) -> Iterator[tuple[str, Step|MessagePair]]:
        """Send a user message and stream the assistant's response.

        Args:
            access_token (str): The user's access token.
            message (str): The message sent by the user.
            thread_id (UUID): The unique identifier of the thread.

        Yields:
            Iterator[tuple[str, Step|MessagePair]]: Tuples containing a status message and either a `Step` or `MessagePair` object.
                While streaming, `Step` objects are yielded. Once streaming is complete, a final `MessagePair` is yielded.
        """
        user_message = UserMessage(content=message)

        self.logger.info(f"[MESSAGE] Sending message {user_message.id} in thread {thread_id}")

        steps = []

        try:
            with httpx.stream(
                method="POST",
                url=f"{self.base_url}/chat/threads/{thread_id}/messages/stream/",
                headers={"Authorization": f"Bearer {access_token}"},
                json=user_message.model_dump(mode="json"),
                timeout=httpx.Timeout(5.0, read=300.0),
            ) as response:
                response.raise_for_status()

                self.logger.success(f"[MESSAGE] User message sent successfully")

                for line in response.iter_lines():
                    if not line:
                        continue

                    payload = json.loads(line)
                    streaming_status = payload["status"]
                    data = payload["data"]

                    if streaming_status == "running":
                        message = Step.model_validate_json(data)
                        steps.append(message)
                    elif streaming_status == "complete":
                        data["steps"] = steps
                        message = MessagePair(**data)

                    yield streaming_status, message
        except httpx.ReadTimeout:
            self.logger.exception(f"[MESSAGE] Timeout error on sending user message:")
            message = MessagePair(
                user_message=user_message.content,
                error_message=(
                    "Ops, parece que a solicitação expirou! Por favor, tente novamente. "
                    "Se o problema persistir, avise-nos. Obrigado pela paciência!"
                ),
                steps=steps or [],
            )
            yield "complete", message
        except Exception:
            self.logger.exception(f"[MESSAGE] Error on sending user message:")
            message = MessagePair(
                user_message=user_message.content,
                error_message=(
                    "Ops, algo deu errado! Por favor, tente novamente. "
                    "Se o problema persistir, avise-nos. Obrigado pela paciência!"
                ),
                steps=steps or [],
            )
            yield "complete", message

    def send_feedback(self, access_token: str, message_pair_id: UUID, rating: int, comments: str) -> bool:
        """Send a feedback.

        Args:
            access_token (str): User access token.
            message_pair_id (UUID): The message pair unique identifier.
            rating (int): The rating (0 or 1).
            comments (str): The comments.

        Returns:
            bool: Whether the operation succeeded or not.
        """
        feedback_meaning = "positive" if rating else "negative"

        self.logger.info(f"[FEEDBACK] Sending {feedback_meaning} feedback for message pair {message_pair_id}")

        try:
            response = httpx.put(
                url=f"{self.base_url}/chatbot/message-pairs/{message_pair_id}/feedbacks/",
                json={
                    "rating": rating,
                    "comment": comments,
                },
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            self.logger.success(f"[FEEDBACK] Feedback sent successfully")
            return True
        except Exception:
            self.logger.exception(f"[FEEDBACK] Error on sending feedback:")
            return False

    def delete_thread(self, access_token: str, thread_id: UUID) -> bool:
        """Soft delete a thread and hard delete all its checkpoints.

        Args:
            access_token (str): User access token.
            thread_id (UUID): Thread unique identifier.

        Returns:
            bool: Whether the operation succeeded or not.
        """
        self.logger.info(f"""[CLEAR] Clearing assistant memory""")

        try:
            response = httpx.delete(
                url=f"{self.base_url}/chatbot/threads/{thread_id}/",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            self.logger.success(f"[CLEAR] Assistant memory cleared successfully")
            return True
        except Exception:
            self.logger.exception("[CLEAR] Error on clearing assistant memory:")
            return False
