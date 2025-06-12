#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid = "VARAD";
const char* password = "Adventure4@4242";

const char* mqtt_server = "192.168.1.12";  // Replace with your local MQTT broker IP

WiFiClient espClient;
PubSubClient client(espClient);

const int buttonPin = 0;  // GPIO0
bool lastButtonState = HIGH;

void setup_wifi() {
  delay(10);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void reconnect() {
  while (!client.connected()) {
    client.connect("ESP01ButtonClient");
  }
}

void setup() {
  pinMode(buttonPin, INPUT_PULLUP);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  bool buttonState = digitalRead(buttonPin);
  
  // Detect button press (falling edge)
  if (lastButtonState == HIGH && buttonState == LOW) {
    client.publish("esp01/button", "pressed");
  }

  lastButtonState = buttonState;
  delay(50);  // Debounce delay
}
