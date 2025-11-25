import time
from flask import Flask, request, jsonify
from config import SECRET_STRING
from solver import solve_quiz_url
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.post("/api/quiz")
def quiz_endpoint():
    # Validate JSON
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid json"}), 400

    email = payload.get("email")
    secret = payload.get("secret")
    url = payload.get("url")

    if not (email and secret and url):
        return jsonify({"error": "missing fields"}), 400

    if secret != SECRET_STRING:
        return jsonify({"error": "invalid secret"}), 403

    # Secret matches -> we will solve the quiz and return a 200 with results
    start = time.time()
    try:
        result = solve_quiz_url(url)
    except Exception as e:
        return jsonify({"error": "solver_error", "exception": str(e)}), 500

    elapsed = time.time() - start
    response = {
        "ok": True,
        "email": email,
        "url": url,
        "result": result,
        "elapsed_seconds": elapsed
    }
    return jsonify(response), 200

@app.get("/")
def home():
    return "LLM Quiz Project "

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
