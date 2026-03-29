# Haxxy-GAS_SENSOR
Model of gas leakage sensor, alarm alert + automatic shutoff + IoT message
#include <Servo.h>

const int GAS_SENSOR_PIN = A0;
const int LED_PIN = 7;
const int BUZZER_PIN = 8;
const int SERVO_PIN = 9;
const int FAN_PIN = 6;

const int KITCHEN_MILD = 450;
const int KITCHEN_MODERATE = 550;
const int KITCHEN_DANGEROUS = 700;
const int KITCHEN_EMERGENCY = 900;

int gasValue = 0;
int baselineValue = 0;
int GAS_THRESHOLD = 0;
int newThreshold = 0;
bool alertActive = false;

const unsigned long RECALIBRATE_INTERVAL = 300000;
unsigned long lastRecalibrateTime = 0;

Servo gasValve;

String getDangerLevel() {
  if (gasValue >= KITCHEN_EMERGENCY) return "EMERGENCY";
  else if (gasValue >= KITCHEN_DANGEROUS) return "DANGEROUS";
  else if (gasValue >= KITCHEN_MODERATE) return "MODERATE LEAK";
  else if (gasValue >= KITCHEN_MILD) return "MILD LEAK";
  else return "NORMAL";
}

void alertBeepAndLED() {
  if (gasValue >= KITCHEN_DANGEROUS) {
    Serial.println("CONTINUOUS BUZZ — LED ON");
    unsigned long buzzStart = millis();
    int duration = (gasValue >= KITCHEN_EMERGENCY) ? 5000 : 3000;
    digitalWrite(LED_PIN, HIGH);
    while (millis() - buzzStart < duration) {
      if (analogRead(GAS_SENSOR_PIN) <= GAS_THRESHOLD) {
        digitalWrite(BUZZER_PIN, LOW);
        digitalWrite(LED_PIN, LOW);
        return;
      }
      digitalWrite(BUZZER_PIN, HIGH);
      delay(100);
    }
    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  } else {
    int numberOfBeeps = 0;
    int beepDuration = 500;
    int beepGap = 200;

    if (gasValue >= KITCHEN_MODERATE) numberOfBeeps = 5;
    else if (gasValue >= KITCHEN_MILD) numberOfBeeps = 3;

    Serial.print("Playing ");
    Serial.print(numberOfBeeps);
    Serial.println(" beeps and blinks...");

    for (int i = 0; i < numberOfBeeps; i++) {
      if (analogRead(GAS_SENSOR_PIN) <= GAS_THRESHOLD) {
        digitalWrite(BUZZER_PIN, LOW);
        digitalWrite(LED_PIN, LOW);
        return;
      }
      digitalWrite(BUZZER_PIN, HIGH);
      digitalWrite(LED_PIN, HIGH);
      delay(beepDuration);
      digitalWrite(BUZZER_PIN, LOW);
      digitalWrite(LED_PIN, LOW);
      delay(beepGap);
    }
    delay(500);
  }
}

int calculateThreshold(int baseline) {
  if (baseline <= 150) return baseline + 50;
  else if (baseline <= 200) return baseline + 60;
  else if (baseline <= 300) return baseline + 70;
  else if (baseline <= 400) return baseline + 80;
  else if (baseline <= 500) return baseline + 90;
  else return baseline + 100;
}

void calibrateSensor() {
  Serial.println("==============================");
  Serial.println("  LPG Kitchen Safety System   ");
  Serial.println("==============================");
  Serial.println("Calibrating sensor...");
  Serial.println("Make sure no gas is present!");
  Serial.println("==============================");

  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(300);
    digitalWrite(LED_PIN, LOW);
    delay(300);
  }

  long total = 0;
  int minValue = 1023;
  int maxValue = 0;

  for (int i = 0; i < 20; i++) {
    int reading = analogRead(GAS_SENSOR_PIN);
    total += reading;
    if (reading < minValue) minValue = reading;
    if (reading > maxValue) maxValue = reading;
    Serial.print("Reading ");
    if (i + 1 < 10) Serial.print("0");
    Serial.print(i + 1);
    Serial.print(" : ");
    Serial.println(reading);
    delay(1000);
  }

  baselineValue = total / 20;
  int variance = maxValue - minValue;
  GAS_THRESHOLD = calculateThreshold(baselineValue);

  if (variance <= 20) Serial.println("Environment: Very stable");
  else if (variance <= 50) Serial.println("Environment: Moderately stable");
  else if (variance <= 100) Serial.println("Environment: Slightly unstable");
  else Serial.println("Environment: Unstable");

  Serial.println("==============================");
  Serial.print("Baseline average : ");
  Serial.println(baselineValue);
  Serial.print("Minimum reading  : ");
  Serial.println(minValue);
  Serial.print("Maximum reading  : ");
  Serial.println(maxValue);
  Serial.print("Variance         : ");
  Serial.println(variance);
  Serial.print("Threshold set to : ");
  Serial.println(GAS_THRESHOLD);
  Serial.println("==============================");
  Serial.println("Calibration complete!");

  // Fan test on startup
  Serial.println("Fan test starting...");
  digitalWrite(FAN_PIN, HIGH);
  Serial.println("Fan ON — testing...");
  delay(3000);
  digitalWrite(FAN_PIN, LOW);
  Serial.println("Fan OFF — test complete!");

  for (int i = 0; i < 5; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }

  lastRecalibrateTime = millis();
}

void dynamicRecalibrate() {
  if (alertActive) {
    Serial.println("Skipping recalibration — gas detected.");
    return;
  }

  Serial.println("==============================");
  Serial.println("Dynamic recalibration started...");

  long total = 0;
  for (int i = 0; i < 5; i++) {
    total += analogRead(GAS_SENSOR_PIN);
    delay(200);
  }

  int newBaseline = total / 5;
  newThreshold = calculateThreshold(newBaseline);

  Serial.print("Old threshold    : ");
  Serial.println(GAS_THRESHOLD);
  Serial.print("New threshold    : ");
  Serial.println(newThreshold);

  int difference = newThreshold - GAS_THRESHOLD;
  int gradualStep = difference * 0.2;

  if (difference > 0 && gradualStep == 0) gradualStep = 1;
  if (difference < 0 && gradualStep == 0) gradualStep = -1;

  GAS_THRESHOLD = GAS_THRESHOLD + gradualStep;
  baselineValue = newBaseline;

  Serial.print("Threshold adjusted to : ");
  Serial.println(GAS_THRESHOLD);
  Serial.println("==============================");

  lastRecalibrateTime = millis();
}

void setup() {
  Serial.begin(9600);

  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);

  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(FAN_PIN, LOW);

  gasValve.attach(SERVO_PIN);
  gasValve.write(0);

  Serial.println("System starting...");
  Serial.println("Warming up sensor...");
  Serial.println("Please wait 10 seconds...");

  for (int i = 0; i < 10; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(500);
    digitalWrite(LED_PIN, LOW);
    delay(500);
    Serial.print("Warmup: ");
    Serial.print(i + 1);
    Serial.println(" seconds");
  }

  calibrateSensor();

  Serial.println("==============================");
  Serial.println("Monitoring kitchen gas levels");
  Serial.println("Next recalibration in 5 mins");
  Serial.println("==============================");
}

void loop() {
  gasValue = analogRead(GAS_SENSOR_PIN);

  Serial.print("Gas level: ");
  Serial.print(gasValue);
  Serial.print("   Threshold: ");
  Serial.print(GAS_THRESHOLD);
  Serial.print("   Status: ");
  Serial.println(getDangerLevel());

  if (gasValue > GAS_THRESHOLD) {
    alertActive = true;

    // Servo closes valve
    delay(300);
    gasValve.write(90);

    // Fan turns ON to disperse gas
    digitalWrite(FAN_PIN, HIGH);

    Serial.print("WARNING — ");
    Serial.println(getDangerLevel());
    Serial.println("Valve closed!");
    Serial.println("Fan ON — dispersing gas!");

    // Buzzer and LED alert
    alertBeepAndLED();
  }

  if (gasValue <= GAS_THRESHOLD && alertActive) {
    alertActive = false;
    digitalWrite(LED_PIN, LOW);
    digitalWrite(BUZZER_PIN, LOW);

    // Servo opens valve
    delay(300);
    gasValve.write(0);

    // Fan turns OFF
    digitalWrite(FAN_PIN, LOW);

    Serial.println("Gas cleared.");
    Serial.println("Valve opened.");
    Serial.println("Fan OFF.");
    Serial.println("Kitchen monitoring resumed.");
    Serial.println("==============================");
  }

  if (gasValue <= GAS_THRESHOLD && !alertActive) {
    Serial.println("Kitchen safe. No gas detected.");
  }

  unsigned long currentTime = millis();
  if (currentTime - lastRecalibrateTime >= RECALIBRATE_INTERVAL) {
    dynamicRecalibrate();
  }

  delay(500);
}
