# project-5
# Intelligent Robot Car with Face Recognition and Privacy Protection

This project implements an intelligent robot car system that integrates real-time face recognition and feature-level privacy protection. The system is developed using a K210 AI Vision Module for visual perception and a Micro:bit V2 for robot control.

---

## 1. Project Overview

The robot car is capable of detecting and recognizing human faces in real time. To protect biometric privacy, facial feature vectors are not stored or transmitted directly. Instead, feature-level SHA-256 hashing is applied to ensure that biometric data cannot be reconstructed or misused.

The project demonstrates a complete Sense–Process–Act workflow on an embedded edge-AI platform, combining hardware control, AI inference, and privacy-aware system design.

---

## 2. Hardware Components

The hardware platform consists of the following components:

- Micro:bit V2 (robot motion control)
- K210 AI Vision Module with camera and LCD
- Robot car chassis with DC motors and wheels
- Motor driver expansion board
- Lithium battery for power supply
- MicroSD card for AI model storage

---

## 3. Software Architecture

The system is divided into two independent software modules to ensure modularity and stability.

### 3.1 K210 AI Vision Module

- Programming language: MicroPython (MaixPy)
- Main file: main.py

Main functionalities include:
- Camera sensor and LCD initialization
- Face detection using a YOLO-based model
- Facial landmark detection and face alignment
- Facial feature extraction using KPU acceleration
- Feature-level SHA-256 hashing for privacy protection
- Real-time face recognition and on-screen output

### 3.2 Micro:bit Control Module

- Development platform: Microsoft MakeCode
- Compiled file: microbit-TianciZeng.hex

Main functionalities include:
- Motor control logic
- Basic robot movement (forward, stop)
- User feedback through LEDs or sound

---

## 4. File Structure

The project files are organized as follows:
project_root/
│
├── main.py # K210 AI vision and recognition program
├── README.md # Project documentation
├── microbit-TianciZeng.hex # Micro:bit robot control program
## 5. Deployment Instructions

### 5.1 K210 Setup

1. Copy the KPU and k210 directories to the root directory of the MicroSD card.
2. Insert the MicroSD card into the K210 module.
3. Copy main.py to the K210 filesystem.
4. Power on the K210 module to start the AI vision program.

### 5.2 Micro:bit Setup

1. Connect the Micro:bit V2 to a computer using a USB cable.
2. Drag and drop microbit-TianciZeng.hex onto the Micro:bit drive.
3. Disconnect the Micro:bit and power the robot car.

---

## 6. Usage Instructions

1. Power on the robot car system.
2. The K210 module will automatically initialize the camera and start face detection.
3. When a face is detected, a bounding box is displayed on the LCD screen.
4. Facial features are extracted and converted into SHA-256 hash values.
5. Press the registration button to register a new user.
6. The system compares incoming faces with registered users and provides real-time recognition feedback.

---

## 7. Privacy Protection Mechanism

To ensure biometric privacy, the system does not store raw facial images or numerical feature vectors externally. Facial features are serialized and processed using the SHA-256 cryptographic hash algorithm, producing irreversible hash values.

This approach ensures that biometric data cannot be reconstructed or misused while maintaining effective face recognition performance.

---

## 8. Project Deliverables

The final project submission includes:

- main.py – K210 AI vision and privacy protection implementation
- microbit-TianciZeng.hex – Micro:bit robot control program
- README.md – Project documentation
- Technical report (PDF)
- Demonstration video

---

## 9. Notes

- Ensure sufficient lighting for stable face detection.
- Do not remove the SD card during system operation.
- AI model files must match the K210 firmware version.

---

## 10. License

This project is developed for educational and experimental purposes only.
