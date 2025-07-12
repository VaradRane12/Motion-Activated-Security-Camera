import paho.mqtt.client as mqtt
import requests
import time
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()
WEBHOOK_DOOR = os.getenv("DISCORD_WEBHOOK_GENERAL")

# Discord notification function
def send_discord_notification():
    if not WEBHOOK_DOOR:
        print("Webhook not set.")
        return
    try:
        payload = {
            "content": "🚪 **Doorbell Rang!** Door was opened."
        }
        requests.post(WEBHOOK_DOOR, json=payload, timeout=5)
        print("Notification sent.")
    except Exception as e:
        print(f"Error sending to Discord: {e}")

# MQTT callback
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe("door/status")
    else:
        print("Failed to connect, return code:", rc)

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    print(f"Received on {msg.topic}: {message}")
    if message.strip().upper() == "OPEN":
        send_discord_notification()

# Setup MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect("localhost", 1883, 60)
except Exception as e:
    print(f"MQTT connection failed: {e}")
    exit(1)

client.loop_start()

print("🚪 Door Monitor running...")

# Keep script alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting.")
    client.loop_stop()
