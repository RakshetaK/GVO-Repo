import cv2
from picamera2 import Picamera2
import numpy as np
import time
import RPi.GPIO as GPIO

# ====== User settings ======
THRESHOLD = 170.0
HYSTERESIS = 10.0
ANGLE_NORMAL = 0
ANGLE_PROTECT = 90
SERVO_PIN = 18
PWM_HZ = 50

# Manual exposure/gain (initial guesses). You can press 'c' at runtime to auto-calibrate then lock.
EXPOSURE_US = 8000        # 8000 µs ≈ 1/125 s
ANALOGUE_GAIN = 1.0       # 1.0–2.0 are typical; higher = brighter but noisier
FIX_WHITE_BALANCE = True  # lock AWB so colors/grey levels stay consistent
WB_GAINS = (1.8, 1.6)     # typical daylight-ish starting point; adjust after 'c' calibration if needed
# ===========================

# --- Servo helpers ---
def setup_servo():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(SERVO_PIN, PWM_HZ)
    pwm.start(0)
    return pwm

def angle_to_duty(angle):
    angle = max(0, min(180, angle))
    duty_min, duty_max = 2.5, 12.5
    return duty_min + (angle / 180.0) * (duty_max - duty_min)

def move_servo(pwm, angle):
    pwm.ChangeDutyCycle(angle_to_duty(angle))
    time.sleep(0.2)

# --- Camera setup ---
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)

# Set controls BEFORE start() so libcamera applies them as the stream begins
initial_controls = {
    "AeEnable": False,                  # turn OFF auto-exposure
    "ExposureTime": EXPOSURE_US,        # microseconds
    "AnalogueGain": ANALOGUE_GAIN,      # sensor analogue gain
    "NoiseReductionMode": 0             # 0 = off; helps keep processing consistent
}

if FIX_WHITE_BALANCE:
    initial_controls.update({
        "AwbEnable": False,             # turn OFF auto white balance
        "ColourGains": WB_GAINS         # manual WB gains (R, B). G is implicit.
    })

picam2.set_controls(initial_controls)
picam2.start()

# --- Servo setup ---
pwm = setup_servo()
current_state = "normal"
move_servo(pwm, ANGLE_NORMAL)

def lock_current_exposure_and_wb():
    """Enable AE/AWB briefly to find sane values, then lock them."""
    # Enable AE/AWB
    picam2.set_controls({"AeEnable": True})
    if FIX_WHITE_BALANCE:
        picam2.set_controls({"AwbEnable": True})
    time.sleep(1.0)  # let it settle; increase if scene is very dim

    meta = picam2.capture_metadata()
    exp_us = meta.get("ExposureTime")
    ag = meta.get("AnalogueGain")

    # If AWB is used, read its ColourGains and lock them too
    cg = meta.get("ColourGains") if FIX_WHITE_BALANCE else None

    # Now lock everything back
    lock_controls = {"AeEnable": False}
    if exp_us is not None:
        lock_controls["ExposureTime"] = int(exp_us)
    if ag is not None:
        lock_controls["AnalogueGain"] = float(ag)
    if FIX_WHITE_BALANCE:
        lock_controls["AwbEnable"] = False
        if cg is not None:
            lock_controls["ColourGains"] = (float(cg[0]), float(cg[1]))

    # Keep denoise off for consistency
    lock_controls["NoiseReductionMode"] = 0
    picam2.set_controls(lock_controls)

    return exp_us, ag, cg

try:
    last_info = ""
    while True:
        frame = picam2.capture_array()

        # Compute brightness
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        average_brightness = float(np.mean(gray_frame))

        upper = THRESHOLD + HYSTERESIS / 2.0
        lower = THRESHOLD - HYSTERESIS / 2.0

        if current_state == "normal" and average_brightness >= upper:
            move_servo(pwm, ANGLE_PROTECT)
            current_state = "protect"
        elif current_state == "protect" and average_brightness <= lower:
            move_servo(pwm, ANGLE_NORMAL)
            current_state = "normal"

        # Read (locked) exposure/gain from metadata for on-screen info
        meta = picam2.capture_metadata()
        exp_us = meta.get("ExposureTime")
        ag = meta.get("AnalogueGain")

        status_text = f'Brightness: {average_brightness:.1f}  State: {current_state}'
        cv2.putText(frame, status_text, (10, 28), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Threshold: {THRESHOLD:.0f}', (10, 54),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2, cv2.LINE_AA)
        if exp_us and ag:
            info = f'Exp: {int(exp_us)}us  Gain: {ag:.2f}'
            last_info = info
        cv2.putText(frame, last_info, (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2, cv2.LINE_AA)

        cv2.imshow("Camera Feed (AE/AWB locked)", frame)

        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):   # quit
            break
        elif k == ord('c'): # calibrate + lock
            exp, gain, cg = lock_current_exposure_and_wb()
            last_info = f'LOCKED -> Exp:{int(exp) if exp else "?"}us  Gain:{gain:.2f if gain else "?"}'

finally:
    try:
        move_servo(pwm, ANGLE_NORMAL)
        pwm.stop()
        GPIO.cleanup()
    except Exception:
        pass
    picam2.stop()
    cv2.destroyAllWindows()