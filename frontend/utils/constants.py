import os

import dotenv

dotenv.load_dotenv()

# Website API variables
WEBSITE_HOST = os.environ["WEBSITE_HOST"]
WEBSITE_PORT = os.environ["WEBSITE_PORT"]
BASE_WEBSITE_URL = f"http://{WEBSITE_HOST}:{WEBSITE_PORT}"

# Chatbot API variables
CHATBOT_HOST = os.environ["CHATBOT_HOST"]
CHATBOT_PORT = os.environ["CHATBOT_PORT"]
BASE_CHATBOT_URL = f"http://{CHATBOT_HOST}:{CHATBOT_PORT}"

# Set log level
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

# Whether the full stacktrace should be shown when logging exceptions
LOG_BACKTRACE = os.getenv("LOG_BACKTRACE", "true").lower() == "true"

# Whether exception traces should display the variables values,
# for debugging. Should be se to False in production
LOG_DIAGNOSE = os.getenv("LOG_DIAGNOSE", "false").lower() == "true"

# Whether the messages to be logged should first pass through
# a multiprocessing-safe queue before reaching the sink
LOG_ENQUEUE = os.getenv("LOG_ENQUEUE", "true").lower() == "true"

# Key for storing an empty chat page in the session state
NEW_CHAT = "new_chat"
