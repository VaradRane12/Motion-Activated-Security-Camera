#include <ESP8266WiFi.h>

void setup() {
  Serial.begin(115200);
  delay(1000);

  const char* ssid = "VARAD";
  const char* password = "Adventure4@4242";

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  Serial.println("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected!");

  // Print all requested info
  Serial.print("Local IP: ");
  Serial.println(WiFi.localIP());

  Serial.print("Gateway: ");
  Serial.println(WiFi.gatewayIP());

  Serial.print("Subnet: ");
  Serial.println(WiFi.subnetMask());

  Serial.print("DNS: ");
  Serial.println(WiFi.dnsIP());

  Serial.print("BSSID (MAC of AP): ");
  Serial.println(WiFi.BSSIDstr());

  Serial.print("Channel: ");
  Serial.println(WiFi.channel());
}

void loop() {
  // Nothing here
}
