import tempfile
import pandas as pd
import pdfplumber
from typing import Dict, Any
import os

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

def parse_file_bytes(content: bytes, filename_hint: str):
    # Save to temp file and parse based on extension
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
        # fallback: try csv then raw text
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
