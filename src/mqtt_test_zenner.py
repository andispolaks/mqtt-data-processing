import json
import os

import paho.mqtt.publish as publish
from dotenv import load_dotenv


load_dotenv()


payload = {
    "devEUI": "04b6480450052428",
    "device": "ZennerSP12",
    "ok": True,
    "time": "2025-06-30T09:19:46.242854Z",
    "volumes": [
        {
            "hour": 10,
            "val": 1024346,
        },
        {
            "hour": 11,
            "val": 1024492,
        },
        {
            "hour": 12,
            "val": 1024673,
        },
    ],
}


topic = (
    "clients/demo/"
    "buildings/test/"
    "devices/04b6480450052428/"
    "telemetry"
)


publish.single(
    topic=topic,
    payload=json.dumps(payload),
    hostname=os.getenv("MQTT_HOST"),
    port=int(
        os.getenv("MQTT_PORT", "1883")
    ),
    qos=1,
    auth={
        "username": os.getenv(
            "RABBITMQ_USER"
        ),
        "password": os.getenv(
            "RABBITMQ_PASSWORD"
        ),
    },
)


print("Zenner MQTT message published!")