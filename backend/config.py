import os

SECRET_STRING = os.environ.get("SECRET_STRING", "")

# Gemini / Google Generative AI key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Prompts stored in environment variables (<=100 chars recommended)
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT", "")
USER_PROMPT = os.environ.get("USER_PROMPT", "")

# Timeouts (seconds)
PLAYWRIGHT_NAV_TIMEOUT = int(os.environ.get("PLAYWRIGHT_NAV_TIMEOUT", "60"))
SOLVE_TOTAL_TIMEOUT = int(os.environ.get("SOLVE_TOTAL_TIMEOUT", "160"))  # must be < 180
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "30"))
