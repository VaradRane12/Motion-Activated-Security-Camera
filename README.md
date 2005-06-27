# Motion‑Activated Security Camera

A DIY motion-triggered surveillance system using Raspberry Pi and NodeMCU. This project captures video/images on motion detection, uploads to AWS or your local server, and provides a web interface using Flask.


## 🚀 Features
- 🎥 Motion-triggered video/image capture
- 🌐 Flask web interface to control and monitor
- ☁️ AWS S3 integration for cloud storage 
- 🔌 NodeMCU-based light & PIR sensor logic
- 📹 Raspberry Pi camera motion detection
- 🕹️ Remote pause/resume of motion detection

## 📁 Project Structure
```
Motion-Activated-Security-Camera/
├── flask/                    # Flask backend for web control
├── nodemcu/                  # NodeMCU firmware (C++/Arduino)
├── aws.py                    # Uploads files to AWS S3
├── script.py                 # Main motion detection and camera logic
├── Light_timed_switch.py     # Light control logic (optional)
├── requirements.txt          # Python dependencies
├── DOCUMENTATION/            # Additional docs or diagrams
└── README.md                 # You’re here!
```

## ⚙️ Requirements

### 🔧 Hardware
- Raspberry Pi (with PiCamera module)
- NodeMCU (ESP8266)
- PIR Motion Sensor
- Jumper wires, Breadboard
- LED, Relay module (optional for light control)

### 💻 Software
- Python 3.x
- Flask
- OpenCV
- boto3 (for AWS)
- RPi.GPIO
- picamera2

Install dependencies:
```bash
pip3 install -r requirements.txt
```

## 🛠️ Setup Instructions

### 1. Hardware Wiring

**Raspberry Pi**:
- PIR sensor signal to GPIO 17 (can be changed in code)
- PiCamera connected via ribbon cable

**NodeMCU**:
- PIR sensor to D5
- Optional: Relay for light control to D6

### 2. Flask Web Server
```bash
cd flask
flask run --host=0.0.0.0 --port=5000
```

### 3. Run Motion Detection Script
```bash
python3 script.py
```

### 4. NodeMCU Firmware
- Flash the code in `nodemcu/` using Arduino IDE
- Update Wi-Fi SSID, password, and Flask server IP in the code

### 5. AWS Setup (Optional)
- Add your AWS credentials in `aws.py`
- Set your bucket name and region

## ▶️ Usage Flow

1. System starts and monitors motion  
2. On detection:
   - Starts video recording or takes a photo
   - Uploads it to AWS or stores locally  
3. Flask server UI allows:
   - Live camera feed  
   - Pause/resume surveillance  
   - Light/siren toggle  

## 🧪 Example Config (Python)
```python
# script.py
PAUSE_FLAG_PATH = "/home/pi/motion_pause.flag"
RECORD_DURATION = 10  # seconds
CAMERA_RESOLUTION = (1280, 720)
UPLOAD_TO_AWS = True
```

## 💡 Troubleshooting

| Problem              | Solution                                                |
|----------------------|---------------------------------------------------------|
| PIR stays HIGH       | Ensure mode pins (L, MD, H) are configured correctly    |
| Camera not working   | Enable camera with `raspi-config`                       |
| No upload            | Check AWS credentials in `aws.py`                       |
| Buttons not toggling | Ensure JS and Flask state variables are aligned         |

## 📷 Screenshots / Media
*(Add wiring diagrams, screenshots, or demo videos here later)*

## 📜 License
MIT License  
Feel free to use, modify, and share.

## 🤝 Contributing

Pull requests are welcome!  
To contribute:

1. Fork the repo  
2. Create a new branch  
3. Make your changes  
4. Open a PR with a meaningful description

## 🙌 Credits
Developed by [Varad Rane](https://github.com/VaradRane12)
