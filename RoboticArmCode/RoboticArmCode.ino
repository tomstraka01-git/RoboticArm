#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <math.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

#define SERVOMIN  150
#define SERVOMAX  600
#define NUM_SERVOS 5
#define STEP_DELAY 10

float H0 = 50.0;
float L1 = 105.0;
float L2 = 100.0;
float L3 = 35.0;
float Lg = 60.0;

float theta0, theta1, theta2, theta3;
int currentAngle[NUM_SERVOS];

struct Position { float x, y, z; };
Position CurrentPosition;

bool ik_mode_on = true;


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

Position solveFK(float t0_deg, float t1_deg, float t2_deg, float t3_deg) {
  float t0 = t0_deg * PI / 180.0;
  float t1 = t1_deg * PI / 180.0;
  float t2 = t2_deg * PI / 180.0;
  float t3 = t3_deg * PI / 180.0;
  float phi = t1 + t2 + t3;

  float r = L1 * cos(t1) + L2 * cos(t1 + t2) + (L3 + Lg) * cos(phi);
  float z = H0 + L1 * sin(t1) + L2 * sin(t1 + t2) + (L3 + Lg) * sin(phi);

  Position p;
  p.x = r * cos(t0);
  p.y = r * sin(t0);
  p.z = z;
  return p;
}

bool solveIK(float x, float y, float z, float phi_deg = 0) {
  float phi = (phi_deg - 90.0) * PI / 180.0;

  theta0 = atan2(y, x);

  float r  = sqrt(x*x + y*y) - L3 * cos(phi);
  float zw = z - H0 - L3 * sin(phi);

  r  -= Lg * cos(phi);
  zw -= Lg * sin(phi);

  float dist = sqrt(r*r + zw*zw);
  if (dist > (L1 + L2) || dist < fabs(L1 - L2)) {
    return false;
  }

  float cos_theta2 = (r*r + zw*zw - L1*L1 - L2*L2) / (2.0 * L1 * L2);
  cos_theta2 = constrain(cos_theta2, -1.0, 1.0);
  theta2 = acos(cos_theta2);

  float k1 = L1 + L2 * cos(theta2);
  float k2 = L2 * sin(theta2);
  theta1 = atan2(zw, r) - atan2(k2, k1);

  theta3 = -(theta1 + theta2) + phi;

  theta0 *= 180.0 / PI;
  theta1 *= 180.0 / PI;
  theta2 *= 180.0 / PI;
  theta3 *= 180.0 / PI;

  return true;
}

void change_ik_mode(bool statement) {
  if (ik_mode_on != statement) {
    ik_mode_on = statement;
    CurrentPosition = solveFK(
      currentAngle[0] - 90,
      currentAngle[1] - 90,
      currentAngle[2] - 90,
      currentAngle[3] - 90
    );
  }
}

void moveTo(float x, float y, float z, float phi_deg = 90) {
  if (!solveIK(x, y, z, phi_deg)) {
    Serial.println("Target unreachable!");
    return;
  }

  int base = constrain((int)(theta0 + 90), 0, 180);
  int shoulder = constrain((int)(theta1 + 90), 0, 180);
  int elbow = constrain((int)(theta2 - 90), 0, 180);
  int wrist = constrain((int)(theta3 + 90), 0, 180);

  Serial.print("Angles => base:"); Serial.print(base);
  Serial.print(" shoulder:"); Serial.print(shoulder);
  Serial.print(" elbow:"); Serial.print(elbow);
  Serial.print(" wrist:"); Serial.println(wrist);

  queueServo(0, base);
  queueServo(1, shoulder);
  queueServo(2, elbow);
  queueServo(3, wrist);
}

void setGripper(int percent) {
  int angle = map(percent, 0, 100, 30, 150);
  queueServo(4, angle);
}

void demoSequence() {
  setGripper(100);
  moveTo(100, 0, 80, 90);
  delay(1000);
  moveTo(100, 80, 80, 90);
  delay(1000);
  moveTo(80, 0, 60, 0);
  delay(1000);
  setGripper(0);
  delay(500);
  setGripper(100);
}

void handleSerial() {
  if (!Serial.available()) return;

  String input = Serial.readStringUntil('\n');
  input.trim();

  if (input.startsWith("g ")) {
    setGripper(input.substring(2).toInt());
    return;
  }

  if (input.startsWith("m ")) {
    change_ik_mode(input.substring(2).toInt() == 1);
    return;
  }

  int i1 = input.indexOf(' ');
  int i2 = input.indexOf(' ', i1 + 1);
  int i3 = input.indexOf(' ', i2 + 1);

  if (i1 < 0 || i2 < 0) return;

  float a = input.substring(0, i1).toFloat();
  float b = input.substring(i1 + 1, i2).toFloat();
  float c = input.substring(i2 + 1, i3 > 0 ? i3 : input.length()).toFloat();
  float d = i3 > 0 ? input.substring(i3 + 1).toFloat() : 0.0;

  if (ik_mode_on) {
    Serial.print("Moving to: ");
    Serial.print(a); Serial.print(", ");
    Serial.print(b); Serial.print(", ");
    Serial.print(c); Serial.print(", phi=");
    Serial.println(d);
    moveTo(a, b, c, d);
    CurrentPosition = {a, b, c};
  } else {
    Serial.print("Direct angles => ");
    Serial.print(a); Serial.print(", ");
    Serial.print(b); Serial.print(", ");
    Serial.print(c); Serial.print(", ");
    Serial.println(d);
    queueServo(0, (int)a);
    queueServo(1, (int)b);
    queueServo(2, (int)c);
    queueServo(3, (int)d);

    CurrentPosition = solveFK(a - 90, b - 90, c - 90, d - 90);
  }
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