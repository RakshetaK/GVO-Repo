from flask import Flask, render_template, request, jsonify
import threading

app = Flask(__name__)

# Shared state (example compressor values)
settings = {
    "threshold_db": -20,
    "ratio": 4,
    "makeup_gain_db": 0,
}

@app.route("/")
def index():
    return render_template("index.html", settings=settings)

@app.route("/update", methods=["POST"])
def update():
    data = request.get_json()
    for key, value in data.items():
        if key in settings:
            settings[key] = float(value)
    print("Updated settings:", settings)
    return jsonify(success=True, settings=settings)

def run_web_server():
    app.run(host="0.0.0.0", port=5000, debug=False)
