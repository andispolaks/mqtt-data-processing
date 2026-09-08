import json
import os

import paho.mqtt.publish as publish
from dotenv import load_dotenv


load_dotenv()


payload = {
    "applicationID": 5,
    "attachedBackplate": True,
    "batteryVoltage": 3.3,
    "brokenSensor": False,
    "calibrationFailed": False,
    "childLock": 1,
    "devEUI": "70b3d52dd301015d",
    "deviceName": "Vicki-VWMT",
    "highMotorConsumption": False,
    "lowMotorConsumption": False,
    "motorPosition": 6,
    "motorRange": 515,
    "newVersion": True,
    "openProcentage": 98.83495145631068,
    "openWindow": False,
    "perceiveAsOnline": True,
    "relativeHumidity": 50,
    "sensorTemperature": 23.588263633251334,
    "targetTemperature": 24,
    "time": "2025-06-30T12:33:01.634324Z",
}


topic = (
    "clients/demo/"
    "buildings/test/"
    "devices/70b3d52dd301015d/"
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


print("Vicki MQTT message published!")