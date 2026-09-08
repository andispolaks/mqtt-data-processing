import json
import os

import paho.mqtt.publish as publish
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()


payload = {
    "Lib_version": "v1.2",
    "name": "TP_wago",
    "manufacturer": "WAGO",
    "model": "751-9301",
    "serial": "37SUN31564010260470190+0000000002428588",
    "type": "PLC",
    "DPS": [
        {
            "max strava": 931.821,
            "ts": "DT#2025-06-30-12:12:47"
        },
        {
            "TP1_temp": 26.8,
            "ts": "DT#2025-06-30-12:12:47"
        },
        {
            "TP2_temp": 30.5,
            "ts": "DT#2025-06-30-12:12:47"
        },
        {
            "Alarm_TP1": 0,
            "ts": "DT#2025-06-30-12:12:47"
        },
        {
            "Alarm_TP2": 0,
            "ts": "DT#2025-06-30-12:12:47"
        }
    ]
}
device_id = payload["serial"]
topic_device_id = quote(device_id, safe="")

topic = (
    "clients/demo/"
    "buildings/test/"
    f"devices/{topic_device_id}/"
    "telemetry"
)


publish.single(
    topic=topic,
    payload=json.dumps(payload),
    hostname=os.getenv("MQTT_HOST"),
    port=int(os.getenv("MQTT_PORT", "1883")),
    qos=1,
    auth={
        "username": os.getenv("RABBITMQ_USER"),
        "password": os.getenv("RABBITMQ_PASSWORD"),
    },
)


print("WAGO PLC MQTT message published!")