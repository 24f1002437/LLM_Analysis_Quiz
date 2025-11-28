import time
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import SECRET_STRING
from solver import solve_quiz_url

# -----------------------------------------
# Flask App
# -----------------------------------------
app = Flask(__name__)

# Optional: Enable CORS (useful for HF Spaces or frontend)
CORS(app)

logging.basicConfig(level=logging.INFO)


# -----------------------------------------
# Health Check
# -----------------------------------------
@app.get("/")
def home():
    return "LLM Quiz Project (API running)"


# -----------------------------------------
# Main Quiz Solve Endpoint
# -----------------------------------------
@app.post("/api/quiz")
def quiz_endpoint():

    # Check JSON content-type
    if not request.is_json:
        return jsonify({"error": "content-type must be application/json"}), 400

    # Parse JSON
    try:
        payload = request.get_json(force=True)
    except Exception as e:
        return jsonify({"error": "invalid json", "exception": str(e)}), 400

    email   = payload.get("email")
    secret  = payload.get("secret")
    url     = payload.get("url")

    # Validate required fields
    if not email or not secret or not url:
        return jsonify({"error": "missing fields", 
                        "required": ["email", "secret", "url"]}), 400

    # Validate secret
    if secret != SECRET_STRING:
        return jsonify({"error": "invalid secret"}), 403

    # -----------------------------------------
    # Run Solver
    # -----------------------------------------
    start = time.time()

    try:
        result = solve_quiz_url(url)
    except Exception as e:
        logging.exception("Solver crashed")
        return jsonify({
            "error": "solver_error",
            "exception": str(e)
        }), 500

    elapsed = round(time.time() - start, 4)

    # -----------------------------------------
    # Return Response
    # -----------------------------------------
    return jsonify({
        "ok": True,
        "email": email,
        "url": url,
        "result": result,
        "elapsed_seconds": elapsed
    }), 200


# -----------------------------------------
# Local Debug Run
# -----------------------------------------
if __name__ == "__main__":
    # Important for Hugging Face Space: host must be 0.0.0.0
    app.run(host="0.0.0.0", port=5000, debug=False)
