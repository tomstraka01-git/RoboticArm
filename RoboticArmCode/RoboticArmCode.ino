#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <math.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

#define SERVOMIN  150
#define SERVOMAX  600
#define NUM_SERVOS 5
#define STEP_DELAY 10



int currentAngle[NUM_SERVOS];


struct ServoTarget {
  int target;
  bool moving;
};


ServoTarget servoTargets[NUM_SERVOS];
unsigned long lastStepTime = 0;


int angleToPulse(int angle) {
  return map(angle, 0, 180, SERVOMIN, SERVOMAX);
}

void setServo(uint8_t channel, int angle) {
  angle = constrain(angle, 0, 180);
  pwm.setPWM(channel, 0, angleToPulse(angle));
  currentAngle[channel] = angle;
}

void queueServo(uint8_t channel, int targetAngle) {
  servoTargets[channel].target = constrain(targetAngle, 0, 180);
  servoTargets[channel].moving = true;
}

void updateServos() {
  if (millis() - lastStepTime < STEP_DELAY) return;
  lastStepTime = millis();

  for (int i = 0; i < NUM_SERVOS; i++) {
    if (!servoTargets[i].moving) continue;
    int current = currentAngle[i];
    int target = servoTargets[i].target;
    if (current == target) {
      servoTargets[i].moving = false;
      continue;
    }
    int step = (current < target) ? 1 : -1;
    setServo(i, current + step);
  }
}


void handleSerial() {
  if (!Serial.available()) return;

  String input = Serial.readStringUntil('\n');
  input.trim();


  float values[5] = {0, 0, 0, 0, 0};
  int valueIndex = 0;
  int start = 0;

  for (int i = 0; i <= input.length() && valueIndex < 5; i++) {
    if (i == input.length() || input[i] == ' ') {
      if (i > start) {
        values[valueIndex++] = input.substring(start, i).toFloat();
      }
      start = i + 1;
    }
  }

  if (valueIndex < 5) return; 

  float base = values[0];
  float shoulder = values[1];
  float elbow = values[2];
  float wrist = values[3];
  float gripper = values[4];

  queueServo(0, (int)base);
  queueServo(1, (int)shoulder);
  queueServo(2, (int)elbow);
  queueServo(3, (int)wrist);
  queueServo(4, (int)gripper);
 

  
  Serial.print("Angles => base:"); Serial.print(base);
  Serial.print(" shoulder:"); Serial.print(shoulder);
  Serial.print(" elbow:"); Serial.print(elbow);
  Serial.print(" wrist:"); Serial.print(wrist);
  Serial.print(" gripper:"); Serial.println(gripper);
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  pwm.begin();
  pwm.setPWMFreq(50);
  delay(500);

  for (int i = 0; i < NUM_SERVOS; i++) {
    currentAngle[i] = 90;
    setServo(i, 90);
    servoTargets[i] = {90, false}; 
  }
}

void loop() {
  handleSerial();
  updateServos();
}