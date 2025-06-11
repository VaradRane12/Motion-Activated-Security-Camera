#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid = "Varad-2";
const char* password = "";
const char* mqtt_server = "192.168.1.12"; // IP of Raspberry Pi

WiFiClient espClient;
PubSubClient client(espClient);

const int relayPin = 3;  

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived on topic [");
  Serial.print(topic);
  Serial.print("]: ");

  String msg;
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  Serial.println(msg);

  if (msg == "ON") {
    digitalWrite(relayPin, HIGH);
    Serial.println("Relay turned ON");
  } else if (msg == "OFF") {
    digitalWrite(relayPin, LOW);
    Serial.println("Relay turned OFF");
  } else {
    Serial.println("Unknown message received");
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(relayPin, OUTPUT);
  digitalWrite(relayPin, LOW);

  setup_wifi();

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  Serial.print("Connecting to MQTT broker at ");
  Serial.println(mqtt_server);

  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP8266Client")) {
      Serial.println("Connected!");
      client.subscribe("home/light1");
      Serial.println("Subscribed to topic: home/light1");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(". Trying again in 2 seconds.");
      delay(2000);
    }
  }
}

void loop() {
  if (!client.connected()) {
    Serial.println("MQTT disconnected. Reconnecting...");
    while (!client.connected()) {
      if (client.connect("ESP8266Client")) {
        Serial.println("Reconnected to MQTT broker");
        client.subscribe("home/light1");
      } else {
        Serial.print("Reconnect failed, rc=");
        Serial.println(client.state());
        delay(2000);
      }
    }
  }

  client.loop();
}
