from flask import Flask, request, jsonify
from flask_cors import CORS
from config import SECRET_STRING
from solver import solve_quiz_url
import time
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

@app.get("/")
def home():
    return "LLM Quiz API running"

@app.post("/api/quiz")
def quiz_endpoint():
    if not request.is_json:
        return jsonify({"error": "Content-type must be application/json"}), 400

    try:
        payload = request.get_json(force=True)
    except Exception as e:
        return jsonify({"error": "invalid json", "exception": str(e)}), 400

    email = payload.get("email")
    secret = payload.get("secret")
    url = payload.get("url")

    if not email or not secret or not url:
        return jsonify({"error": "missing fields"}), 400

    if secret != SECRET_STRING:
        return jsonify({"error": "invalid secret"}), 403

    start = time.time()
    try:
        result = solve_quiz_url(url)
    except Exception as e:
        logging.exception("Solver crashed")
        return jsonify({"error": "solver_error", "exception": str(e)}), 500

    elapsed = round(time.time() - start, 4)
    return jsonify({
        "ok": True,
        "email": email,
        "url": url,
        "result": result,
        "elapsed_seconds": elapsed
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
