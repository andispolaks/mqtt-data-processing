import os

import paho.mqtt.publish as publish
from dotenv import load_dotenv


load_dotenv()


topic = (
    "clients/demo/"
    "buildings/test/"
    "devices/broken-device/"
    "telemetry"
)


payload = """
{
    "temperature": 22.1,
    THIS IS NOT VALID JSON
}
"""


publish.single(
    topic=topic,
    payload=payload,
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


print("Broken MQTT message published!")