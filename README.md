# VYZ — A Wearable That Calms Overwhelming Environments (Fall 2025 Good Vibes Only! Hackathon)

A smart baseball cap that helps people stay comfortable in loud, high-stimulus places (arenas, concerts, busy streets) by **softening light**, **softening sound**, and **adding steady, calming cues**—all controlled by a simple phone app.

## Edits
We currently have this ported on to the Jetson Nano. This read me talks about the RPi version of this project. For more information on the Jetson Nano version, refer to this doc:
https://docs.google.com/document/d/1ECA6VJYPtvybOeiOZTtpwBOocEHXtJOASXUGUJ1G4Ss/edit?tab=t.0

---

## The Problem

Big venues bombard you with flashing lights and sharp, harsh sounds. For many people—especially those with sensory sensitivities—that can trigger stress, headaches, or panic. Single-purpose fixes (earplugs, sunglasses) don’t adapt when the environment changes moment to moment. This will be especially be useful in the upcoming 2028 Sumemer Olympic games hosted in LA to help as many people enjoy them as possible.

## The Idea (What VYZ Is)

VYZ combines three effects into one discreet wearable:

1. **Soften what you see**  
   A small visor (“sunglasses”) flips down on demand to cut glare and visual clutter.

2. **Soften what you hear**  
   An audio path aims to reduce unpleasant, piercing frequencies and soften loud sounds to reduce the effects of harsh sounds.

3. **Steady what you feel**  
   Gentle LED lights can provide a calming feel when needed and ensure that the user can stay calm.

All of this can be customized with a simple app and AI to ensure that the user has the best experience possible.

## Who It Helps

- People with **sensory processing sensitivities** (autism, ADHD, PTSD, migraines)
- Anyone who wants to **enjoy events longer** without sensory fatigue
- Parents, caregivers, and venue staff who need a **fast, reliable** calming tool

# Vyz Hardware
<img src="https://github.com/RakshetaK/GVO-Repo/blob/main/Images/vyz-physical-wearable.JPG" width="300">
<img src="https://github.com/RakshetaK/GVO-Repo/blob/main/Images/vyz-compute-box.JPG" width="300">
<img src="https://github.com/RakshetaK/GVO-Repo/blob/main/Images/IMG_3413.JPG" width="300">

### Sunglasses
Sunglasses are connected to a servo on the brim of the hat which is controlled by a camera connected to the RPi. The Rpi sends the signal over to an Arduino which performs the actual PWM to move the servo. When certain brightness is exceeded, the sunglasses come down to shield the user from harsh conditions. Additionally, the sunglasses can sense strobe lights to ensure that users can have a welcoming experience.

### Noise Canceling
A USB microphone connected to the RPi picks up audio signals. Then, signal transformations are performed in order to filter out high and low frequencies as well as compress loud sounds down to a less harsh level. We then play the processed audio signals out through headphones for the user to experience the game in it's entirety without fear of being overwhelmed.

### Calming LEDs
We used AI based on sensory inputs like brightness and noise to set the leds to an optimal level to reduce stress on the user. This processing is done on the RPi and then the light state is sent to an Arduino to actually control the LEDs.

# Vyz Mobile App (React Native + TypeScript, Expo)

A lightweight companion app that lets users quickly interact with **Mindfulness**, **Audio**, and **Visual** settings or functionality. Built with **React Native + TypeScript** and runs in **Expo Go** for instant demo-ability.
---

### 1) Welcome / Login
  
<img src="https://github.com/RakshetaK/GVO-Repo/blob/main/Images/vyz-login.png" width="300">

### 2) Mindfulness (Home tab)
- **Purpose:** fast access to guided breathing patterns for calming down in overstimulating spaces.
- **UI:** grid of “cards” (e.g., *Box*, *Balloon*, *Wave*, *4-7-8*), each launching a short on-screen guide or animation.
- **Behavior:** a tap starts a simple timer + animation + haptic tick.
- **Why:** creates a predictable rhythm, like a visual metronome for breathing.

<img src="https://github.com/RakshetaK/GVO-Repo/blob/main/Images/vyz-mindful.png" width="300">

---

### 3) Audio
- **Purpose:** reduce perceived harshness and offer soothing sound options.
- **UI:**
  - **Noise Suppression slider** (0–100%) to simulate muffling/attenuation.
  - **Soothing Sounds list** (White/Brown noise, Ocean Waves, Gentle Rain, etc.) with play/stop buttons.
- **Behavior:** single active sound at a time; respects system audio focus; persists last selection.

<img src="https://github.com/RakshetaK/GVO-Repo/blob/main/Images/vyz-audio.png" width="300">

---

### 4) Visual
- **Purpose:** dim bright surroundings and stabilize visual input.
- **UI:** circular **Brightness** control (coarse steps) with a vertical level indicator (fine feedback).
- **Behavior:** updates a brightness percentage and persists locally; intended to map to wearable’s visor/LED state in production.

<img src="https://github.com/RakshetaK/GVO-Repo/blob/main/Images/vyz-visual.png" width="300">

# Future Directions

### Electochromic Lenses
We want to implement electrochromic lenses, material that can change its transparency based on voltage to provide a more continous experience darkening and lightening experience to the user rather than the current binary sunglasses of on and off.

### Better Noise Canceling
We can implement a better noise canceling system for the headphones which can cancel out sound in a better way. We could use better microphones, higher computer, and better speakers to create a more immersive experience for users while preventing themm from becoming overwhelmed.

### Better Form Factor and Design
We currently need to run lots of cables and the device isn't very easy to use. We would like to make the design more seamless, so it's not as obvious that a user is using this device. Additionally, we want to make it significantly easier to use the device in general.
