from src.models import ParsedDeviceMessage
from src.parsers.milesight import (
    parse_am103,
    parse_uc300,
    parse_vicki,
    parse_zenner,
)
from src.parsers.wago import parse_wago
from src.parsers.viltrus import parse_viltrus
def parse_payload(
    payload: dict,
    timezone_name: str = "UTC",
) -> ParsedDeviceMessage:

    # Milesight AM103 environmental sensor
    if {
        "devEUI",
        "battery",
        "co2",
        "humidity",
        "temperature",
    }.issubset(payload.keys()):
        return parse_am103(payload)

    # Vicki thermostat
    if (
        "devEUI" in payload
        and "deviceName" in payload
        and "sensorTemperature" in payload
        and "targetTemperature" in payload
    ):
        return parse_vicki(payload)
        # Milesight UC300 controller
    if (
        "devEUI" in payload
        and "time" in payload
        and (
            "pt100_1" in payload
            or "gpio_in_1" in payload
            or "OstasSkati_energy" in payload
        )
    ):
        return parse_uc300(payload)
        # Zenner water meter
    if (
        "devEUI" in payload
        and payload.get("device")
        == "ZennerSP12"
        and "volumes" in payload
    ):
        return parse_zenner(
            payload,
            timezone_name=timezone_name,
        )
        # WAGO / Schneider / Corrigo format
    if (
        "DPS" in payload
        and "name" in payload
        and "manufacturer" in payload
        and "model" in payload
        and "type" in payload
    ):
        return parse_wago(
            payload,
            timezone_name=timezone_name,
        )
        # Viltrus format
    if (
        "SN" in payload
        and "header" in payload
        and "data" in payload
    ):
        return parse_viltrus(
            payload,
            timezone_name=timezone_name,
        )
    raise ValueError(
        "Unsupported or unrecognized device payload"
    )