import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
FMP_API_KEY = os.environ.get("FMP_API_KEY", "")

TOP_N = 5
WEIGHT_FUNDAMENTAL = 60
WEIGHT_TECHNICAL = 40
