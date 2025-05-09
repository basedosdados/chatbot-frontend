from uuid import UUID

import requests
from loguru import logger

from frontend.datatypes import MessagePair, Thread, UserMessage

ERROR_MESSAGES = {
    "DEFAULT": "Algo deu errado. Por favor, tente novamente mais tarde.",
    "USERNAME_TAKEN": "O usuário escolhido está indisponível.",
    "ALREADY_VERIFIED": "O email fornecido já está verificado.",
    "TOKEN_EXPIRED": "O link de verificação expirou. Por favor, realize o cadastro novamente.",
    "TOKEN_NOT_FOUND": "Token de verificação não encontrado. Por favor, realize o cadastro novamente.",
    "USER_NOT_FOUND": "Usuário não encontrado. Por favor, realize o cadastro novamente.",
}

def get_error_message(response: requests.Response) -> str:
    error_detail = response.json().get("detail")

    if isinstance(error_detail, dict):
        error_code = error_detail.get("code", "DEFAULT")

    return ERROR_MESSAGES[error_code]

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.logger = logger.bind(classname=self.__class__.__name__)

    def authenticate(self, username: str, password: str) -> tuple[str|None, str]:
        """Send a post request to the authentication endpoint

        Args:
            username (str): The username
            password (str): The password

        Returns:
            tuple[str|None, str]: A tuple containing the access token and a status message
        """
        access_token = None

        message = "Ops! Ocorreu um erro durante o login. Por favor, tente novamente."

        try:
            response = requests.post(
                url=f"{self.base_url}/chatbot/token/",
                data={
                    "email": username,
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
        except requests.exceptions.HTTPError:
            if response.status_code == requests.codes.unauthorized:
                self.logger.warning(f"[LOGIN] Invalid credentials")
                message = "Usuário ou senha incorretos."
            else:
                self.logger.exception(f"[LOGIN] HTTP error:")
        except requests.exceptions.RequestException:
            self.logger.exception(f"[LOGIN] Login error:")

        return access_token, message

    def create_thread(self, access_token: str) -> UUID|None:
        """Create a thread

        Args:
            access_token (str): User access token

        Returns:
            UUID|None: Thread unique identifier if the thread was created successfully. None otherwise
        """
        self.logger.info("[THREAD] Creating thread")

        try:
            response = requests.post(
                url=f"{self.base_url}/chatbot/threads/",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            thread = Thread(**response.json())
            self.logger.success(f"[MESSAGE] Thread created successfully for user {thread.id}")
            return thread.id
        except requests.RequestException:
            self.logger.exception(f"[MESSAGE] Error on thread creation:")
            return None

    def send_message(self, access_token: str, message: str, thread_id: UUID) -> MessagePair:
        """Send a user message

        Args:
            access_token (str): User access token
            message (str): User message
            thread_id (UUID): Thread unique identifier

        Returns:
            MessagePair:
                A MessagePair object containing:
                    - id: unique identifier
                    - thread: thread unique identifier
                    - model_uri: assistant's model URI
                    - user_message: user message
                    - assistant_message: assistant message
                    - generated_queries: generated sql queries
                    - generated_chart: generated data for visualization
                    - created_at: message pair creation timestamp
        """
        user_message = UserMessage(content=message)

        self.logger.info(f"[MESSAGE] Sending message {user_message.id} in thread {thread_id}")

        try:
            response = requests.post(
                url=f"{self.base_url}/chatbot/threads/{thread_id}/messages/",
                json=user_message.model_dump(mode="json"),
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            self.logger.success(f"[MESSAGE] User message sent successfully")
            message_pair = response.json()
        except requests.RequestException:
            self.logger.exception(f"[MESSAGE] Error on sending user message:")
            message_pair = {
                "thread": thread_id,
                "model_uri": "",
                "user_message": user_message.content,
                "assistant_message": "Ops, algo deu errado! Por favor, tente novamente. "\
                    "Se o problema persistir, avise-nos. Obrigado pela paciência!"
            }

        return MessagePair(**message_pair)

    def send_feedback(self, access_token: str, message_pair_id: UUID, rating: int, comments: str) -> bool:
        """Send a feedback

        Args:
            access_token (str): User access token
            message_pair_id (UUID): The message pair unique identifier
            rating (int): The rating (0 or 1)
            comments (str): The comments

        Returns:
            bool: Whether the operation succeeded or not
        """
        feedback_meaning = "positive" if rating else "negative"

        self.logger.info(f"[FEEDBACK] Sending {feedback_meaning} feedback for message pair {message_pair_id}")

        try:
            response = requests.put(
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
        except requests.exceptions.RequestException:
            self.logger.exception(f"[FEEDBACK] Error on sending feedback:")
            return False

    def clear_thread(self, access_token: str, thread_id: UUID) -> bool:
        """Clear a thread

        Args:
            access_token (str): User access token
            thread_id (UUID): Thread unique identifier

        Returns:
            bool: Whether the operation succeeded or not
        """
        self.logger.info(f"""[CLEAR] Clearing assistant memory""")

        try:
            response = requests.delete(
                url=f"{self.base_url}/chatbot/checkpoints/{thread_id}/",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            self.logger.success(f"[CLEAR] Assistant memory cleared successfully")
            return True
        except requests.exceptions.RequestException:
            self.logger.exception("[CLEAR] Error on clearing assistant memory:")
            return False
