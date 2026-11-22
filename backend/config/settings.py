import os

APP_NAME = os.environ.get("APP_NAME", "NOVA AI")

VERSION = os.environ.get("VERSION", "1.0.0")

OWNER_NAME = os.environ.get("OWNER_NAME", "Roshan")

DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

# Use env var for memory file path (for deployment), fallback to local
MEMORY_FILE = os.environ.get("MEMORY_FILE_PATH", "memory.json")

LOG_FILE = os.environ.get("LOG_FILE_PATH", "logs/astra.log")

MAX_HISTORY = int(os.environ.get("MAX_HISTORY", "20"))
