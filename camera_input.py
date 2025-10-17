
#!/usr/bin/env python3
import time
import os
from collections import deque
import numpy as np
import cv2
from picamera2 import Picamera2, Preview
import RPi.GPIO as GPIO

# ================== USER SETTINGS ==================
# Glare logic
THRESHOLD   = 55.0
HYSTERESIS  = 10.0
REQ_FRAMES  = 8            # consecutive frames before flipping (was 6)
COOLDOWN_S  = 1.5          # minimum time between flips (was 1.0)
PRINT_EVERY = 20           # print status every N frames (less console load)

# Servo (RPi.GPIO software PWM; drive-then-release to avoid jitter)
SERVO_PIN    = 18
PWM_HZ       = 50
MOVE_HOLD_MS = 300         # how long to drive the servo for each move
DUTY_MIN     = 5.5         # typical micro-servo safe range at 50 Hz
DUTY_MAX     = 9.3

# Map these two angles to your up/down positions
ANGLE_UP     = 0
ANGLE_DOWN   = 180

# Exposure/white balance (manual by default)
EXPOSURE_US       = 12000      # a bit longer -> steadier brightness
ANALOGUE_GAIN     = 1.2
FIX_WHITE_BALANCE = True
WB_GAINS          = (1.8, 1.6) # (R, B)

# ---- Flashing/strobe detection (NEW) ----
WIN_SEC                = 2.0    # seconds of luminance history to analyze
FLICKER_CHECK_EVERY    = 0.25   # compute score every X seconds
FLASH_BAND_LOW_HZ      = 3.0    # detectable with normal camera FPS
FLASH_BAND_HIGH_HZ     = 15.0
FLICKER_FORCE_T        = 0.35   # >= this -> force DOWN + latch
MIN_DOWN_HOLD_S        = 2.0    # minimum stay-down once flashing starts
EXTRA_HOLD_PER_SCORE   = 3.0    # extra hold (s) * flicker_score
BIAS_UPPER_PER_SCORE   = 8.0    # lower DOWN threshold by this * score
BIAS_LOWER_PER_SCORE   = 4.0    # raise UP threshold by this * score
# ===================================================

# ---------------- Servo helpers (jitter-minimized) ----------------
def setup_servo():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(SERVO_PIN, PWM_HZ)
    pwm.start(0.0)
    return pwm

def angle_to_duty(angle):
    angle = max(0, min(180, angle))
    return DUTY_MIN + (angle / 180.0) * (DUTY_MAX - DUTY_MIN)

def move_servo(pwm, angle, hold_ms=MOVE_HOLD_MS):
    """Drive servo briefly to target, then stop driving to avoid hold jitter."""
    duty = angle_to_duty(angle)
    t_end = time.time() + hold_ms/1000.0
    while time.time() < t_end:
        pwm.ChangeDutyCycle(duty)
        time.sleep(0.02)  # ~1–2 pulses per loop
    pwm.ChangeDutyCycle(0.0)  # release -> no jitter while idle

# ---------------- Camera / Picamera2 ----------------
def make_camera():
    picam2 = Picamera2()
    picam2.start_preview(Preview.NULL)  # headless-safe
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
    """Enable AE/AWB briefly to find sane values, then lock them."""
    picam2.set_controls({"AeEnable": True})
    if FIX_WHITE_BALANCE:
        picam2.set_controls({"AwbEnable": True})
    time.sleep(1.0)  # increase if very dim

    meta  = picam2.capture_metadata()
    exp   = meta.get("ExposureTime")
    gain  = meta.get("AnalogueGain")
    cgain = meta.get("ColourGains") if FIX_WHITE_BALANCE else None

    lock = {"AeEnable": False, "NoiseReductionMode": 0}
    if exp   is not None: lock["ExposureTime"] = int(exp)
    if gain  is not None: lock["AnalogueGain"] = float(gain)
    if FIX_WHITE_BALANCE:
        lock["AwbEnable"] = False
        if cgain is not None:
            lock["ColourGains"] = (float(cgain[0]), float(cgain[1]))
    picam2.set_controls(lock)
    return exp, gain, cgain

# --------- Flicker score (FFT on rolling luminance) ---------
def compute_flicker_score(ts, xs, band_lo=FLASH_BAND_LOW_HZ, band_hi=FLASH_BAND_HIGH_HZ):
    """ts, xs: arrays of timestamps (s) and luminance samples (arbitrary units)."""
    if len(xs) < 20:
        return 0.0
    dur = ts[-1] - ts[0]
    if dur < 0.8:  # need enough history
        return 0.0

    # Resample to a uniform grid near the actual rate (cap at 50 Hz)
    est_fs = max(10.0, min(50.0, len(xs) / dur))
    t_uniform = np.linspace(ts[0], ts[-1], int(est_fs * dur), endpoint=True)
    x_uniform = np.interp(t_uniform, ts, xs)

    # Remove DC & window
    x = x_uniform - np.mean(x_uniform)
    if np.max(np.abs(x)) < 1e-6:
        return 0.0
    w = np.hanning(len(x))
    X = np.fft.rfft(x * w)
    P = (np.abs(X) ** 2)
    freqs = np.fft.rfftfreq(len(x), 1.0 / est_fs)

    # band power / total power (excluding DC bin)
    band = (freqs >= band_lo) & (freqs <= band_hi)
    num = float(np.sum(P[band]))
    den = float(np.sum(P[1:]) + 1e-9)
    score = num / den
    return float(np.clip(score, 0.0, 1.0))

# ---------------- Main ----------------
def main():
    picam2 = make_camera()
    pwm = setup_servo()

    # Start with glasses UP
    current_state = "up"
    move_servo(pwm, ANGLE_UP)

    last_flip = 0.0
    hi_cnt = lo_cnt = 0
    frame_idx = 0
    last_info = ""

    # Brightness smoothing
    avg_ema = THRESHOLD  # initialize near threshold

    # Flicker buffers & timers
    lum_buf = deque(maxlen=1000)  # (t, luma)
    last_flicker_check = 0.0
    flicker_score = 0.0
    hold_until = 0.0

    try:
        while True:
            frame = picam2.capture_array()
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Use a central ROI (robust to edges)
            h, w = gray.shape
            roi = gray[h//3:2*h//3, w//3:2*w//3]
            inst_luma = float(np.mean(roi))

            # Update EMA and buffers
            avg_ema = 0.8 * avg_ema + 0.2 * inst_luma
            now   = time.time()
            lum_buf.append((now, inst_luma))

            # Recompute flicker score periodically
            if now - last_flicker_check >= FLICKER_CHECK_EVERY:
                ts = np.array([t for t,_ in lum_buf], dtype=np.float64)
                xs = np.array([x for _,x in lum_buf], dtype=np.float32)
                # keep only last WIN_SEC seconds
                if len(ts) >= 2:
                    t0 = ts[-1] - WIN_SEC
                    keep = ts >= t0
                    ts, xs = ts[keep], xs[keep]
                flicker_score = compute_flicker_score(ts, xs)
                last_flicker_check = now

            # Bias thresholds while flashing
            upper = THRESHOLD + HYSTERESIS/2.0
            lower = THRESHOLD - HYSTERESIS/2.0
            upper_down = upper - BIAS_UPPER_PER_SCORE * flicker_score
            lower_up   = lower + BIAS_LOWER_PER_SCORE * flicker_score

            # Latch DOWN while strong flashing
            if flicker_score >= FLICKER_FORCE_T:
                hold = MIN_DOWN_HOLD_S + EXTRA_HOLD_PER_SCORE * flicker_score
                hold_until = max(hold_until, now + hold)
                if current_state != "down" and (now - last_flip) > 0.1:
                    move_servo(pwm, ANGLE_DOWN)
                    current_state = "down"
                    last_flip = now

            # Headless calibration trigger: touch /tmp/calibrate to relock AE/AWB
            if os.path.exists("/tmp/calibrate"):
                exp, gain, cg = lock_current_exposure_and_wb(picam2)
                last_info = f"LOCKED exp={int(exp) if exp else '?'}us gain={gain:.2f if gain else '?'}"
                os.remove("/tmp/calibrate")

            # Persistence + cooldown decisions (using EMA + biased thresholds)
            if current_state == "up":
                hi_cnt = hi_cnt + 1 if avg_ema >= upper_down else 0
                if hi_cnt >= REQ_FRAMES and (now - last_flip) > COOLDOWN_S:
                    move_servo(pwm, ANGLE_DOWN)
                    current_state = "down"
                    last_flip = now
            else:  # down
                # Respect the hold timer during/after flashing
                can_release = now >= hold_until
                lo_cnt = lo_cnt + 1 if avg_ema <= lower_up else 0
                if can_release and lo_cnt >= REQ_FRAMES and (now - last_flip) > COOLDOWN_S:
                    move_servo(pwm, ANGLE_UP)
                    current_state = "up"
                    last_flip = now

            # Lightweight status printing
            if (frame_idx % PRINT_EVERY) == 0:
                if not last_info:
                    meta = picam2.capture_metadata()
                    exp  = meta.get("ExposureTime")
                    ag   = meta.get("AnalogueGain")
                    if exp and ag:
                        last_info = f"exp={int(exp)}us gain={ag:.2f}"
                print(f"Bright={avg_ema:.1f}  Flicker={flicker_score:.2f}  State={current_state}  {last_info}")
                last_info = ""

            frame_idx += 1

    except KeyboardInterrupt:
        pass
    finally:
        try:
            move_servo(pwm, ANGLE_UP)  # park up
            time.sleep(0.3)
        except Exception:
            pass
        pwm.stop()
        GPIO.cleanup()
        picam2.stop()

if __name__ == "__main__":
    main()
