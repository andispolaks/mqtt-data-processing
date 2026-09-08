import json
import os

import paho.mqtt.publish as publish
from dotenv import load_dotenv


load_dotenv()


payload = {
    "SN": "105945",
    "name": "EL_uzskaite_3",
    "header": {
        "startTime": "2025-06-30T15:40:00.000",
        "endTime": "2025-06-30T15:40:00.000",
        "recordCount": 1,
        "columns": {
            "0": {
                "id": "0",
                "name": "Sk1_aktiva_jauda",
                "dataType": "NUMBER",
                "format": "float"
            },
            "1": {
                "id": "1",
                "name": "SK1_kopeja_jauda",
                "dataType": "NUMBER",
                "format": "float"
            },
            "2": {
                "id": "2",
                "name": "Sk1_aktivas_en_paterins",
                "dataType": "NUMBER",
                "format": "float"
            }
        }
    },
    "data": [
        {
            "ts": "2025-06-30T15:40:00.000",
            "f": {
                "0": {
                    "v": 80.6681
                },
                "1": {
                    "v": 87.6578
                },
                "2": {
                    "v": 1509779.7500
                }
            }
        }
    ]
}


topic = (
    "clients/demo/"
    "buildings/test/"
    "devices/105945/"
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


print("Viltrus MQTT message published!")