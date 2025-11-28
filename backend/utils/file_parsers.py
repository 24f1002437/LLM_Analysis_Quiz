import tempfile
import pandas as pd
import pdfplumber
from typing import Dict, Any
import os
from PIL import Image, ImageOps
import wave
import contextlib
import google.generativeai as genai  # Gemini SDK
import base64
import io

# Configure Gemini (requires GEMINI_API_KEY in env)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Maximum allowed file size (Safety for HF Spaces)
MAX_FILE_SIZE = 30 * 1024 * 1024  # 30 MB

# Correct MIME mapping
AUDIO_MIME_MAP = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "ogg": "audio/ogg",
    "flac": "audio/flac"
}


# ---------------------------
# CSV Parser
# ---------------------------
def parse_csv(path: str):
    try:
        df = pd.read_csv(path, sep=None, engine="python")  # auto-detect delimiter
        return {
            "type": "csv",
            "columns": df.columns.tolist(),
            "rows": df.to_dict(orient="records")
        }
    except Exception as e:
        return {"type": "csv", "error": f"CSV parse failed: {str(e)}"}


# ---------------------------
# XLSX Parser (all sheets)
# ---------------------------
def parse_xlsx(path: str):
    try:
        sheets = pd.read_excel(path, sheet_name=None)  # dict of sheets
        parsed = {}
        for name, df in sheets.items():
            parsed[name] = {
                "columns": df.columns.tolist(),
                "rows": df.to_dict(orient="records")
            }
        return {"type": "xlsx", "sheets": parsed}
    except Exception as e:
        return {"type": "xlsx", "error": f"XLSX parse failed: {str(e)}"}


# ---------------------------
# PDF Parser
# ---------------------------
def parse_pdf(path: str):
    try:
        texts = []
        tables = []

        with pdfplumber.open(path) as pdf:
            for p in pdf.pages:
                texts.append(p.extract_text() or "")

                tbl = p.extract_table()
                if tbl:
                    tables.append(tbl)

        return {
            "type": "pdf",
            "pages": len(texts),
            "texts": texts,
            "tables": tables
        }

    except Exception as e:
        return {"type": "pdf", "error": f"Failed to parse PDF: {str(e)}"}


# ---------------------------
# Image Parser (with EXIF fix)
# ---------------------------
def parse_image(path: str):
    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)  # Fix rotated images
            width, height = img.size

            # Optional: Return thumbnail as base64
            buf = io.BytesIO()
            img.thumbnail((256, 256))
            img.save(buf, format="PNG")
            thumb_b64 = base64.b64encode(buf.getvalue()).decode()

            return {
                "type": "image",
                "format": img.format,
                "mode": img.mode,
                "size": (width, height),
                "thumbnail_base64": thumb_b64
            }

    except Exception as e:
        return {"type": "image", "error": f"Failed to parse image: {str(e)}"}


# ---------------------------
# Audio Parser + Gemini Transcription
# ---------------------------
def parse_audio(path: str):
    info = {}

    ext = os.path.splitext(path)[1][1:].lower()
    mime = AUDIO_MIME_MAP.get(ext, f"audio/{ext}")

    # WAV metadata
    try:
        if ext == "wav":
            with contextlib.closing(wave.open(path, 'rb')) as wf:
                info.update({
                    "channels": wf.getnchannels(),
                    "sample_width": wf.getsampwidth(),
                    "framerate": wf.getframerate(),
                    "frames": wf.getnframes(),
                    "duration_sec": wf.getnframes() / wf.getframerate(),
                })
        else:
            info.update({
                "format": ext,
                "size": os.path.getsize(path)
            })
    except Exception as e:
        info.update({"audio_metadata_error": str(e)})

    # Transcription
    try:
        with open(path, "rb") as f:
            audio_bytes = f.read()

        resp = genai.audio.transcribe(
            model="models/gemini-2.5-flash",
            audio=audio_bytes,
            audio_format=ext
        )
        transcription = resp.text

    except Exception as e:
        transcription = f"Transcription failed: {str(e)}"

    info.update({
        "type": "audio",
        "mime": mime,
        "transcription": transcription
    })
    return info


# ---------------------------
# Main File Dispatcher
# ---------------------------
def parse_file_bytes(content: bytes, filename_hint: str):
    # File size check
    if len(content) > MAX_FILE_SIZE:
        return {"error": "File too large"}

    ext = os.path.splitext(filename_hint)[1].lower()

    # Create temp file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(content)
    tmp.flush()
    tmp.close()

    try:
        if ext == ".csv":
            return parse_csv(tmp.name)

        if ext in [".xls", ".xlsx"]:
            return parse_xlsx(tmp.name)

        if ext == ".pdf":
            return parse_pdf(tmp.name)

        if ext in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
            return parse_image(tmp.name)

        if ext in [".wav", ".mp3", ".ogg", ".flac"]:
            return parse_audio(tmp.name)

        # fallback generic CSV try
        try:
            return parse_csv(tmp.name)
        except Exception:
            return {"type": "binary", "size": os.path.getsize(tmp.name)}

    finally:
        try:
            os.unlink(tmp.name)
        except:
            pass
