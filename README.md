# Robotic Arm

Robotic arm is a  project about making my own robotic arm from scratch. I designed the arm from scratch and i plan to 3D print the file. Both firmware codes are written by me. The C++ code will run on  microcontroller, i will be using pico 2. The python code can be run on any computer wich can run python files. 

## Operation
First assemble the arm and try to set the servos in 90 degrees position. Then compile the code and wire everything together. After that run the python code and connnect the microcontroller via usb to your computer. Then use the python code to operate it, send signals, set position and record position. The main inverse and forward kinematics run on the pc, the c++ microcontroller code just recieves the serial commands. It uses cosine ease when animating through the listbox to make the movement seems smooth, moves nonlinearly.

### Keybinds
Use keybinds to control the robotic arm easily.
```
[t]: increments the time by 0.5 seconds
[q]: closes the serial port and GUI
[l]: loads animation
[s]: saves animation
[space]: animates smoothly through loaded positions or angles
[r]: records the current position onto the listbox
```
![Logo](screenshots/ProjectScreenshot12.png)
## What can it do?
You can set positions manually, record and play animations, pick up objects, use it to help you in your everyday life.


## Circuit
The circuit consists of a microcontroller, can be any but i chose pico 2. A PCA9685 servo driver servos, exteral power source and i pcb i will use from my other project. Connect servos to the pcb pins, and connect gnd to gnd and 5V to pcb 5V. Connect signal pins from pcb pins to PCA9685 signal pins. Connect sda scl and power pins from pico 2 to PCA9685. Then upload the code and turn on the power supply. The power supply should be able to handle around 5v 10 amps for safety.

![Logo](screenshots/DiagramStatisRobotArm.png)

## How to print?
If you want to replicate the project, you need to buy simillar servos, use some i2c pwm generation module and some circuit to distribute the power. For printing downooad the 3d print file, and use a 3d printer, that has over 400mm print surface. I want to use pla, because it is cheap and okay for my project. You can use other filaments if you want. For my printer, Prusa XL, the slicer says that it would take 22 hours to print and 300 grams to print. Use any microcontroller wich has i2c and serial communication, upload the code and connect it via usb to pc running the python file. Then it should work.

## Why?
Why would i want to build this arm? Because it is a great learning oppurtunity that can teach me many new things. It is also a challange for me, because it is one of my first big projects. I also need a small assistant to help me move things around my desk.

![Logo](screenshots/ProjectScreenshot11.png)

![Logo](screenshots/ProjectScreenshot1.png)

![Logo](screenshots/ProjectScreenshot8.png)

![Logo](screenshots/ProjectScreenshot9.png)

![Logo](screenshots/ProjectScreenshot7.png)

![Logo](screenshots/ProjectScreenshot6.png)

Made by Tomáš Straka for Statis Hackathon by hackclub.
