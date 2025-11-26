import os
import dotenv

dotenv.load_dotenv()

# API variables
API_HOST = os.environ["API_HOST"]
API_PORT = os.environ["API_PORT"]
BASE_URL = f"http://{API_HOST}:{API_PORT}" # Base API URL

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
