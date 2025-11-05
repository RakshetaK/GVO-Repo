#!/usr/bin/env python3
"""
Tiny Flask server to keep parity with original architecture.
Reads the latest BRIGHTNESS from store.env and returns a simple recommendation.
"""
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os

SETTINGS_ENV = "settings.env"
STORE_ENV    = "store.env"

app = Flask(__name__)

def load_threshold():
    load_dotenv(SETTINGS_ENV, override=True)
    try:
        return float(os.getenv("BRIGHTNESS_THRESHOLD", "0.5"))
    except Exception:
        return 0.5

def read_brightness():
    load_dotenv(STORE_ENV, override=True)
    try:
        return float(os.getenv("BRIGHTNESS", "0.0"))
    except Exception:
        return 0.0

@app.route("/recommend", methods=["POST"])
def recommend():
    thr = load_threshold()
    bright = read_brightness()

    light = "visor_down" if bright > thr else "visor_up"
    # You can expand with audio logic here
    audio = "white_noise" if bright > thr else "none"

    return jsonify({
        "success": True,
        "recommendation": {
            "light": light,
            "audio": audio,
            "brightness": bright,
            "threshold": thr
        }
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
