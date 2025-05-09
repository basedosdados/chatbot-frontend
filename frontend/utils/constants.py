# API variables
BASE_URL = "http://localhost:8000" # Base API URL

# Log configuration variables
LOG_FILE_PATH = "/var/log/chatbot/frontend.log"
LOG_LEVEL = "DEBUG"
LOG_ROTATION = "1 day" # Rotate logs daily.
LOG_RETENTION = None   # Don't delete old logs.
LOG_BACKTRACE = True   # Whether the full stacktrace should be shown when logging exceptions.
LOG_DIAGNOSE = False   # Whether exception traces should display the variables values, for debugging. Should be se to False in production.
LOG_ENQUEUE = True     # Whether the messages to be logged should first pass through a multiprocessing-safe queue before reaching the sink.
