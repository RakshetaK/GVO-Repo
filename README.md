# VYZ — A Wearable That Calms Overwhelming Environments

A smart baseball cap that helps people stay comfortable in loud, high-stimulus places (arenas, concerts, busy streets) by **softening light**, **softening sound**, and **adding steady, calming cues**—all controlled by a simple phone app.

---

## The Problem

Big venues bombard you with flashing lights and sharp, harsh sounds. For many people—especially those with sensory sensitivities—that can trigger stress, headaches, or panic. Single-purpose fixes (earplugs, sunglasses) don’t adapt when the environment changes moment to moment.

## The Idea (What VYZ Is)

VYZ combines three effects into one discreet wearable:

1. **Soften what you see**  
   A small visor (“sunglasses”) flips down on demand to cut glare and visual clutter.

2. **Soften what you hear**  
   An audio path aims to reduce unpleasant, piercing frequencies so sound feels less harsh.

3. **Steady what you feel**  
   Gentle, slow LED light cues act like a visual “deep breath,” replacing chaotic flashes with predictability.

You control this via a **simple app** with big buttons: **Calm • Dark • Quiet • Auto**.

## Who It Helps

- People with **sensory processing sensitivities** (autism, ADHD, PTSD, migraines)
- Anyone who wants to **enjoy events longer** without sensory fatigue
- Parents, caregivers, and venue staff who need a **fast, reliable** calming tool

## Images of Our Product
<img src="https://raw.githubusercontent.com/RakshetaK/GVO-Repo/refs/heads/main/vyz-login.png" width="400">

## A 30-Second Walkthrough

- Enter a loud arena → tap **Calm** → cap shows a soft, steady LED glow.
- Stage lights start strobing → tap **Dark** → visor flips down, LEDs go minimal.
- A whistle shrieks nearby → tap **Quiet** → sound becomes less sharp and more comfortable.
- Things settle → tap **Auto** → the cap watches for spikes and adjusts itself.

## Why It’s Different

- **Three senses, one solution** — visual dimming + audio comfort + steady cues (most products only do one).
- **Fast in stressful moments** — big, obvious modes that react instantly.
- **Discreet** — it looks like a regular cap; no bulky headsets.

## What Exists Today (Proof, Not Promises)

- **Working cap** with:
  - Flip-down visor (tiny servo motor)
  - Calming LED patterns (smooth, non-flickery)
  - Prototype audio comfort path
- **Phone app** that switches modes (Calm/Dark/Quiet/Auto)
- **On-cap controller** that executes commands immediately

## Demo Checklist (What Judges Should Look For)

- **Speed** — tapping a mode produces an immediate, visible change
- **Clarity** — mode is obvious at a glance
- **Comfort** — behavior is calming, not distracting
- **Robustness** — repeated switching without glitches

## Safety & Reliability

- **Gentle motion** on the visor to avoid snaps/pinches
- **Conservative LED patterns** (slow, dim by default; “Dark” disables LEDs)
- **Power headroom** sized for servo and LEDs; common grounding
- **Fail-safe** — if the app disconnects, the cap stays in the last comfortable mode

---

## Quick Start (Nontechnical)

1. **Charge the cap.**
2. **Open the app** and connect.
3. **Tap a mode** (Calm, Dark, Quiet, Auto).
4. **Adjust intensity** if needed. That’s it.

---

## FAQ

**Does it work without the app?**  
Prototype uses the app; production adds on-cap buttons for quick toggles.

**Is it safe for light-sensitive users?**  
Yes. Patterns are slow/dim by default; “Dark” minimizes LEDs entirely.

**What about concerts?**  
“Quiet” focuses on reducing harshness rather than muting the world, which is more realistic in loud venues.

**Is setup complicated?**  
No—charge, open the app, tap a mode.

---

## Impact in One Line

**VYZ helps people stay present in places they love—without getting overwhelmed.**

---

# Technical Explanation (High Level)

> This section orients engineers and technical judges without drowning them in implementation details.

## System Components

- **Wearable Hardware**
  - **Arduino-class MCU**: deterministic control of LEDs (PWM) and servo
  - **RGB LED(s)**: soft, low-frequency patterns (no strobing)
  - **Micro-servo**: actuates visor/sunglasses
  - **(Optional) Mic/Audio path**: comfort filtering for harsh frequencies
  - **(Optional) Light/camera sensor**: detect fast brightness spikes for Auto mode
- **Edge Controller**
  - **Raspberry Pi** (or similar SBC): networking + simple API → forwards commands to MCU via serial
  - **Flask service**: HTTP endpoints mapping UI actions to serial commands
- **Mobile App**
  - **Simple UI** with four modes + intensity sliders
  - Connects to the Pi’s local API (or BLE in future) to send commands

## Architecture (Control & Data Flow)

[Mobile App]
|
| HTTP/WebSocket (local network) ← future: BLE
v
[Edge: Flask API on Raspberry Pi]
|
| Serial (USB/UART)
v
[Arduino MCU] ──> [RGB LEDs (PWM, smoothing)]
└──> [Servo (visor)]
└──> [Audio comfort path (prototype)]
^
└── (optional) [Light/Mic sensors for Auto mode]

- **Edge separation**: the Pi handles connectivity and simple logic; the MCU handles millisecond-level timing and actuator control for smooth, flicker-free output.
- **Determinism**: LED and servo updates never wait on the network; only _mode changes_ traverse the app→Pi→MCU pipeline.

## Modes = A Tiny State Machine

States: `CALM`, `DARK`, `QUIET`, `AUTO` (+ `IDLE/SAFE`)

- **CALM**: LEDs run a low-frequency, low-intensity easing pattern; visor up; audio neutral.
- **DARK**: visor down; LEDs minimal/off; audio neutral; used for bright/stroby scenes.
- **QUIET**: audio comfort curve active; LEDs subdued; visor optional.
- **AUTO**: sensor thresholds (light spikes, sudden loudness) trigger transitions to `DARK`/`QUIET`; decay timers return to `CALM` once the environment stabilizes.

Transition sketch:
CALM --(light spike)--> DARK --(stability timer)--> CALM
CALM --(loudness spike)--> QUIET --(stability timer)--> CALM
ANY --(user tap)--> [CALM|DARK|QUIET|AUTO]
AUTO --(no spikes)--> CALM

## Command Protocol (Edge → MCU)

Human-readable, line-based messages over serial (examples):
MODE:CALM
MODE:DARK
MODE:QUIET
MODE:AUTO

LED:SET R=20,G=24,B=28
LED:PATTERN type=EASE_IN_OUT cycle_ms=4000

SERVO:ANGLE 38 # visor position (deg)
AUDIO:PROFILE QUIET_1 # prototype EQ/attenuation preset

SENSOR:THRESHOLDS LIGHT_SPIKE=high AUDIO_SPIKE=medium

- MCU parses and applies commands immediately; invalid lines are ignored (robust to noise).
- Rate-limit and idempotency prevent “thrash” (e.g., re-applying same mode too often).

## Safety & Power Considerations

- **Power budget**: isolate servo current peaks; add bulk capacitance; avoid brownouts.
- **LED current-limit**: always use series resistors; verify common-anode/cathode wiring.
- **Common ground**: Pi, MCU, sensors share a reference ground to avoid erratic behavior.
- **Mechanical**: limit servo travel; soft start/stop to avoid pinches and audible chatter.

## Performance Notes

- **LED smoothing**: gamma correction + eased ramps to avoid perceived flicker/steps.
- **Servo motion**: rate limiting (deg/sec) + micro-steps for quiet, smooth flips.
- **Auto mode stability**: hysteresis + hold-off timers to prevent mode ping-pong.

## Setup (Engineer’s High-Level)

1. **Flash MCU** with the Arduino sketch (pins: RGB on PWM, servo on a timer-friendly pin).
2. **Wire** LEDs (with resistors), servo (separate 5V rail if needed), and shared ground.
3. **Run Flask API** on the Pi; set serial port and advertise IP to the app.
4. **Point the App** at the Pi’s IP; tap modes; confirm immediate MCU response.

## Known Limitations (Prototype)

- Audio path is a **prototype**; advanced filtering/EQ requires dedicated DSP/SoC.
- Using Wi-Fi adds **latency variability**; BLE or on-cap buttons are planned.
- Sensor-based Auto mode is basic; richer models (e.g., ML spike classification) are future work.

## Roadmap

- Add **on-cap buttons** for app-free toggles
- Package **profiles** (Arena/Concert/Classroom) with one-tap presets
- BLE control, offline operation, and haptics for discreet feedback
- Venue partnership: **“Sensory-Friendly Mode”** integrations

---
