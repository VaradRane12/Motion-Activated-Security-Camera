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
#define REED_PIN 2  // GPIO1 on ESP-01 (TX pin, use carefully)
const int relayPin = 3;

// MQTT Topics
const char* status_topic = "door/status";
const char* control_topic = "home/light1";
const char* ack_topic = "door/ack";

int lastState = HIGH;
bool waitingForAck = false;
unsigned long lastSentTime = 0;
const unsigned long ackTimeout = 1000; // 3 seconds
String lastSentStatus = "";

void setup_wifi() {
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi connected");
}

void sendStatus(String status) {
  client.publish(status_topic, status.c_str(), true);
  lastSentStatus = status;
  lastSentTime = millis();
  waitingForAck = true;
  Serial.printf("📤 Sent status: %s\n", status.c_str());
}

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

  if (String(topic) == ack_topic) {
    if ((ltastSentStaus == "OPEN" && message == "ACK_OPEN") ||
        (lastSentStatus == "CLOSED" && message == "ACK_CLOSED")) {
      Serial.printf("✅ ACK received: %s\n", message.c_str());
      waitingForAck = false;
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "ESP8266Sender_" + String(ESP.getChipId());
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      client.subscribe(control_topic);
      client.subscribe(ack_topic);
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
  digitalWrite(relayPin, LOW);

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
    sendStatus(status);
  }

  if (waitingForAck && (millis() - lastSentTime > ackTimeout)) {
    Serial.println("⚠️ ACK timeout, resending status");
    sendStatus(lastSentStatus);
  }

  delay(100);
}
