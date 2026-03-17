/*
 * ESP32 IoT Air Quality Monitor - Web Client
 * Sends sensor data to Flask web server via HTTP POST
 * 
 * Hardware Setup:
 * - DHT22: GPIO 4 (VCC → 3.3V, GND, DATA)
 * - MQ-135: GPIO 34 (VCC → 5V, GND, AOUT)
 * - Buzzer: GPIO 5 (VCC → 3.3V, GND, Signal)
 * 
 * Features:
 * - WiFi connectivity
 * - Automatic sensor reading every 5 seconds
 * - HTTP POST to Flask server
 * - Buzzer alerts for poor air quality
 * - Automatic reconnection on failure
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ==================== CONFIGURATION ====================
// WiFi Credentials (CHANGE THESE!)
const char* WIFI_SSID = "Moto";
const char* WIFI_PASSWORD = "12345678";

// Server Configuration (CHANGE THIS!)
const char* SERVER_URL = "http://10.112.237.217:5000/api/predict";  // Your computer's IP address
const char* DEVICE_ID = "ESP32_001";  // Unique device identifier

// Pin Definitions
#define DHTPIN 4
#define DHTTYPE DHT11
#define MQ135_PIN 34
#define BUZZER_PIN 5

// Timing Configuration
const unsigned long READ_INTERVAL = 5000;       // 5 seconds between readings
const unsigned long WIFI_TIMEOUT = 20000;       // 20 seconds WiFi connection timeout
const unsigned long HTTP_TIMEOUT = 10000;       // 10 seconds HTTP request timeout

// Air Quality Thresholds
const int AQI_GOOD_THRESHOLD = 300;
const int AQI_MODERATE_THRESHOLD = 400;
const int AQI_UNHEALTHY_THRESHOLD = 500;

// ==================== GLOBAL VARIABLES ====================
DHT dht(DHTPIN, DHTTYPE);
unsigned long lastReadTime = 0;
unsigned long readingCount = 0;
bool wifiConnected = false;

// ==================== FUNCTION PROTOTYPES ====================
void setupWiFi();
void reconnectWiFi();
void readSensorsAndSend();
void triggerBuzzer(int beeps);
String getAQICategory(int mq135Value);

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("\n╔═══════════════════════════════════════════════════════════╗");
  Serial.println("║   ESP32 IoT Air Quality Monitor - Web Client v2.0       ║");
  Serial.println("╚═══════════════════════════════════════════════════════════╝\n");
  
  // Initialize sensors
  Serial.println("🔧 Initializing sensors...");
  dht.begin();
  pinMode(MQ135_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  Serial.println("✓ Sensors initialized\n");
  
  // Connect to WiFi
  setupWiFi();
  
  // Success beep
  triggerBuzzer(1);
  
  Serial.println("\n✓ System ready! Starting sensor readings...\n");
}

// ==================== MAIN LOOP ====================
void loop() {
  unsigned long currentTime = millis();
  
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    wifiConnected = false;
    Serial.println("⚠️ WiFi connection lost! Reconnecting...");
    reconnectWiFi();
  } else {
    wifiConnected = true;
  }
  
  // Read sensors and send data at regular intervals
  if (currentTime - lastReadTime >= READ_INTERVAL) {
    lastReadTime = currentTime;
    readSensorsAndSend();
  }
  
  delay(100);
}

// ==================== WIFI SETUP ====================
void setupWiFi() {
  Serial.println("📡 Connecting to WiFi...");
  Serial.print("   SSID: ");
  Serial.println(WIFI_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  unsigned long startAttemptTime = millis();
  
  while (WiFi.status() != WL_CONNECTED && 
         millis() - startAttemptTime < WIFI_TIMEOUT) {
    delay(500);
    Serial.print(".");
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("\n✓ WiFi connected successfully!");
    Serial.print("   IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("   Signal Strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm\n");
  } else {
    wifiConnected = false;
    Serial.println("\n✗ WiFi connection failed!");
    Serial.println("   Check your SSID and password in the code\n");
  }
}

// ==================== WIFI RECONNECT ====================
void reconnectWiFi() {
  WiFi.disconnect();
  delay(1000);
  setupWiFi();
}

// ==================== READ SENSORS AND SEND DATA ====================
void readSensorsAndSend() {
  readingCount++;
  
  Serial.println("─────────────────────────────────────────────────────────");
  Serial.print("📊 Reading #");
  Serial.print(readingCount);
  Serial.print("  |  Time: ");
  Serial.print(millis() / 1000);
  Serial.println(" seconds");
  Serial.println("─────────────────────────────────────────────────────────");
  
  // Read DHT22 sensor
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  // Check DHT22 reading
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("✗ ERROR: Failed to read DHT22 sensor!");
    Serial.println("   Check wiring: VCC → 3.3V, GND, DATA → GPIO 4\n");
    return;
  }
  
  // Read MQ-135 sensor
  int mq135Raw = analogRead(MQ135_PIN);
  float mq135Voltage = (mq135Raw / 4095.0) * 3.3;
  
  // Display sensor readings
  Serial.print("🌡️  Temperature:  ");
  Serial.print(temperature, 1);
  Serial.println(" °C");
  
  Serial.print("💧 Humidity:     ");
  Serial.print(humidity, 1);
  Serial.println(" %");
  
  Serial.print("🏭 Air Quality:  ");
  Serial.print(mq135Raw);
  Serial.print(" (");
  Serial.print(mq135Voltage, 2);
  Serial.print("V) - ");
  Serial.println(getAQICategory(mq135Raw));
  
  // Check air quality and trigger buzzer if needed
  if (mq135Raw > AQI_UNHEALTHY_THRESHOLD) {
    Serial.println("⚠️⚠️⚠️ CRITICAL: UNHEALTHY AIR QUALITY!");
    triggerBuzzer(3);  // 3 beeps for critical
  } else if (mq135Raw > AQI_MODERATE_THRESHOLD) {
    Serial.println("⚠️ WARNING: Moderate air quality");
    triggerBuzzer(2);  // 2 beeps for warning
  } else {
    Serial.println("✓ Air quality is GOOD");
  }
  
  // Send data to server if WiFi is connected
  if (wifiConnected) {
    Serial.println("\n📤 Sending data to server...");
    
    HTTPClient http;
    http.begin(SERVER_URL);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(HTTP_TIMEOUT);
    
    // Create JSON payload
    StaticJsonDocument<256> doc;
    doc["device_id"] = DEVICE_ID;
    doc["temperature"] = round(temperature * 10) / 10.0;
    doc["humidity"] = round(humidity * 10) / 10.0;
    doc["mq135"] = mq135Raw;  // Flask server expects 'mq135' field name
    
    String jsonPayload;
    serializeJson(doc, jsonPayload);
    
    Serial.print("   Payload: ");
    Serial.println(jsonPayload);
    
    // Send HTTP POST request
    int httpResponseCode = http.POST(jsonPayload);
    
    if (httpResponseCode > 0) {
      Serial.print("✓ Server response: ");
      Serial.print(httpResponseCode);
      
      // Get response body for all status codes
      String response = http.getString();
      
      if (httpResponseCode == 200 || httpResponseCode == 201) {
        Serial.println(" - SUCCESS");
        Serial.print("   Response: ");
        Serial.println(response);
        
        // Parse JSON response to get AQI prediction
        StaticJsonDocument<512> responseDoc;
        DeserializationError error = deserializeJson(responseDoc, response);
        
        if (!error && responseDoc.containsKey("prediction")) {
          JsonObject prediction = responseDoc["prediction"];
          if (prediction.containsKey("predicted_aqi")) {
            float predictedAQI = prediction["predicted_aqi"];
            Serial.print("   🎯 Predicted AQI: ");
            Serial.println(predictedAQI, 1);
          }
        }
      } else {
        Serial.println(" - ERROR");
        Serial.println("   ========== SERVER ERROR DETAILS ==========");
        Serial.println(response);
        Serial.println("   ==========================================");
      }
    } else {
      Serial.print("✗ HTTP Error: ");
      Serial.println(httpResponseCode);
      Serial.println("   Check server URL and ensure Flask server is running");
    }
    
    http.end();
  } else {
    Serial.println("\n⚠️ WiFi not connected - data not sent");
  }
  
  Serial.println();
}

// ==================== GET AQI CATEGORY ====================
String getAQICategory(int mq135Value) {
  if (mq135Value < AQI_GOOD_THRESHOLD) {
    return "GOOD";
  } else if (mq135Value < AQI_MODERATE_THRESHOLD) {
    return "MODERATE";
  } else if (mq135Value < AQI_UNHEALTHY_THRESHOLD) {
    return "UNHEALTHY";
  } else {
    return "HAZARDOUS";
  }
}

// ==================== BUZZER CONTROL ====================
void triggerBuzzer(int beeps) {
  for (int i = 0; i < beeps; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(200);
    digitalWrite(BUZZER_PIN, LOW);
    if (i < beeps - 1) {
      delay(300);
    }
  }
}
