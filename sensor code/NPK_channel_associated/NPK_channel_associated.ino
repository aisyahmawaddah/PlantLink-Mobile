#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid     = "aisyah";
const char* password = "aisyahmawaddah3";

// PlantLink server URL
const char* serverURL = "http://plantlink.xyz/sensor/new_data/";

// API Key - shared across all sensors on this channel
const char* API_KEY = "pineapplesoil";

// RS-485 pins
#define RXD2    16  // RX2 on your board
#define TXD2    17  // TX2 on your board
#define RE_PIN  4   // D4
#define DE_PIN  2   // D2

// NPK query command
byte npkQuery[] = {0x01, 0x03, 0x00, 0x00, 0x00, 0x03, 0x05, 0xCB};

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);
  pinMode(RE_PIN, OUTPUT);
  pinMode(DE_PIN, OUTPUT);
  digitalWrite(RE_PIN, LOW);
  digitalWrite(DE_PIN, LOW);

  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
}

void loop() {
  // Send query to NPK sensor
  digitalWrite(RE_PIN, HIGH);
  digitalWrite(DE_PIN, HIGH);
  delay(10);
  Serial2.write(npkQuery, sizeof(npkQuery));
  Serial2.flush();
  delay(10);
  digitalWrite(RE_PIN, LOW);
  digitalWrite(DE_PIN, LOW);

  // Read response
  delay(300);
  byte response[11];
  int idx = 0;
  unsigned long startTime = millis();
  while (millis() - startTime < 1000 && idx < 11) {
    if (Serial2.available()) {
      response[idx++] = Serial2.read();
    }
  }

  // Check response
  if (idx < 11) {
    Serial.println("ERROR: Incomplete response");
    Serial.println("Try changing 9600 to 4800");
    delay(5000);
    return;
  }

  // Extract values
  int nitrogen    = (response[3] << 8) | response[4];
  int phosphorous = (response[5] << 8) | response[6];
  int potassium   = (response[7] << 8) | response[8];

  Serial.printf("Nitrogen:    %d mg/kg\n", nitrogen);
  Serial.printf("Phosphorous: %d mg/kg\n", phosphorous);
  Serial.printf("Potassium:   %d mg/kg\n", potassium);

  // Send to PlantLink
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<200> doc;
    doc["API_KEY"]     = API_KEY;
    doc["nitrogen"]    = nitrogen;
    doc["phosphorous"] = phosphorous;
    doc["potassium"]   = potassium;
    doc["sensor_type"] = "NPK";
    String body;
    serializeJson(doc, body);

    int code = http.POST(body);
    Serial.printf("PlantLink response: %d\n", code);
    if (code == 200 || code == 201) {
      Serial.println("Data sent successfully!");
    } else {
      Serial.println("Failed to send, check API key and server URL");
    }

    http.end();
  }

  delay(15000);
}
