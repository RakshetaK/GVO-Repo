# VYZ

Imagine you're at the 2028 LA Olympics Game! You're watching your favorite sport, but you feel uncomfortable. There's strobing lights and loud sounds all around you, and you're starting to feel overwhelmed. However, you don't want to miss enjoying your favorite sport. Introducing, Vyz, a baseball hat that helps reduce sensory overload by using calming leds, putting on sunglasses, and filtering out loud noises and uncomfortable frequencies.

## 🔌 Important Pin-Out and Connections Information

### 🧭 RPi to Arduino Communication

- **Raspberry Pi GPIO14 (Pin 8)** → **Arduino Digital 0 (RX)**
- **Shared Ground** between Raspberry Pi and Arduino

---

### 🔴 Arduino to RGB LED Connections

- **Digital 3** → **LED Red**
- **Digital 5** → **LED Green**
- **Digital 6** → **LED Blue**
- **3.3V** → **LED Anode**

---

### ⚙️ Arduino to Servo Connection

- **Digital 9** → **Servo Signal**
- **5V** → **Servo Positive (Power)**
