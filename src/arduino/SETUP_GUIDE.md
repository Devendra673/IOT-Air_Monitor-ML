# ESP32 Setup Guide - Web Client

## 📋 Overview
This guide will help you upload the Arduino code to your ESP32 and connect it to your Flask web server.

---

## 🔧 Hardware Requirements

- **ESP32 Development Board**
- **DHT22 Temperature & Humidity Sensor**
- **MQ-135 Air Quality Sensor**
- **Buzzer** (optional, for alerts)
- **Breadboard and jumper wires**
- **USB Cable** (for programming ESP32)

---

## 📌 Wiring Diagram

### DHT22 Sensor
```
DHT11 Pin    →    ESP32 Pin
VCC          →    3.3V
GND          →    GND
DATA         →    GPIO 4
```

### MQ-135 Sensor
```
MQ-135 Pin   →    ESP32 Pin
VCC          →    5V (or VIN)
GND          →    GND
AOUT         →    GPIO 34 (ADC1)
```

### Buzzer (Optional)
```
Buzzer Pin   →    ESP32 Pin
Positive (+) →    GPIO 5
Negative (-) →    GND
```

**Note:** If using an active buzzer, connect directly. If using a passive buzzer, you may need a transistor.

---

## 💻 Software Setup

### 1. Install Arduino IDE
- Download from: https://www.arduino.cc/en/software
- Install version 2.0 or higher

### 2. Install ESP32 Board Support
1. Open Arduino IDE
2. Go to **File → Preferences**
3. In "Additional Board Manager URLs", add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Go to **Tools → Board → Boards Manager**
5. Search for "esp32"
6. Install "ESP32 by Espressif Systems"

### 3. Install Required Libraries
Go to **Tools → Manage Libraries** and install:
- **DHT sensor library** by Adafruit (also install dependencies)
- **ArduinoJson** by Benoit Blanchon (version 6.x)
- **HTTPClient** (usually pre-installed with ESP32 board)

---

## ⚙️ Configuration

### 1. Find Your Computer's IP Address

**Windows:**
```bash
ipconfig
```
Look for "IPv4 Address" under your active network connection (e.g., 192.168.1.100)

**Mac/Linux:**
```bash
ifconfig
```
or
```bash
ip addr show
```

### 2. Configure the Arduino Code

Open `web_client.ino` and modify these lines:

```cpp
// WiFi Credentials (CHANGE THESE!)
const char* WIFI_SSID = "YOUR_WIFI_SSID";          // Your WiFi network name
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";  // Your WiFi password

// Server Configuration (CHANGE THIS!)
const char* SERVER_URL = "http://192.168.1.100:5000/api/predict";  // Your computer's IP
const char* DEVICE_ID = "ESP32_001";  // Give it a unique name
```

**Example Configuration:**
```cpp
const char* WIFI_SSID = "MyHomeWiFi";
const char* WIFI_PASSWORD = "MySecurePassword123";
const char* SERVER_URL = "http://192.168.1.105:5000/api/predict";
const char* DEVICE_ID = "ESP32_LivingRoom";
```

### 3. Adjust Thresholds (Optional)

You can customize air quality thresholds:
```cpp
const int AQI_GOOD_THRESHOLD = 300;       // Below this = GOOD
const int AQI_MODERATE_THRESHOLD = 400;   // Above this = MODERATE
const int AQI_UNHEALTHY_THRESHOLD = 500;  // Above this = UNHEALTHY
```

---

## 📤 Upload Code to ESP32

1. **Connect ESP32** to your computer via USB
2. **Select Board:**
   - Go to **Tools → Board → ESP32 Arduino**
   - Choose your ESP32 board (e.g., "ESP32 Dev Module")
3. **Select Port:**
   - Go to **Tools → Port**
   - Select the COM port (Windows) or /dev/ttyUSB0 (Linux/Mac)
4. **Configure Upload Settings:**
   - Upload Speed: 115200
   - Flash Frequency: 80MHz
   - Flash Mode: QIO
   - Partition Scheme: Default
5. **Click Upload** button (→ arrow icon)
6. Wait for "Done uploading" message

---

## 🔍 Testing & Monitoring

### 1. Open Serial Monitor
- Go to **Tools → Serial Monitor**
- Set baud rate to **115200**

### 2. Expected Output
You should see:
```
╔═══════════════════════════════════════════════════════════╗
║   ESP32 IoT Air Quality Monitor - Web Client v2.0       ║
╚═══════════════════════════════════════════════════════════╝

🔧 Initializing sensors...
✓ Sensors initialized

📡 Connecting to WiFi...
   SSID: MyHomeWiFi
......
✓ WiFi connected successfully!
   IP Address: 192.168.1.150
   Signal Strength: -45 dBm

✓ System ready! Starting sensor readings...

─────────────────────────────────────────────────────────
📊 Reading #1  |  Time: 5 seconds
─────────────────────────────────────────────────────────
🌡️  Temperature:  24.5 °C
💧 Humidity:     55.2 %
🏭 Air Quality:  285 (0.23V) - GOOD
✓ Air quality is GOOD

📤 Sending data to server...
   Payload: {"device_id":"ESP32_001","temperature":24.5,"humidity":55.2,"mq135":285}
✓ Server response: 201 - SUCCESS
   Response: {"status":"success","prediction":{"predicted_aqi":65.3}}
   🎯 Predicted AQI: 65.3
```

### 3. Check Flask Dashboard
- Open your browser
- Go to http://localhost:5000
- Login with **admin / admin123**
- You should see live data on the dashboard!

---

## 🐛 Troubleshooting

### ❌ WiFi Connection Failed
**Symptom:** `✗ WiFi connection failed!`

**Solutions:**
1. Double-check WiFi SSID and password (case-sensitive!)
2. Make sure ESP32 is within WiFi range
3. Check if your WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
4. Try putting WiFi credentials in quotes: `"MyWiFi"`

### ❌ HTTP Error
**Symptom:** `✗ HTTP Error: -1` or `✗ HTTP Error: 404`

**Solutions:**
1. Verify Flask server is running (`python run.py`)
2. Check your computer's IP address hasn't changed
3. Make sure both ESP32 and computer are on same WiFi network
4. Try accessing `http://YOUR_IP:5000` in your browser first
5. Check Windows Firewall isn't blocking port 5000

### ❌ Sensor Reading Failed
**Symptom:** `✗ ERROR: Failed to read DHT22 sensor!`

**Solutions:**
1. Check DHT22 wiring (VCC → 3.3V, not 5V!)
2. Verify DATA pin is connected to GPIO 4
3. Add 10kΩ pull-up resistor between DATA and VCC
4. Try powering ESP32 from external 5V supply (not just USB)

### ❌ MQ-135 Always Reads 0
**Solutions:**
1. MQ-135 needs warm-up time (24-48 hours for accurate readings)
2. Check wiring (AOUT → GPIO 34, VCC → 5V)
3. Make sure you're reading AOUT pin, not DOUT

### ❌ Upload Failed
**Solutions:**
1. Hold BOOT button while uploading
2. Try different USB cable (some cables are power-only)
3. Install CH340 or CP2102 USB drivers
4. Lower upload speed to 921600 or 460800

---

## 📊 Understanding the Data

### Air Quality Categories
- **GOOD** (< 300): Safe air quality
- **MODERATE** (300-400): Acceptable, sensitive people should limit prolonged outdoor exposure
- **UNHEALTHY** (400-500): Everyone may begin to experience health effects
- **HAZARDOUS** (> 500): Health alert, everyone may experience serious health effects

### Buzzer Alerts
- **1 beep**: System startup successful
- **2 beeps**: Moderate air quality (warning)
- **3 beeps**: Unhealthy air quality (critical alert)

---

## 🔄 Device Registration

First time connecting a new device:
1. Device sends data to `/api/predict`
2. Server automatically registers device with ID
3. View registered devices on **Devices** page in dashboard
4. Device will show as "Online" when sending data

---

## 📖 Additional Tips

### Reading Interval
Default is 5 seconds. To change:
```cpp
const unsigned long READ_INTERVAL = 10000;  // 10 seconds
```

### Multiple Devices
Deploy multiple ESP32 units by changing device ID:
```cpp
const char* DEVICE_ID = "ESP32_Bedroom";
const char* DEVICE_ID = "ESP32_Kitchen";
const char* DEVICE_ID = "ESP32_Office";
```

### Power Options
- **USB Power**: Good for testing
- **5V Adapter**: Better for 24/7 operation
- **Battery**: Use with deep sleep mode (requires code modification)

---

## 🚀 Next Steps

1. ✅ Upload code and verify serial monitor output
2. ✅ Check device appears on dashboard
3. ✅ Monitor real-time readings
4. ✅ Test alert system by blowing on MQ-135
5. ✅ Set up email notifications in Settings page
6. ✅ Export historical data for analysis

---

## 📞 Support

If you encounter issues:
1. Check serial monitor for error messages
2. Verify all wiring connections
3. Ensure Flask server is running
4. Check network connectivity (ping computer's IP from another device)
5. Review this guide's troubleshooting section

Happy monitoring! 🌱
