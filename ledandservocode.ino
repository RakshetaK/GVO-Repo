#include <Servo.h>

// Servo control pins and variables
const int servoPin = 9;          // Servo signal pin
const int inputPin = 2;          // Digital input pin (button or signal)
Servo myServo;

// RGB LED control pins and variables
#define PIN_RED   3    // PWM pin for Red
#define PIN_GREEN 5    // PWM pin for Green
#define PIN_BLUE  6    // PWM pin for Blue

// ---- CONFIG ----
const bool COMMON_ANODE = true;   // Set false for common-cathode LED

// ----------------
String serialBuffer;
int valR = 0, valG = 0, valB = 0;

// Setup function
void setup() {
  // Initialize servo
  pinMode(inputPin, INPUT_PULLUP);   // Input pin with pull-up resistor
  myServo.attach(servoPin);          // Attach servo to pin 9
  myServo.write(0);                  // Start at 0 degrees

  // Initialize RGB LED pins
  pinMode(PIN_RED, OUTPUT);
  pinMode(PIN_GREEN, OUTPUT);
  pinMode(PIN_BLUE, OUTPUT);

  // Set RGB LED to off initially
  setRGB(50, 50, 50);  

  // Start Serial communication
  Serial.begin(9600);
  Serial.println("Servo and RGB LED Controller Ready");
}

// Function to convert percentage to PWM value
int percentToPWM(int percent) {
  percent = constrain(percent, 0, 100);
  int pwm = map(percent, 0, 100, 0, 255);
  if (COMMON_ANODE) pwm = 255 - pwm;  // Invert for common-anode LED
  return pwm;
}

// Function to set RGB LED colors
void setRGB(int r, int g, int b) {
  analogWrite(PIN_RED,   percentToPWM(r));
  analogWrite(PIN_GREEN, percentToPWM(g));
  analogWrite(PIN_BLUE,  percentToPWM(b));
}

// Main loop
void loop() {
  // Read input state for servo
  int state = digitalRead(inputPin);  // Read digital input

  if (state == LOW) {                 // LOW = active (button pressed or signal)
    myServo.write(90);                // Move to 90 degrees
    Serial.println("Input LOW → Servo 90°");
  } else {                            // HIGH = inactive
    myServo.write(0);                 // Move back to 0 degrees
    Serial.println("Input HIGH → Servo 0°");
  }

  // Serial command parsing for RGB LED
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '!') {
      serialBuffer = "";          // Start of new message
    } else if (c == '#') {
      parseRGB(serialBuffer);     // End of message
      serialBuffer = "";
    } else {
      serialBuffer += c;          // Accumulate characters
    }
  }

  delay(50);  // Small delay to avoid jitter
}

// Parse the RGB format "R.G.B"
void parseRGB(String msg) {
  int p1 = msg.indexOf('.');
  int p2 = msg.indexOf('.', p1 + 1);
  if (p1 == -1 || p2 == -1) {
    Serial.println("Invalid format");
    return;
  }

  int r = msg.substring(0, p1).toInt();
  int g = msg.substring(p1 + 1, p2).toInt();
  int b = msg.substring(p2 + 1).toInt();

  // Constrain the values to 0-100% range
  r = constrain(r, 0, 100);
  g = constrain(g, 0, 100);
  b = constrain(b, 0, 100);

  // Set the RGB LED colors
  setRGB(r, g, b);

  // Print RGB values to Serial Monitor
  Serial.print("Set RGB → ");
  Serial.print(r); Serial.print("% ");
  Serial.print(g); Serial.print("% ");
  Serial.print(b); Serial.println("%");
}

