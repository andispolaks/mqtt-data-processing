import json
import os

import paho.mqtt.publish as publish
from dotenv import load_dotenv


load_dotenv()


payload = {
    "OstasSkati_cold_side": 2480,
    "OstasSkati_current_flow": 0,
    "OstasSkati_current_power": 0,
    "OstasSkati_energy": 1429938,
    "OstasSkati_hot_side": 2460,
    "OstasSkati_temp_diff": -20,
    "adv_1": 0,
    "devEUI": "24e124445d226973",
    "gpio_in_1": "off",
    "gpio_in_2": "off",
    "gpio_in_3": "off",
    "gpio_in_4": "off",
    "gpio_out_1": "off",
    "gpio_out_2": "off",
    "pt100_1": 12.2,
    "pt100_2": 12.1,
    "time": "2025-06-30T12:33:10.709277Z",
}


topic = (
    "clients/demo/"
    "buildings/test/"
    "devices/24e124445d226973/"
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


print("UC300 MQTT message published!")