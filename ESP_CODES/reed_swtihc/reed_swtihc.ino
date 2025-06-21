#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#define REED_PIN 16  // GPIO1 on ESP-01 (TX pin; be cautious!)

const char* ssid = "VARAD";
const char* password = "Adventure4@4242";

const char* mqtt_server = "192.168.1.12";
const int mqtt_port = 1883;
const char* mqtt_topic = "door/status";

WiFiClient espClient;
PubSubClient client(espClient);

int lastState = HIGH;

void setup_wifi() {
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(200);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.println("Connecting to MQTT broker...");
    if (client.connect("ESP01Client")) {
      Serial.println("Connected to MQTT!");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(". Trying again...");
      delay(500);
    }
  }
}

void setup() {
  Serial.begin(9600);
  delay(10);
  Serial.println("\nESP01 Reed Switch Starting...");

  pinMode(REED_PIN, INPUT_PULLUP);
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  int state = digitalRead(REED_PIN);
  if (state != lastState) {
    lastState = state;

    if (state == LOW) {
      Serial.println("Reed Switch: Door Closed");
      client.publish(mqtt_topic, "Door Closed");
    } else {
      Serial.println("Reed Switch: Door Opened");
      client.publish(mqtt_topic, "Door Opened");
    }

    delay(50); // debounce
  }

  delay(100); // Polling interval
}
