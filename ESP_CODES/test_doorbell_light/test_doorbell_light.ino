#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// Wi-Fi and MQTT Configuration
const char* ssid = "VARAD";
const char* password = "Adventure4@4242";
const char* mqtt_server = "192.168.1.12";
const int mqtt_port = 1883;

WiFiClient espClient;
PubSubClient client(espClient);

// Reed Switch and Relay
#define REED_PIN 2  // GPIO1 on ESP-01 (TX pin; be cautious!)
const int relayPin = 3;

const char* status_topic = "door/status";
const char* control_topic = "home/light1";

int lastState = HIGH;

// WiFi Setup
void setup_wifi() {
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\\nWiFi connected");
}

// MQTT Callback
void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  if (String(topic) == control_topic) {
    if (message == "ON") {
      digitalWrite(relayPin, HIGH);
    } else if (message == "OFF") {
      digitalWrite(relayPin, LOW);
    }
  }
}

// MQTT Reconnect
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");

    // Generate a unique client ID using ESP chip ID
    String clientId = "ESP8266_" + String(ESP.getChipId());

    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      client.subscribe(control_topic);  // Subscribe after connecting
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}
void setup() {
  Serial.begin(9600);
  pinMode(REED_PIN, INPUT_PULLUP);
  pinMode(relayPin, OUTPUT);

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  int currentState = digitalRead(REED_PIN);
  if (currentState != lastState) {
    lastState = currentState;
    String status = (currentState == LOW) ? "OPEN" : "CLOSED";
    client.publish(status_topic, status.c_str(), true);
  }

  delay(100);
}