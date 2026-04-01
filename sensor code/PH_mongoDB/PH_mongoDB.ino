#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* ssid = "M403163@Rate One";            // WiFi network SSID
const char* password = "wifipw_M403163";       // WiFi network password
// const char* server = "103.144.185.242";  // Public IP address of your Django server

const int port = 8000;                   // Port number your Django server is listening on
const char* endpoint = "/sensor/arduino_data/";  // Endpoint on your Django server to send data

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

    // Send pH value to Django server
    sendToServer(phValue);

    // Add a delay before next iteration
    delay(5000);  // Adjust this delay as needed
  } else {
    Serial.println("WiFi not connected. Reconnecting...");
    // Reconnect to WiFi network
    WiFi.begin(ssid, password);
  }
}

void sendToServer(float value)
{
  WiFiClient client;
  IPAddress server(192, 168, 100, 49);
  if (client.connect(server, port)) {
    // Connected to server
    Serial.println("Connected to server.");
    // Construct the HTTP POST request
    String postRequest = "POST ";
    postRequest += endpoint;
    postRequest += " HTTP/1.1\r\n";
    postRequest += "Host: ";
    postRequest += server.toString(); // Convert IPAddress to String
    postRequest += "\r\n";
    postRequest += "Content-Type: application/x-www-form-urlencoded\r\n";
    postRequest += "Content-Length: ";
    postRequest += String(value).length();
    postRequest += "\r\n\r\n";
    postRequest += "value=";
    postRequest += String(value);

    // Send the HTTP POST request to the server
    client.print(postRequest);
    Serial.println("Request sent to server.");

    // Wait for server response
    while (client.connected() && !client.available()) {
      delay(10);
    }
    // Read server response
    while (client.available()) {
      char c = client.read();
      Serial.write(c);
    }
  } else {
    // Failed to connect to server
    Serial.println("Connection to server failed.");
  }
}
