from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv, set_key
import json
import openai
import serial
from serial.tools import list_ports
import time
import glob

app = Flask(__name__)

# File paths
SETTINGS_ENV = "settings.env"
STORE_ENV = "store.env"

# -------- UART auto-detect (for Arduino LED control) --------
def open_serial():
    """Auto-detect and open serial connection to Arduino"""
    candidates = [
        '/dev/serial0', '/dev/ttyAMA0', '/dev/ttyS0',
        '/dev/ttyACM0', '/dev/ttyUSB0'
    ]
    detected = [p.device for p in list_ports.comports()]
    for c in candidates + detected:
        try:
            if c and (glob.glob(c) or c in detected):
                s = serial.Serial(c, baudrate=9600, timeout=1)
                print(f"[UART] Connected on {c}")
                time.sleep(2.0)  # Arduino reset guard
                s.reset_input_buffer()
                return s
        except Exception:
            pass
    print("[UART] No serial port available. Running without Arduino.")
    return None

ser = open_serial()

# Initialize .env files if they don't exist
def init_env_files():
    if not os.path.exists(SETTINGS_ENV):
        with open(SETTINGS_ENV, 'w') as f:
            f.write("""BRIGHTNESS_THRESHOLD=0.5
BACKGROUND_AUDIO=white_noise_calm
TARGET_PEAK=0.7
WHITE_NOISE_LEVEL=0.08
HIGHCUT=6000
LOWCUT=200
RATIO=4
THRESHOLD_DB=-20
AMPLITUDE_THRESHOLD=0.5
""")
    
    if not os.path.exists(STORE_ENV):
        with open(STORE_ENV, 'w') as f:
            f.write("""BRIGHTNESS=0.0
AMPLITUDE=0.0
""")

init_env_files()

# Load environment variables
load_dotenv(SETTINGS_ENV)
load_dotenv(STORE_ENV)

# Available patterns for GPT to choose from
AVAILABLE_AUDIO_PATTERNS = [
    "white_noise_calm",
    "white_noise_rain",
    "white_noise_ocean",
    "pink_noise_soft",
    "brown_noise_deep"
]

AVAILABLE_LIGHT_PATTERNS = [
    "steady_warm",
    "steady_cool",
    "breathing_slow",
    "breathing_fast",
    "pulse_gentle",
    "off"
]

# Map light patterns to RGB values (0-100 range)
LIGHT_PATTERN_RGB = {
    "steady_warm": (80, 40, 10),      # Warm orange
    "steady_cool": (10, 40, 80),      # Cool blue
    "breathing_slow": (50, 30, 20),   # Warm breathing
    "breathing_fast": (30, 50, 70),   # Cool breathing
    "pulse_gentle": (60, 50, 40),     # Neutral pulse
    "off": (0, 0, 0)                  # Off
}

# OpenAI setup
openai.api_key = ""

def send_rgb_to_arduino(r, g, b):
    """Send RGB values to Arduino in the format: !R.G.B#"""
    if not ser:
        return False
    try:
        # Ensure values are 0-100
        r = max(0, min(100, int(r)))
        g = max(0, min(100, int(g)))
        b = max(0, min(100, int(b)))
        
        frame = f"!{r}.{g}.{b}#".encode("ascii")
        ser.write(frame)
        ser.flush()
        print(f"✓ Sent to Arduino: R={r} G={g} B={b}")
        return True
    except Exception as e:
        print(f"✗ Arduino communication error: {e}")
        return False

@app.route("/")
def index():
    # Load current settings
    load_dotenv(SETTINGS_ENV, override=True)
    settings = {
        "brightness_threshold": float(os.getenv("BRIGHTNESS_THRESHOLD", 0.5)),
        "background_audio": os.getenv("BACKGROUND_AUDIO", "white_noise_calm"),
        "target_peak": float(os.getenv("TARGET_PEAK", 0.7)),
        "white_noise_level": float(os.getenv("WHITE_NOISE_LEVEL", 0.08)),
        "highcut": int(os.getenv("HIGHCUT", 6000)),
        "lowcut": int(os.getenv("LOWCUT", 200)),
        "ratio": int(os.getenv("RATIO", 4)),
        "threshold_db": int(os.getenv("THRESHOLD_DB", -20)),
        "amplitude_threshold": float(os.getenv("AMPLITUDE_THRESHOLD", 0.5))
    }
    return render_template("index.html", settings=settings)

@app.route("/update_settings", methods=["POST"])
def update_settings():
    """Update settings.env with new parameters from app"""
    try:
        data = request.get_json()
        
        # Valid settings keys
        valid_keys = [
            "BRIGHTNESS_THRESHOLD", "BACKGROUND_AUDIO", "TARGET_PEAK",
            "WHITE_NOISE_LEVEL", "HIGHCUT", "LOWCUT", "RATIO", "THRESHOLD_DB",
            "AMPLITUDE_THRESHOLD"
        ]
        
        # Update each setting in the .env file
        updated = {}
        for key, value in data.items():
            env_key = key.upper()
            if env_key in valid_keys:
                set_key(SETTINGS_ENV, env_key, str(value))
                updated[env_key] = value
        
        # Reload settings
        load_dotenv(SETTINGS_ENV, override=True)
        
        print(f"✓ Settings updated: {updated}")
        return jsonify({"success": True, "message": "Settings updated", "updated": updated})
    
    except Exception as e:
        print(f"✗ Error updating settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/recommend", methods=["POST"])
def recommend():
    """
    Get current store values (brightness, amplitude),
    query GPT for recommendations,
    update settings.env with new audio pattern,
    send light pattern to Arduino via serial
    """
    try:
        # 1. Load current values from store.env
        load_dotenv(STORE_ENV, override=True)
        brightness = float(os.getenv("BRIGHTNESS", 0.0))
        amplitude = float(os.getenv("AMPLITUDE", 0.0))
        
        print(f"\n{'='*60}")
        print(f"RECOMMEND REQUEST")
        print(f"{'='*60}")
        print(f"Current values - Brightness: {brightness:.3f}, Amplitude: {amplitude:.3f}")
        
        # 2. Build GPT prompt
        prompt = f"""Based on the current sensor readings, recommend the most soothing audio and light pattern.

Current readings:
- Brightness: {brightness:.3f} (0.0 = dark, 1.0 = very bright)
- Amplitude: {amplitude:.3f} (0.0 = silent, 1.0 = very loud)

Available audio patterns: {', '.join(AVAILABLE_AUDIO_PATTERNS)}
Available light patterns: {', '.join(AVAILABLE_LIGHT_PATTERNS)}

Consider:
- If brightness is high, use warmer/dimmer lights to reduce visual stimulation
- If brightness is low, can use brighter/cooler lights
- If amplitude is high (loud environment), use calming audio with more white noise
- If amplitude is low (quiet environment), use gentler audio
- Choose patterns that create a soothing, peaceful environment
- When both brightness and amplitude are normal (around 0.3-0.6), recommend baseline calming settings

Respond ONLY with valid JSON in this exact format:
{{"audio": "pattern_name", "light": "pattern_name", "reason": "brief explanation"}}"""

        # 3. Call GPT
        print("Calling OpenAI API...")
        response = openai.chatCompletions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a calming environment assistant. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        # 4. Parse GPT response
        gpt_response = response['choices'][0]['message']['content'].strip()
        print(f"GPT Response: {gpt_response}")
        
        # Extract JSON (in case GPT wraps it in markdown)
        if "```json" in gpt_response:
            gpt_response = gpt_response.split("```json")[1].split("```")[0].strip()
        elif "```" in gpt_response:
            gpt_response = gpt_response.split("```")[1].split("```")[0].strip()
        
        recommendation = json.loads(gpt_response)
        
        # Validate recommendations
        if recommendation.get("audio") not in AVAILABLE_AUDIO_PATTERNS:
            print(f"⚠ Invalid audio pattern '{recommendation.get('audio')}', defaulting to white_noise_calm")
            recommendation["audio"] = "white_noise_calm"
        if recommendation.get("light") not in AVAILABLE_LIGHT_PATTERNS:
            print(f"⚠ Invalid light pattern '{recommendation.get('light')}', defaulting to steady_warm")
            recommendation["light"] = "steady_warm"
        
        print(f"✓ Recommendation: {recommendation}")
        
        # 5. Update BACKGROUND_AUDIO in settings.env (audio processor will pick this up)
        set_key(SETTINGS_ENV, "BACKGROUND_AUDIO", recommendation["audio"])
        print(f"✓ Updated BACKGROUND_AUDIO to: {recommendation['audio']}")
        
        # 6. Send light pattern to Arduino via serial
        light_pattern = recommendation["light"]
        rgb = LIGHT_PATTERN_RGB.get(light_pattern, (50, 50, 50))
        
        if ser:
            send_rgb_to_arduino(rgb[0], rgb[1], rgb[2])
        else:
            print("⚠ Arduino not connected - skipping light control")
        
        print(f"{'='*60}\n")
        
        return jsonify({
            "success": True,
            "recommendation": recommendation,
            "current_values": {
                "brightness": brightness,
                "amplitude": amplitude
            },
            "light_rgb": rgb
        })
    
    except json.JSONDecodeError as e:
        print(f"✗ JSON parsing error: {e}")
        print(f"Raw response: {gpt_response}")
        return jsonify({"success": False, "error": "Invalid JSON from GPT", "raw_response": gpt_response}), 500
    
    except Exception as e:
        print(f"✗ Error in recommend: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/get_store", methods=["GET"])
def get_store():
    """Get current store values (for debugging/monitoring)"""
    try:
        load_dotenv(STORE_ENV, override=True)
        store_values = {
            "brightness": float(os.getenv("BRIGHTNESS", 0.0)),
            "amplitude": float(os.getenv("AMPLITUDE", 0.0))
        }
        return jsonify({"success": True, "store": store_values})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/get_settings", methods=["GET"])
def get_settings():
    """Get current settings (for debugging/monitoring)"""
    try:
        load_dotenv(SETTINGS_ENV, override=True)
        settings = {
            "brightness_threshold": float(os.getenv("BRIGHTNESS_THRESHOLD", 0.5)),
            "amplitude_threshold": float(os.getenv("AMPLITUDE_THRESHOLD", 0.5)),
            "background_audio": os.getenv("BACKGROUND_AUDIO", "white_noise_calm"),
            "target_peak": float(os.getenv("TARGET_PEAK", 0.7)),
            "white_noise_level": float(os.getenv("WHITE_NOISE_LEVEL", 0.08)),
            "highcut": int(os.getenv("HIGHCUT", 6000)),
            "lowcut": int(os.getenv("LOWCUT", 200)),
            "ratio": int(os.getenv("RATIO", 4)),
            "threshold_db": int(os.getenv("THRESHOLD_DB", -20))
        }
        return jsonify({"success": True, "settings": settings})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CALMING ENVIRONMENT CONTROL SERVER")
    print("="*60)
    print(f"Settings file: {SETTINGS_ENV}")
    print(f"Store file: {STORE_ENV}")
    print(f"Arduino serial: {'CONNECTED' if ser else 'NOT CONNECTED'}")
    if ser:
        print(f"  Port: {ser.port}")
        print(f"  Baud: {ser.baudrate}")
    print(f"OpenAI API: {'CONFIGURED' if os.getenv('OPENAI_API_KEY') else 'NOT CONFIGURED'}")
    print("="*60 + "\n")
    
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
    
