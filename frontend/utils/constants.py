# API variables
API_HOST = "api-development-service"
API_PORT = 80
BASE_URL = f"http://{API_HOST}:{API_PORT}" # Base API URL

# Set log sink.
LOG_FILE_PATH = "/var/log/chatbot/frontend.log"

# Set log level.
LOG_LEVEL = "DEBUG"

# Rotate logs daily.
LOG_ROTATION = "1 day"

# Don't delete old logs.
LOG_RETENTION = None

# Whether the full stacktrace should be shown when logging exceptions.
LOG_BACKTRACE = True

# Whether exception traces should display the variables values,
# for debugging. Should be se to False in production.
LOG_DIAGNOSE = False

# Whether the messages to be logged should first pass through
# a multiprocessing-safe queue before reaching the sink.
LOG_ENQUEUE = True

# Key for storing an empty chat page in the session state.
NEW_CHAT = "new_chat"
