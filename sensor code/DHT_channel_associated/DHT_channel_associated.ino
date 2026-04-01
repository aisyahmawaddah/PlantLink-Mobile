#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

const char *ssid = "M403163@Rate One";
const char *password = "wifipw_M403163";
const char *base_rest_url = "http://192.168.100.6:8000/";
const char *API_KEY="W7XH3T9GJMNNKDG";
WiFiClient client;
HTTPClient http;

#define DHTPIN D4    // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11 // DHT sensor type (DHT11, DHT21, DHT22)

DHT dht(DHTPIN, DHTTYPE);
unsigned long int avgHumidity;
unsigned long int avgTemperature;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(9600);
  delay(1000);  // Give some time to open the serial monitor
  Serial.println("Connecting to WiFi...");

  // Connect to WiFi network
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  dht.begin();  // Initialize DHT sensor
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    // WiFi is connected, proceed with sensor reading and data sending
    float humidityValue = 0;
    float temperatureValue = 0;
    int validReadings = 0;

    // Take 10 sample readings and calculate average
    for (int i = 0; i < 10; i++) {
      delay(1000);  // Delay 1 second between readings

      float humidity = dht.readHumidity();
      float temperature = dht.readTemperature();

      // Check if readings are valid (not NaN)
      if (!isnan(humidity) && !isnan(temperature)) {
        humidityValue += humidity;
        temperatureValue += temperature;
        validReadings++;
      }
    }

    if (validReadings > 0) {
      avgHumidity = humidityValue / validReadings;
      avgTemperature = temperatureValue / validReadings;

      Serial.print("Average Humidity: ");
      Serial.println(avgHumidity);
      Serial.print("Average Temperature: ");
      Serial.println(avgTemperature);

      // Send humidity and temperature data to Django server

      // Construct JSON data for sending to server
      StaticJsonDocument<200> jsonDoc;
      jsonDoc["humidity"] = avgHumidity;
      jsonDoc["temperature"] = avgTemperature;
      jsonDoc["API_KEY"] = API_KEY;

      String jsonData;
      serializeJson(jsonDoc, jsonData);

      // Send data to Node.js server via HTTP POST
      String url = String(base_rest_url) + "sensor/dht_sensor/";
      http.begin(client, url);
      http.addHeader("Content-Type", "application/json");
      int httpResponseCode = http.POST(jsonData);

      if (httpResponseCode > 0) {
          String response = http.getString();
          Serial.println(response);
      } else {
          Serial.print("Error in HTTP POST: ");
          Serial.println(httpResponseCode);
      }

      http.end();

      Serial.println(httpResponseCode);
    } else {
      Serial.println("Invalid readings (NaN). Skipping data transmission.");
    }

    // Add a delay before next iteration
    delay(5000);  // Adjust this delay as needed
  } else {
    Serial.println("WiFi not connected. Reconnecting...");
    // Reconnect to WiFi network
    WiFi.begin(ssid, password);
  }
}