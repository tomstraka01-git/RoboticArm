# Robotic Arm

Robotic arm is a  project about making my own robotic arm from scratch. I designed the arm from scratch and i plan to 3D print the file. Both firmware codes are written by me. The C++ code will run on  microcontroller, i will be using pico 2. The python code can be run on any computer wich can run python files. 

## Operation
First assemble the arm and try to set the servos in 90 degrees position. Then compile the code and wire everything together. After that run the python code and connnect the microcontroller via usb to your computer. Then use the python code to operate it, send signals, set position and record position. The main inverse and forward kinematics run on the pc, the c++ microcontroller code just recieves the serial commands. 

![Logo](screenshots/ProjectScreenshot12.png)

## Circuit
The circuit consists of a microcontroller, can be any but i chose pico 2. A PCA9685 servo driver servos, exteral power source and i pcb i will use from my other project. Connect servos to the pcb pins, and connect gnd to gnd and 5V to pcb 5V. Connect signal pins from pcb pins to PCA9685 signal pins. Connect sda scl and power pins from pico 2 to PCA9685. Then upload the code and turn on the power supply. The power supply should be able to handle around 5v 10 amps for safety.

![Logo](screenshots/DiagramStatisRobotArm.png)

## Why?
Why would i want to build this arm? Because it is a great learning oppurtunity that can teach me many new things. It is also a challange for me, because it is one of my first big projects. I also need a small assistant to help me move things around my desk.

![Logo](screenshots/ProjectScreenshot11.png)

![Logo](screenshots/ProjectScreenshot1.png)

![Logo](screenshots/ProjectScreenshot8.png)

![Logo](screenshots/ProjectScreenshot9.png)

![Logo](screenshots/ProjectScreenshot7.png)

![Logo](screenshots/ProjectScreenshot6.png)

Made by Tomáš Straka for Statis Hackathon by hackclub.
