#!/usr/bin/env python3
"""
Jetson Nano adaptation of the original Raspberry Pi + Arduino camera loop.
- Replaces Picamera2 with OpenCV (GStreamer nvarguscamerasrc if available, USB fallback).
- Replaces RPi.GPIO with Jetson.GPIO.
- Keeps function names and high-level behavior as close as possible.
- Optionally drives a SERVO directly via PWM (set SERVO_PWM_MODE=True) instead of signaling an Arduino.
"""
import os
import time
from collections import deque
import numpy as np
import cv2
import requests

# ---- Jetson GPIO (drop-in for RPi.GPIO API) ----
import Jetson.GPIO as GPIO

# ---- dotenv for settings + store ----
from dotenv import load_dotenv, set_key

# ================== USER SETTINGS ==================
# Glare logic
THRESHOLD   = 55.0
HYSTERESIS  = 10.0
REQ_FRAMES  = 4
COOLDOWN_S  = 0.8
PRINT_EVERY = 20

# ---- Threshold monitoring ----
API_COOLDOWN = 5.0  # minimum seconds between API calls

# ---- Jetson signal pins ----
# NOTE: These are BCM-like identifiers as with RPi.GPIO API.
# On Jetson, verify your header mapping. You may change these if needed.
SIGNAL_PIN  = 23   # used for 'down/up' signal or servo PWM (if SERVO_PWM_MODE=True)
STROBE_PIN  = 24   # optional LED/strobe (digital HIGH pulse)
USE_STROBE  = False

# Servo (optional) — if True, we'll generate PWM to move a small hobby servo
SERVO_PWM_MODE = False          # keep False to use digital HIGH/LOW like before
SERVO_FREQ_HZ  = 50             # 50Hz servo PWM
SERVO_UP_US    = 1000           # ~1.0ms pulse (tweak per servo)
SERVO_DOWN_US  = 2000           # ~2.0ms pulse (tweak per servo)
SERVO_PULSE_MS = 600            # how long to drive the servo at the new position (ms)

# Exposure/white balance (best-effort; CSI control is limited via OpenCV)
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

# Envs
SETTINGS_ENV = "settings.env"
STORE_ENV    = "store.env"

# Flask server URL
FLASK_URL = "http://localhost:5000/recommend"

# Settings reload interval
SETTINGS_RELOAD_INTERVAL = 2.0

# ======== Camera helpers (GStreamer for CSI, fallback to USB) ========
def gstreamer_pipeline(
    capture_width=1280, capture_height=720,
    display_width=640, display_height=480,
    framerate=30, flip_method=0
):
    return (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), "
        f"width={capture_width}, height={capture_height}, format=NV12, framerate={framerate}/1 ! "
        f"nvvidconv flip-method={flip_method} ! "
        f"video/x-raw, width={display_width}, height={display_height}, format=BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=BGR ! appsink"
    )

def make_camera():
    # Try CSI via GStreamer first
    cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        # Fallback to USB cam /dev/video0
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not initialize camera (CSI or USB).")
    return cap

def setup_signal_pins():
    GPIO.setmode(GPIO.BCM)
    if SERVO_PWM_MODE:
        GPIO.setup(SIGNAL_PIN, GPIO.OUT, initial=GPIO.LOW)
    else:
        GPIO.setup(SIGNAL_PIN, GPIO.OUT, initial=GPIO.LOW)
    if USE_STROBE:
        GPIO.setup(STROBE_PIN, GPIO.OUT, initial=GPIO.LOW)

# Global PWM handle (created lazily)
_servo_pwm = None

def _servo_start():
    global _servo_pwm
    if _servo_pwm is None:
        _servo_pwm = GPIO.PWM(SIGNAL_PIN, SERVO_FREQ_HZ)
        _servo_pwm.start(0)

def _us_to_duty(us, freq_hz):
    period_us = 1_000_000.0 / float(freq_hz)
    duty_pct  = (us / period_us) * 100.0
    return max(0.0, min(100.0, duty_pct))

def notify_arduino(state_down: bool):
    """Repurposed:
    - If SERVO_PWM_MODE=False: behaves like original digital signal for Arduino (HIGH when down).
    - If SERVO_PWM_MODE=True : drive hobby servo to UP/DOWN positions directly.
    """
    if SERVO_PWM_MODE:
        _servo_start()
        pulse_us = SERVO_DOWN_US if state_down else SERVO_UP_US
        duty_pct = _us_to_duty(pulse_us, SERVO_FREQ_HZ)
        _servo_pwm.ChangeDutyCycle(duty_pct)
        # drive for a short burst to move the horn
        time.sleep(SERVO_PULSE_MS / 1000.0)
        # stop driving (some servos prefer holding torque; if so, comment this line)
        _servo_pwm.ChangeDutyCycle(0.0)
    else:
        GPIO.output(SIGNAL_PIN, GPIO.HIGH if state_down else GPIO.LOW)

    if USE_STROBE:
        GPIO.output(STROBE_PIN, GPIO.HIGH)
        time.sleep(0.01)
        GPIO.output(STROBE_PIN, GPIO.LOW)

def lock_current_exposure_and_wb(_cap):
    """Best-effort stub on Jetson when using OpenCV.
    CSI controls aren't uniformly exposed via cv2; advanced control is possible using
    nvarguscamerasrc properties or v4l2-ctl outside of Python. Here we no-op to keep behavior similar.
    """
    # You can experiment with cap.set(cv2.CAP_PROP_EXPOSURE, value) on USB webcams.
    # For CSI, consider using a static GStreamer pipeline with manual exposure if needed.
    return None, None, None

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
    try:
        set_key(STORE_ENV, "BRIGHTNESS", f"{normalized_brightness:.6f}")
    except Exception as e:
        print(f"✗ Error updating store: {e}")

def trigger_recommend_api():
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
    load_dotenv(SETTINGS_ENV, override=True)
    return float(os.getenv("BRIGHTNESS_THRESHOLD", 0.5))

def main():
    setup_signal_pins()
    cap = make_camera()

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

    last_api_call = 0.0
    was_above_threshold = False

    last_settings_reload = 0.0
    brightness_threshold = load_brightness_threshold()

    print("\\n" + "="*60)
    print("JETSON CAMERA BRIGHTNESS MONITOR (HOT-RELOAD ENABLED)")
    print("="*60)
    print(f"Settings reload: every {SETTINGS_RELOAD_INTERVAL}s")
    print(f"Initial brightness threshold: {brightness_threshold}")
    print(f"API cooldown: {API_COOLDOWN}s")
    print("="*60 + "\\n")

    try:
        while True:
            now = time.time()
            if now - last_settings_reload > SETTINGS_RELOAD_INTERVAL:
                brightness_threshold = load_brightness_threshold()
                last_settings_reload = now

            ret, frame = cap.read()
            if not ret or frame is None:
                print("✗ Camera frame grab failed; retrying...")
                time.sleep(0.05)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            roi = gray[h//3:2*h//3, w//3:2*w//3]
            inst_luma = float(np.mean(roi))

            avg_ema = 0.6 * avg_ema + 0.4 * inst_luma
            lum_buf.append((now, inst_luma))

            normalized_brightness = avg_ema / 255.0
            update_store_brightness(normalized_brightness)

            is_above_threshold = normalized_brightness > brightness_threshold
            crossed_threshold = is_above_threshold != was_above_threshold

            if crossed_threshold and (now - last_api_call) > API_COOLDOWN:
                print(f"\\n🔔 Brightness threshold crossed! {normalized_brightness:.3f} vs {brightness_threshold:.3f}")
                trigger_recommend_api()
                last_api_call = now

            was_above_threshold = is_above_threshold

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
                lock_current_exposure_and_wb(cap)
                last_info = "LOCKED exposure/WB (best-effort)"
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
        try:
            if _servo_pwm is not None:
                _servo_pwm.stop()
        except Exception:
            pass
        GPIO.cleanup()
        cap.release()
        print("\\n✓ Jetson camera processor stopped")

if __name__ == "__main__":
    main()
