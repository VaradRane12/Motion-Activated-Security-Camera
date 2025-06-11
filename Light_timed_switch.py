import os
import time
import schedule

def turn_on_light():
    os.system('mosquitto_pub -h localhost -t home/light1 -m "ON"')
    print("Light turned ON at 22:17 AM")

def turn_off_light():
    os.system('mosquitto_pub -h localhost -t home/light1 -m "OFF"')
    print("Light turned OFF at 22:22 AM")

schedule.every().day.at("18:30").do(turn_on_light)
schedule.every().day.at("05:30").do(turn_off_light)

print("MQTT Light Scheduler running...")

while True:
    schedule.run_pending()
    time.sleep(1)
