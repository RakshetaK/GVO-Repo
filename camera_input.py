import cv2
from picamera2 import Picamera2
import numpy as np
import time

import RPi.GPIO as GPIO  # sudo apt-get install python3-rpi.gpio

# ====== User settings ======
THRESHOLD = 170.0            # brightness above which we consider it "overbearing"
HYSTERESIS = 10.0            # prevents rapid toggling near the threshold
ANGLE_NORMAL = 0             # angle when brightness is normal
ANGLE_PROTECT = 90           # angle to rotate when brightness is overbearing (tune to your visor)
SERVO_PIN = 18               # BCM numbering; use a PWM-capable pin
PWM_HZ = 50                  # standard servo PWM frequency
# ===========================

# --- Servo helpers ---
def setup_servo():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(SERVO_PIN, PWM_HZ)
    pwm.start(0)  # start with 0% duty, then move to desired angle
    return pwm

def angle_to_duty(angle):
    """
    Map 0–180° to ~2.5–12.5% duty cycle (typical for many servos).
    You may need to tweak min/max for your specific servo.
    """
    angle = max(0, min(180, angle))
    duty_min, duty_max = 2.5, 12.5
    return duty_min + (angle / 180.0) * (duty_max - duty_min)

def move_servo(pwm, angle):
    duty = angle_to_duty(angle)
    pwm.ChangeDutyCycle(duty)
    # small settle time helps some servos reach the position
    time.sleep(0.2)
    # optional: stop driving continuously to reduce buzzing (some servos like this)
    # pwm.ChangeDutyCycle(0)

# --- Camera setup ---
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
picam2.start()

# --- Servo setup ---
pwm = setup_servo()
current_state = "normal"  # "normal" or "protect"
move_servo(pwm, ANGLE_NORMAL)

try:
    while True:
        # Capture frame
        frame = picam2.capture_array()

        # Compute brightness
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        average_brightness = float(np.mean(gray_frame))

        # Hysteresis logic:
        # - Switch to PROTECT when brightness ≥ THRESHOLD + HYSTERESIS/2
        # - Return to NORMAL when brightness ≤ THRESHOLD - HYSTERESIS/2
        upper = THRESHOLD + HYSTERESIS / 2.0
        lower = THRESHOLD - HYSTERESIS / 2.0

        if current_state == "normal" and average_brightness >= upper:
            move_servo(pwm, ANGLE_PROTECT)
            current_state = "protect"
        elif current_state == "protect" and average_brightness <= lower:
            move_servo(pwm, ANGLE_NORMAL)
            current_state = "normal"

        # Annotate and show
        status_text = f'Brightness: {average_brightness:.1f}  State: {current_state}'
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Threshold: {THRESHOLD:.0f}', (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2, cv2.LINE_AA)

        cv2.imshow("Camera Feed", frame)

        # Exit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Return to safe angle and cleanup
    try:
        move_servo(pwm, ANGLE_NORMAL)
        pwm.stop()
        GPIO.cleanup()
    except Exception:
        pass
    picam2.stop()
    cv2.destroyAllWindows()
