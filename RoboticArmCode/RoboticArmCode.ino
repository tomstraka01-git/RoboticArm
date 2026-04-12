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

int angleToPulse(int angle) {
  return map(angle, 0, 180, SERVOMIN, SERVOMAX);
}

void setServo(uint8_t channel, int angle) {
  angle = constrain(angle, 0, 180);
  pwm.setPWM(channel, 0, angleToPulse(angle));
  currentAngle[channel] = angle;
}

void moveServoSmooth(uint8_t channel, int targetAngle) {
  targetAngle = constrain(targetAngle, 0, 180);
  int start = currentAngle[channel];
  int step = (start < targetAngle) ? 1 : -1;
  for (int a = start; a != targetAngle; a += step) {
    setServo(channel, a);
    delay(STEP_DELAY);
  }
  setServo(channel, targetAngle);
}

// phi_deg: 0 = horizontal, -90 = pointing down
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

void moveTo(float x, float y, float z, float phi_deg = 90) {
  if (!solveIK(x, y, z, phi_deg)) {
    Serial.println("Target unreachable!");
    return;
  }

  int base = constrain((int)(theta0 + 90), 0, 180);
  int shoulder = constrain((int)(theta1 + 90), 0, 180);
  int elbow = constrain((int)(theta2     ), 0, 180);
  int wrist = constrain((int)(theta3 + 90), 0, 180);

  Serial.print("Angles => base:"); Serial.print(base);
  Serial.print(" shoulder:"); Serial.print(shoulder);
  Serial.print(" elbow:"); Serial.print(elbow);
  Serial.print(" wrist:"); Serial.println(wrist);

  moveServoSmooth(0, base);
  moveServoSmooth(1, shoulder);
  moveServoSmooth(2, elbow);
  moveServoSmooth(3, wrist);
}

void setGripper(int percent) {
  int angle = map(percent, 0, 100, 30, 150);
  moveServoSmooth(4, angle);
}

void demoSequence() {
  setGripper(100);
  moveTo(100, 0, 80, 90); // horizontal
  delay(1000); 
  moveTo(100, 80, 80, 90);   
  delay(1000);
  moveTo(80, 0, 60, 0); // pointing down   
  delay(1000);
  setGripper(0);            
  delay(500);
  setGripper(100);
}

void handleSerial() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("g ")) {
      setGripper(input.substring(2).toInt());
      return;
    }

    
    int first = input.indexOf(' ');
    int second = input.indexOf(' ', first + 1);
    int third = input.indexOf(' ', second + 1);

    if (first > 0 && second > 0) {
      float x = input.substring(0, first).toFloat();
      float y = input.substring(first + 1, second).toFloat();
      float z = input.substring(second + 1, third > 0 ? third : input.length()).toFloat();
      float phi = third > 0 ? input.substring(third + 1).toFloat() : 0.0;

      Serial.print("Moving to: ");
      Serial.print(x); Serial.print(", ");
      Serial.print(y); Serial.print(", ");
      Serial.print(z); Serial.print(", phi=");
      Serial.println(phi);
      moveTo(x, y, z, phi);
    }
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
  }


}

void loop() {
  handleSerial();
}