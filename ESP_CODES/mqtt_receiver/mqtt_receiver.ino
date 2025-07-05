#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// Wi-Fi credentials
const char* ssid = "VARAD";
const char* password = "Adventure4@4242";

// MQTT Broker details
const char* mqtt_server = "192.168.1.12";
const int mqtt_port = 1883;
const char* mqtt_topic = "door/status";
const char* ack_topic = "door/ack";

WiFiClient espClient;
PubSubClient client(espClient);

#define LED_PIN 3  // Relay or indicator

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
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.printf("📩 Message arrived [%s]: %s\n", topic, message.c_str());

  if (String(topic) == mqtt_topic) {
    if (message == "OPEN") {
      digitalWrite(LED_PIN, HIGH);
      delay(4000);
      client.publish(ack_topic, "ACK_OPEN");
    } else if (message == "CLOSED") {
      digitalWrite(LED_PIN, LOW);
      client.publish(ack_topic, "ACK_CLOSED");
    }
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
