import json
from config import GEMINI_API_KEY
import google.generativeai as genai

if not GEMINI_API_KEY:
    # we don't raise here to allow server to start locally if missing
    pass
else:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL = genai.GenerativeModel("models/gemini-2.5-flash")

def ask_gemini(prompt: str, max_tokens: int = 1024) -> str:
    """
    Send prompt to Gemini and return text output.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set in environment")

    response = MODEL.generate_content(prompt)
    # Newer SDK returns .text; fallback to inspect attributes
    text = getattr(response, "text", None)
    if text:
        return str(text)
    # fallback: try response.response or response.output
    try:
        # attempt to get nested fields
        return str(response.response.get("output", ""))
    except Exception:
        return str(response)
