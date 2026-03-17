/*
 * ESP32 Local Sensor Reader
 * Reads DHT11 and MQ135 sensors locally via Serial Monitor
 * No WiFi or cloud connection required
 * 
 * Hardware Setup:
 * - DHT11: GPIO 4 (VCC, GND, DATA)
 * - MQ135: GPIO 34 (VCC, GND, AOUT)
 * - HW-512 Buzzer: GPIO 5 (VCC → 3.3V or 5V, GND, Signal)
 * 
 * Use this for:
 * - Local data collection
 * - CSV export to computer
 * - Real-time monitoring without internet
 * - Air quality warnings with buzzer alerts
 */

#include <DHT.h>

// Pin definitions
#define DHTPIN 4
#define DHTTYPE DHT11
#define MQ135_PIN 34
#define BUZZER_PIN 5

DHT dht(DHTPIN, DHTTYPE);

// Configuration
const unsigned long READ_INTERVAL = 5000;  // 5 seconds between readings
unsigned long lastRead = 0;
unsigned long readingNumber = 0;

// Air Quality Threshold
const int AIR_QUALITY_THRESHOLD = 400;  // Warning threshold for MQ135

// Buzzer Configuration (HW-512)
const int BUZZER_BEEP_DURATION = 200;    // Beep duration in ms
const int BUZZER_PAUSE = 300;            // Pause between beeps
const int WARNING_BEEP_PATTERN = 3;      // 3 beeps for warning

// CSV mode flag (set to true for CSV output, false for formatted output)
const bool CSV_MODE = false;

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  // Initialize sensors
  dht.begin();
  pinMode(MQ135_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);  // Ensure HW-512 buzzer is off initially
  
  
  if (!CSV_MODE) {
    // Formatted output header
    Serial.println("\n╔═════════════════════════════════════════════════════════╗");
    Serial.println("║     ESP32 LOCAL SENSOR READER - NO WIFI REQUIRED      ║");
    Serial.println("╚═════════════════════════════════════════════════════════╝");
    Serial.println("\nReading sensors every 5 seconds...\n");
  } else {
    // CSV header
    Serial.println("timestamp_ms,reading_number,temperature_c,humidity_rh,mq135_raw,mq135_voltage,mq135_percent");
  }
}

void loop() {
  unsigned long now = millis();
  
  if (now - lastRead >= READ_INTERVAL) {
    lastRead = now;
    readingNumber++;
    
    // Read sensors
    float temp = dht.readTemperature();
    float hum = dht.readHumidity();
    int mq135 = analogRead(MQ135_PIN);
    float mq135_voltage = (mq135 / 4095.0) * 3.3;
    float mq135_percent = (mq135 / 4095.0) * 100.0;
    
    // Check for sensor errors
    if (isnan(temp) || isnan(hum)) {
      if (!CSV_MODE) {
        Serial.println("✗ ERROR: DHT sensor read failed!");
      }
      return;
    }
    
    // Check air quality threshold
    bool airQualityWarning = (mq135 > AIR_QUALITY_THRESHOLD);
    
    // Control HW-512 buzzer based on air quality
    if (airQualityWarning) {
      // Trigger warning beep pattern (3 beeps)
      for (int i = 0; i < WARNING_BEEP_PATTERN; i++) {
        digitalWrite(BUZZER_PIN, HIGH);
        delay(BUZZER_BEEP_DURATION);
        digitalWrite(BUZZER_PIN, LOW);
        if (i < WARNING_BEEP_PATTERN - 1) {
          delay(BUZZER_PAUSE);
        }
      }
    } else {
      digitalWrite(BUZZER_PIN, LOW);   // Ensure buzzer is off
    }
    
    // Output data
    if (CSV_MODE) {
      // CSV format - easy to import into Excel/Python
      Serial.print(now);
      Serial.print(",");
      Serial.print(readingNumber);
      Serial.print(",");
      Serial.print(temp, 2);
      Serial.print(",");
      Serial.print(hum, 2);
      Serial.print(",");
      Serial.print(mq135);
      Serial.print(",");
      Serial.print(mq135_voltage, 3);
      Serial.print(",");
      Serial.print(mq135_percent, 2);
      Serial.print(",");
      Serial.println(airQualityWarning ? "WARNING" : "OK");
    } else {
      // Formatted output - easy to read
      Serial.println("─────────────────────────────────────────────────────────");
      Serial.print("📊 Reading #");
      Serial.print(readingNumber);
      Serial.print("  |  Time: ");
      Serial.print(now / 1000);
      Serial.println(" seconds");
      Serial.println("─────────────────────────────────────────────────────────");
      Serial.print("  🌡️  Temperature:  ");
      Serial.print(temp, 1);
      Serial.println(" °C");
      Serial.print("  💧 Humidity:     ");
      Serial.print(hum, 1);
      Serial.println(" %");
      Serial.print("  🏭 MQ135 Raw:    ");
      Serial.print(mq135);
      Serial.print(" / ");
      Serial.print(AIR_QUALITY_THRESHOLD);
      Serial.print("  (");
      Serial.print(mq135_voltage, 2);
      Serial.print("V, ");
      Serial.print(mq135_percent, 1);
      Serial.println("%)");
      
      // Air quality warning
      if (airQualityWarning) {
        Serial.println("\n╔════════════════════════════════════════════════════════╗");
        Serial.println("║  ⚠️⚠️⚠️  CRITICAL: AIR QUALITY WARNING!  ⚠️⚠️⚠️        ║");
        Serial.println("╚════════════════════════════════════════════════════════╝");
        Serial.print("  MQ135 Reading: ");
        Serial.print(mq135);
        Serial.print(" > Threshold: ");
        Serial.println(AIR_QUALITY_THRESHOLD);
        Serial.println("  ⚠️  ACTION REQUIRED: Ventilate the area immediately!");
        Serial.println("════════════════════════════════════════════════════════");
      } else {
        Serial.println("  ✓ Air Quality: NORMAL");
      }
      Serial.println();
    }
  }
}
