#!/usr/bin/env python3
import time
import os
from collections import deque
import numpy as np
import cv2
from picamera2 import Picamera2, Preview
import RPi.GPIO as GPIO
from dotenv import load_dotenv, set_key
import requests

# Load settings
SETTINGS_ENV = "settings.env"
STORE_ENV = "store.env"

# Flask server URL
FLASK_URL = "http://localhost:5000/recommend"

# Settings reload interval
SETTINGS_RELOAD_INTERVAL = 2.0

# ================== USER SETTINGS ==================
# Glare logic
THRESHOLD   = 55.0
HYSTERESIS  = 10.0
REQ_FRAMES  = 4
COOLDOWN_S  = 0.8
PRINT_EVERY = 20

# ---- Threshold monitoring ----
API_COOLDOWN = 5.0  # minimum seconds between API calls

# ---- Pi -> Arduino signal pins ----
SIGNAL_PIN  = 23
STROBE_PIN  = 24
USE_STROBE  = False

# Exposure/white balance
EXPOSURE_US       = 8000
ANALOGUE_GAIN     = 1.0
FIX_WHITE_BALANCE = True
WB_GAINS          = (1.8, 1.6)

# ---- Flashing/strobe detection ----
WIN_SEC                = 2.0
FLICKER_CHECK_EVERY    = 0.10
FLASH_BAND_LOW_HZ      = 3.0
FLASH_BAND_HIGH_HZ     = 15.0
FLICKER_FORCE_T        = 0.35
MIN_DOWN_HOLD_S        = 2.0
EXTRA_HOLD_PER_SCORE   = 3.0
BIAS_UPPER_PER_SCORE   = 8.0
BIAS_LOWER_PER_SCORE   = 4.0
# ===================================================

def setup_signal_pins():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SIGNAL_PIN, GPIO.OUT, initial=GPIO.LOW)
    if USE_STROBE:
        GPIO.setup(STROBE_PIN, GPIO.OUT, initial=GPIO.LOW)

def notify_arduino(state_down: bool):
    GPIO.output(SIGNAL_PIN, GPIO.HIGH if state_down else GPIO.LOW)
    if USE_STROBE:
        GPIO.output(STROBE_PIN, GPIO.HIGH)
        time.sleep(0.01)
        GPIO.output(STROBE_PIN, GPIO.LOW)

def make_camera():
    picam2 = Picamera2()
    picam2.start_preview(Preview.NULL)
    config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(config)

    controls = {
        "AeEnable": False,
        "ExposureTime": int(EXPOSURE_US),
        "AnalogueGain": float(ANALOGUE_GAIN),
        "NoiseReductionMode": 0,
    }
    if FIX_WHITE_BALANCE:
        controls.update({
            "AwbEnable": False,
            "ColourGains": (float(WB_GAINS[0]), float(WB_GAINS[1])),
        })
    picam2.set_controls(controls)
    picam2.start()
    return picam2

def lock_current_exposure_and_wb(picam2):
    picam2.set_controls({"AeEnable": True})
    if FIX_WHITE_BALANCE:
        picam2.set_controls({"AwbEnable": True})
    time.sleep(1.0)

    meta  = picam2.capture_metadata()
    exp   = meta.get("ExposureTime")
    gain  = meta.get("AnalogueGain")
    cgain = meta.get("ColourGains") if FIX_WHITE_BALANCE else None

    lock = {"AeEnable": False, "NoiseReductionMode": 0}
    if exp   is not None: lock["ExposureTime"] = int(exp)
    if gain  is not None: lock["AnalogueGain"]  = float(gain)
    if FIX_WHITE_BALANCE:
        lock["AwbEnable"] = False
        if cgain is not None:
            lock["ColourGains"] = (float(cgain[0]), float(cgain[1]))
    picam2.set_controls(lock)
    return exp, gain, cgain

def compute_flicker_score(ts, xs, band_lo=FLASH_BAND_LOW_HZ, band_hi=FLASH_BAND_HIGH_HZ):
    if len(xs) < 20:
        return 0.0
    dur = ts[-1] - ts[0]
    if dur < 0.8:
        return 0.0

    est_fs = max(10.0, min(50.0, len(xs) / dur))
    t_uniform = np.linspace(ts[0], ts[-1], int(est_fs * dur), endpoint=True)
    x_uniform = np.interp(t_uniform, ts, xs)

    x = x_uniform - np.mean(x_uniform)
    if np.max(np.abs(x)) < 1e-6:
        return 0.0
    w = np.hanning(len(x))
    X = np.fft.rfft(x * w)
    P = (np.abs(X) ** 2)
    freqs = np.fft.rfftfreq(len(x), 1.0 / est_fs)

    band = (freqs >= band_lo) & (freqs <= band_hi)
    num = float(np.sum(P[band]))
    den = float(np.sum(P[1:]) + 1e-9)
    score = num / den
    return float(np.clip(score, 0.0, 1.0))

def update_store_brightness(normalized_brightness):
    """Update BRIGHTNESS in store.env"""
    try:
        set_key(STORE_ENV, "BRIGHTNESS", f"{normalized_brightness:.6f}")
    except Exception as e:
        print(f"✗ Error updating store: {e}")

def trigger_recommend_api():
    """Call Flask /recommend endpoint"""
    try:
        response = requests.post(FLASK_URL, timeout=3)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                rec = result.get("recommendation", {})
                print(f"✓ API Response - Audio: {rec.get('audio')}, Light: {rec.get('light')}")
        else:
            print(f"✗ API error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"✗ API call failed: Flask server not reachable at {FLASK_URL}")
    except Exception as e:
        print(f"✗ API call failed: {e}")

def load_brightness_threshold():
    """Load brightness threshold from settings.env"""
    load_dotenv(SETTINGS_ENV, override=True)
    return float(os.getenv("BRIGHTNESS_THRESHOLD", 0.5))

def main():
    setup_signal_pins()
    picam2 = make_camera()

    current_state = "up"
    notify_arduino(state_down=False)

    last_flip = 0.0
    hi_cnt = lo_cnt = 0
    frame_idx = 0
    last_info = ""

    avg_ema = THRESHOLD

    lum_buf = deque(maxlen=1000)
    last_flicker_check = 0.0
    flicker_score = 0.0
    hold_until = 0.0

    # Threshold tracking
    last_api_call = 0.0
    was_above_threshold = False
    
    # Settings reload tracking
    last_settings_reload = 0.0
    brightness_threshold = load_brightness_threshold()

    print("\n" + "="*60)
    print("CAMERA BRIGHTNESS MONITOR (HOT-RELOAD ENABLED)")
    print("="*60)
    print(f"Settings reload: every {SETTINGS_RELOAD_INTERVAL}s")
    print(f"Initial brightness threshold: {brightness_threshold}")
    print(f"API cooldown: {API_COOLDOWN}s")
    print("="*60 + "\n")

    try:
        while True:
            # Reload settings if due
            now = time.time()
            if now - last_settings_reload > SETTINGS_RELOAD_INTERVAL:
                brightness_threshold = load_brightness_threshold()
                last_settings_reload = now

            frame = picam2.capture_array()
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            h, w = gray.shape
            roi = gray[h//3:2*h//3, w//3:2*w//3]
            inst_luma = float(np.mean(roi))

            avg_ema = 0.6 * avg_ema + 0.4 * inst_luma
            lum_buf.append((now, inst_luma))

            # Normalize brightness to 0-1 range (assuming 0-255 grayscale)
            normalized_brightness = avg_ema / 255.0
            
            # Update store.env continuously
            update_store_brightness(normalized_brightness)

            # Check threshold crossing
            is_above_threshold = normalized_brightness > brightness_threshold
            crossed_threshold = is_above_threshold != was_above_threshold
            
            if crossed_threshold and (now - last_api_call) > API_COOLDOWN:
                print(f"\n🔔 Brightness threshold crossed! {normalized_brightness:.3f} vs {brightness_threshold:.3f}")
                trigger_recommend_api()
                last_api_call = now
            
            was_above_threshold = is_above_threshold

            # flicker score
            if now - last_flicker_check >= FLICKER_CHECK_EVERY:
                ts = np.array([t for t,_ in lum_buf], dtype=np.float64)
                xs = np.array([x for _,x in lum_buf], dtype=np.float32)
                if len(ts) >= 2:
                    t0 = ts[-1] - WIN_SEC
                    keep = ts >= t0
                    ts, xs = ts[keep], xs[keep]
                flicker_score = compute_flicker_score(ts, xs)
                last_flicker_check = now

            upper = THRESHOLD + HYSTERESIS/2.0
            lower = THRESHOLD - HYSTERESIS/2.0
            upper_down = upper - BIAS_UPPER_PER_SCORE * flicker_score
            lower_up   = lower + BIAS_LOWER_PER_SCORE * flicker_score

            if flicker_score >= FLICKER_FORCE_T:
                hold = MIN_DOWN_HOLD_S + EXTRA_HOLD_PER_SCORE * flicker_score
                hold_until = max(hold_until, now + hold)
                if current_state != "down" and (now - last_flip) > 0.1:
                    notify_arduino(state_down=True)
                    current_state = "down"
                    last_flip = now

            if os.path.exists("/tmp/calibrate"):
                exp, gain, cg = lock_current_exposure_and_wb(picam2)
                last_info = f"LOCKED exp={int(exp) if exp else '?'}us gain={gain:.2f if gain else '?'}"
                os.remove("/tmp/calibrate")

            if current_state == "up":
                hi_cnt = hi_cnt + 1 if avg_ema >= upper_down else 0
                if hi_cnt >= REQ_FRAMES and (now - last_flip) > COOLDOWN_S:
                    notify_arduino(state_down=True)
                    current_state = "down"
                    last_flip = now
            else:
                can_release = now >= hold_until
                lo_cnt = lo_cnt + 1 if avg_ema <= lower_up else 0
                if can_release and lo_cnt >= REQ_FRAMES and (now - last_flip) > COOLDOWN_S:
                    notify_arduino(state_down=False)
                    current_state = "up"
                    last_flip = now

            if (frame_idx % PRINT_EVERY) == 0:
                if not last_info:
                    meta = picam2.capture_metadata()
                    exp  = meta.get("ExposureTime")
                    ag   = meta.get("AnalogueGain")
                    if exp and ag:
                        last_info = f"exp={int(exp)}us gain={ag:.2f}"
                print(f"Bright={normalized_brightness:.3f} ({avg_ema:.1f})  Flicker={flicker_score:.2f}  State={current_state}  Threshold={brightness_threshold:.3f}  {last_info}")
                last_info = ""
            frame_idx += 1

    except KeyboardInterrupt:
        pass
    finally:
        try:
            notify_arduino(state_down=False)
            time.sleep(0.1)
        except Exception:
            pass
        GPIO.cleanup()
        picam2.stop()
        print("\n✓ Camera processor stopped")

if __name__ == "__main__":
    main()
