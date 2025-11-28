import tempfile
import pandas as pd
import pdfplumber
from typing import Dict, Any
import os
from PIL import Image
import wave
import contextlib
import genai  # Gemini SDK

# Configure Gemini (make sure GEMINI_API_KEY is set in env)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def parse_csv(path: str):
    df = pd.read_csv(path)
    return {"type": "csv", "columns": df.columns.tolist(), "rows": df.to_dict(orient="records")}

def parse_xlsx(path: str):
    df = pd.read_excel(path)
    return {"type": "xlsx", "columns": df.columns.tolist(), "rows": df.to_dict(orient="records")}

def parse_pdf(path: str):
    tables = []
    texts = []
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            texts.append(p.extract_text() or "")
            tbl = p.extract_table()
            if tbl:
                tables.append(tbl)
    return {"type": "pdf", "pages": len(texts), "texts": texts, "tables": tables}

def parse_image(path: str):
    with Image.open(path) as img:
        return {"type": "image", "format": img.format, "mode": img.mode, "size": img.size}

def parse_audio(path: str):
    info = {}
    # WAV metadata
    if path.lower().endswith(".wav"):
        with contextlib.closing(wave.open(path, 'rb')) as wf:
            info = {
                "channels": wf.getnchannels(),
                "sample_width": wf.getsampwidth(),
                "framerate": wf.getframerate(),
                "frames": wf.getnframes(),
                "duration_sec": wf.getnframes() / wf.getframerate()
            }
    else:
        info = {"format": os.path.splitext(path)[1][1:], "size": os.path.getsize(path)}

    # Transcribe using Gemini
    with open(path, "rb") as f:
        audio_bytes = f.read()
    try:
        resp = genai.audio.transcribe(
            model="models/gemini-2.5-flash",  # or your preferred model
            audio=audio_bytes,
            audio_format=os.path.splitext(path)[1][1:]  # mp3, wav, etc.
        )
        transcription = resp.text
    except Exception as e:
        transcription = f"Transcription failed: {str(e)}"

    info.update({"type": "audio", "transcription": transcription})
    return info

def parse_file_bytes(content: bytes, filename_hint: str):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename_hint)[1] or "")
    tmp.write(content)
    tmp.flush()
    tmp.close()
    ext = os.path.splitext(filename_hint)[1].lower()
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
        # fallback
        try:
            return parse_csv(tmp.name)
        except Exception:
            with open(tmp.name, "rb") as fh:
                return {"type": "binary", "size": os.path.getsize(tmp.name)}
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
