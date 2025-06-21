#include <ESP8266WiFi.h>
extern "C" {
  #include "user_interface.h"
}

// Replace with your actual credentials
const char* ssid = "VARAD";
const char* password = "Adventure4@4242";

struct {
  uint32_t crc32;
  uint8_t channel;
  uint8_t bssid[6];
  IPAddress ip;
  IPAddress gateway;
  IPAddress subnet;
} rtcData;

uint32_t calculateCRC32(const uint8_t *data, size_t length) {
  uint32_t crc = 0xffffffff;
  while (length--) {
    uint8_t c = *data++;
    for (uint32_t i = 0x80; i; i >>= 1) {
      bool bit = crc & 0x80000000;
      if (c & i) bit = !bit;
      crc <<= 1;
      if (bit) crc ^= 0x04c11db7;
    }
  }
  return crc;
}

void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("\n[BOOT] Device waking from sleep");

  // Try to read RTC memory
  ESP.rtcUserMemoryRead(0, (uint32_t*)&rtcData, sizeof(rtcData));
  uint32_t crc = calculateCRC32(((uint8_t*)&rtcData) + 4, sizeof(rtcData) - 4);

  bool rtcValid = (crc == rtcData.crc32);
  Serial.print("[RTC] CRC check: ");
  Serial.println(rtcValid ? "valid ✅" : "invalid ❌");

  if (rtcValid) {
    WiFi.config(rtcData.ip, rtcData.gateway, rtcData.subnet);
    WiFi.begin(ssid, password, rtcData.channel, rtcData.bssid);
    Serial.println("[WiFi] Trying fast reconnect...");
  } else {
    WiFi.begin(ssid, password);
    Serial.println("[WiFi] Fallback to standard reconnect...");
  }

  uint32_t startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 10000) {
    delay(100);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("[WiFi] Connected successfully ✅");

    Serial.print("[IP] "); Serial.println(WiFi.localIP());
    Serial.print("[Gateway] "); Serial.println(WiFi.gatewayIP());
    Serial.print("[Subnet] "); Serial.println(WiFi.subnetMask());

    // Save new RTC info
    rtcData.channel = WiFi.channel();
    memcpy(rtcData.bssid, WiFi.BSSID(), 6);
    rtcData.ip = WiFi.localIP();
    rtcData.gateway = WiFi.gatewayIP();
    rtcData.subnet = WiFi.subnetMask();
    rtcData.crc32 = calculateCRC32(((uint8_t*)&rtcData) + 4, sizeof(rtcData) - 4);

    bool success = ESP.rtcUserMemoryWrite(0, (uint32_t*)&rtcData, sizeof(rtcData));
    Serial.println(success ? "[RTC] RTC data written successfully ✅" : "[RTC] Failed to write RTC ❌");
  } else {
    Serial.println("[WiFi] Connection failed ❌ — skipping RTC write");
  }

  // Do your task here (MQTT, sensor, etc.)

  Serial.println("[SLEEP] Going to deep sleep for 10 seconds...");
  ESP.deepSleep(10 * 1000000, WAKE_RF_DISABLED); // Deep sleep with Wi-Fi disabled until wake
}

void loop() {
  // Not used
}
