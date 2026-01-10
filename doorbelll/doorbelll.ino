#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid = "VARAD";
const char* password = "Adventure4@4242";
const char* mqtt_server = "192.168.1.12";

// Your AP's MAC address (BSSID)
//30:CC:21:EB:54:A6
uint8_t bssid[] = { 0x30, 0xCC, 0x21, 0xEB, 0x54, 0xA6 };  // Replace with yours
int wifi_channel = 1;  // Replace with your router's channel

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  WiFi.mode(WIFI_STA);

  Serial.println("Fast connecting to WiFi using BSSID...");
  WiFi.begin(ssid, password, wifi_channel, bssid, true);

  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries++ < 20) {
    delay(200);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected.");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi connection failed.");
  }
}

void reconnect() {
  Serial.print("Connecting to MQTT...");
  while (!client.connected()) {
    if (client.connect("ESP01Doorbell")) {
      Serial.println("connected.");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying...");
      delay(1000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("==== Woke from deep sleep ====");

  client.setServer(mqtt_server, 1883);
  setup_wifi();
  reconnect();

  if (client.connected()) {
    Serial.println("Sending MQTT: 'pressed'");
    client.publish("doorbell/button", "pressed");
    client.loop();
    delay(1000);
  }

  Serial.println("Sleeping now...");
  ESP.deepSleep(0);  // Sleep forever
}

void loop() {}
