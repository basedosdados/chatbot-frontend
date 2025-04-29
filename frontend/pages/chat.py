from frontend.api import APIClient
from frontend.components.chat_page import ChatPage
from frontend.utils import BASE_URL


api = APIClient(BASE_URL)

chat_page = ChatPage(api=api, title="Chat")

chat_page.render()
