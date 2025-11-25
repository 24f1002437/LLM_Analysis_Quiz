from flask import Flask, request, jsonify
from config import SECRET_STRING, SYSTEM_PROMPT, USER_PROMPT
from utils.gemini_client import ask_gemini

app = Flask(__name__)

@app.post("/api/quiz")
def quiz():
    data = request.json

    # Verify secret
    if data.get("secret") != SECRET_STRING:
        return jsonify({"error": "Unauthorized"}), 403

    # Quiz question from evaluator
    question = data.get("question")

    # Build final LLM prompt
    full_prompt = f"""
System Prompt (Student): {SYSTEM_PROMPT}

User Prompt (Student): {USER_PROMPT}

Task from evaluator:
{question}
"""

    result = ask_gemini(full_prompt)
    return jsonify({"answer": result})
