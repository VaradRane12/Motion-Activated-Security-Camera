#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// Wi-Fi credentials
const char* ssid = "VARAD";
const char* password = "Adventure4@4242";

// MQTT Broker details
const char* mqtt_server = "192.168.1.12";
const int mqtt_port = 1883;
const char* mqtt_topic = "door/status";

WiFiClient espClient;
PubSubClient client(espClient);

// Optional: use LED on GPIO2 (built-in LED on some boards)
#define LED_PIN 3

void setup_wifi() {
  delay(10);
  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ Wi-Fi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("📩 Message arrived [");
  Serial.print(topic);
  Serial.print("]: ");

  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.println(message);

  // Optional: Take action based on message
  if (message == "Door Opened") {
    digitalWrite(LED_PIN, HIGH); // Turn LED ON
  } else if (message == "Door Closed") {
    digitalWrite(LED_PIN, LOW); // Turn LED OFF
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP8266Receiver")) {
      Serial.println("✅ connected");
      client.subscribe(mqtt_topic);
    } else {
      Serial.print("❌ failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying...");
      delay(1000);
    }
  }
}

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}
