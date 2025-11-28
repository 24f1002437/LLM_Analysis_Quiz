import json
from typing import Optional, Union, Dict, Any
from config import GEMINI_API_KEY
import google.generativeai as genai

# ---------------------------
# Gemini Configuration
# ---------------------------
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    # Allow app to run; model calls will still fail if key missing
    print("⚠ Warning: GEMINI_API_KEY is not set.")

MODEL_NAME = "models/gemini-2.5-flash"
MODEL = genai.GenerativeModel(MODEL_NAME)

# ---------------------------
# Basic Text Generation
# ---------------------------
def ask_gemini(prompt: str, max_tokens: int = 1024) -> str:
    """
    Send a text prompt to Gemini & return the response string.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    try:
        response = MODEL.generate_content(
            prompt, 
            generation_config={"max_output_tokens": max_tokens}
        )
    except Exception as e:
        return f"[Gemini Error] {str(e)}"

    # Extract text safely
    text = getattr(response, "text", None)
    if text:
        return text

    # fallback: investigate nested fields
    try:
        return str(response.response.get("candidates", [{}])[0].get("content", ""))
    except Exception:
        return str(response)

# ---------------------------
# Streaming Support (Optional)
# ---------------------------
def ask_gemini_stream(prompt: str):
    """
    Stream Gemini output chunk by chunk (useful for long responses).
    Yields text chunks.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    try:
        stream = MODEL.generate_content(
            prompt,
            stream=True
        )
        for chunk in stream:
            if hasattr(chunk, "text") and chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"[Streaming error: {str(e)}]"

# ---------------------------
# Image Generation
# ---------------------------
def generate_image(prompt: str, size: str = "1024x1024") -> bytes:
    """
    Generate an image with Gemini & return raw bytes.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    try:
        result = genai.images.generate(
            model="models/gemini-2.0-flash-lite-preview-02-05",
            prompt=prompt,
            size=size,
        )
        # result.images[0].image_bytes contains raw bytes
        return result.images[0].image_bytes
    except Exception as e:
        raise RuntimeError(f"Image generation failed: {e}")

# ---------------------------
# Audio Transcription
# ---------------------------
def transcribe_audio_bytes(audio_bytes: bytes, audio_format: str) -> str:
    """
    Transcribe audio using Gemini 2.5 Flash.
    audio_format must be: wav, mp3, flac, ogg
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    try:
        resp = genai.audio.transcribe(
            model=MODEL_NAME,
            audio=audio_bytes,
            audio_format=audio_format
        )
        return getattr(resp, "text", "") or "Transcription unavailable"
    except Exception as e:
        return f"[Transcription failed: {str(e)}]"

# ---------------------------
# Multimodal: Text + File Metadata
# ---------------------------
def ask_gemini_with_file(prompt: str, file_metadata: Dict[str, Any]) -> str:
    """
    Use Gemini for reasoning on a file (CSV/XLSX/PDF/Image/Audio).
    You pass a dict like file_parsers.py returns.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    message = {
        "prompt": prompt,
        "file_info": file_metadata
    }

    try:
        response = MODEL.generate_content(json.dumps(message))
    except Exception as e:
        return f"[Gemini Error] {str(e)}"

    return getattr(response, "text", "") or str(response)

    
