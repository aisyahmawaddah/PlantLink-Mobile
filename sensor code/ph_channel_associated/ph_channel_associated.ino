#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
const char* ssid = "M403163@Rate One";            // WiFi network SSID
const char* password = "wifipw_M403163";       // WiFi network password
const char* API_KEY = "TF8FANKKYQSKC1W";       // WiFi network password
// const char* server = "103.144.185.242";  // Public IP address of your Django server
WiFiClient client;
HTTPClient http;
const int port = 8000;                   // Port number your Django server is listening on
const char *base_rest_url = "http://192.168.100.6:8000/";  // Endpoint on your Django server to send data

#define SensorPin A0                  // pH meter Analog output connected to Arduino's Analog A0 pin
unsigned long int avgValue;           // Store the average value of the sensor feedback
float b;
int buf[10], temp;

void setup()
{
  pinMode(13, OUTPUT);
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
}

void loop()
{
  if (WiFi.status() == WL_CONNECTED) {
    // WiFi is connected, proceed with sensor reading and data sending
    for (int i = 0; i < 10; i++) {    // Get 10 sample values from the sensor for smoothing
      buf[i] = analogRead(SensorPin);
      delay(10);
    }
    for (int i = 0; i < 9; i++) {      // Sort the analog values from small to large
      for (int j = i + 1; j < 10; j++) {
        if (buf[i] > buf[j]) {
          temp = buf[i];
          buf[i] = buf[j];
          buf[j] = temp;
        }
      }
    }
    avgValue = 0;
    for (int i = 2; i < 8; i++) {                    // Take the average value of 6 center samples
      avgValue += buf[i];
    }
    float phValue = (float)avgValue * 5.0 / 1024 / 6; // Convert the analog into millivolt
    phValue = 3.5 * phValue;                          // Convert the millivolt into pH value

    // Print pH value to serial monitor
    Serial.print("pH:");
    Serial.println(phValue, 2);
    if(phValue>0){
      StaticJsonDocument<200> jsonDoc;
      jsonDoc["phValue"] = phValue;
      jsonDoc["API_KEY"] = API_KEY;
      String jsonData;
      serializeJson(jsonDoc, jsonData);

      // Send data to Node.js server via HTTP POST
      String url = String(base_rest_url) + "sensor/ph_sensor_data/";
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
    }else {
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
