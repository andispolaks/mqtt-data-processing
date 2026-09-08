import json
import os

import paho.mqtt.publish as publish
from dotenv import load_dotenv


load_dotenv()


payload = {
    "battery": 44,
    "co2": 512,
    "devEUI": "24e124725d021011",
    "humidity": 48,
    "temperature": 22.1,
    "time": "2025-06-30T13:10:42.315022Z",
}


topic = (
    "clients/demo/"
    "buildings/test/"
    "devices/24e124725d021011/"
    "telemetry"
)


import time
import paho.mqtt.client as mqtt


disconnected = False


def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected to RabbitMQ.")
    print("Connection result:", reason_code)


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    global disconnected
    disconnected = True
    print("Disconnected by RabbitMQ.")
    print("Reason:", reason_code)


client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2
)

client.username_pw_set(
    os.getenv("CLIENT_MQTT_USER"),
    os.getenv("CLIENT_MQTT_PASSWORD"),
)

client.on_connect = on_connect
client.on_disconnect = on_disconnect

client.connect(
    os.getenv("MQTT_HOST"),
    int(os.getenv("MQTT_PORT", "1883")),
    60,
)

client.loop_start()

time.sleep(1)

print("Trying to publish to:")
print(topic)

message = client.publish(
    topic,
    json.dumps(payload),
    qos=1,
)

for _ in range(30):
    if message.is_published():
        print("Message was accepted.")
        break

    if disconnected:
        print(
            "Publish was rejected by the broker."
        )
        break

    time.sleep(0.1)

else:
    print(
        "No acknowledgement received within 3 seconds."
    )

client.loop_stop()
client.disconnect()

