from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from src.models import Measurement, ParsedDeviceMessage


def parse_am103(payload: dict) -> ParsedDeviceMessage:
    required_fields = {
        "devEUI",
        "time",
        "battery",
        "co2",
        "humidity",
        "temperature",
    }

    missing_fields = required_fields - payload.keys()

    if missing_fields:
        raise ValueError(
            f"Missing required fields: {', '.join(sorted(missing_fields))}"
        )

    timestamp = datetime.fromisoformat(
        payload["time"].replace("Z", "+00:00")
    )

    measurements = [
        Measurement(
            datapoint="battery",
            value=payload["battery"],
            measured_at=timestamp,
        ),
        Measurement(
            datapoint="co2",
            value=payload["co2"],
            measured_at=timestamp,
        ),
        Measurement(
            datapoint="humidity",
            value=payload["humidity"],
            measured_at=timestamp,
        ),
        Measurement(
            datapoint="temperature",
            value=payload["temperature"],
            measured_at=timestamp,
        ),
    ]

    return ParsedDeviceMessage(
        external_id=payload["devEUI"],
        name=None,
        manufacturer="Milesight",
        model="AM103",
        device_type="environment_sensor",
        source_type="milesight",
        raw_payload=payload,
        measurements=measurements,
    )

def parse_vicki(payload: dict) -> ParsedDeviceMessage:
    required_fields = {
        "devEUI",
        "deviceName",
        "time",
        "sensorTemperature",
        "targetTemperature",
    }

    missing_fields = required_fields - payload.keys()

    if missing_fields:
        raise ValueError(
            f"Missing required fields: {', '.join(sorted(missing_fields))}"
        )

    timestamp = datetime.fromisoformat(
        payload["time"].replace("Z", "+00:00")
    )

    datapoints = [
        "attachedBackplate",
        "batteryVoltage",
        "brokenSensor",
        "calibrationFailed",
        "childLock",
        "highMotorConsumption",
        "lowMotorConsumption",
        "motorPosition",
        "motorRange",
        "newVersion",
        "openProcentage",
        "openWindow",
        "perceiveAsOnline",
        "relativeHumidity",
        "sensorTemperature",
        "targetTemperature",
    ]

    measurements = [
        Measurement(
            datapoint=key,
            value=payload[key],
            measured_at=timestamp,
        )
        for key in datapoints
        if key in payload
    ]

    return ParsedDeviceMessage(
        external_id=payload["devEUI"],
        name=payload["deviceName"],
        manufacturer="None",
        model="Vicki",
        device_type="thermostat",
        source_type="milesight",
        raw_payload=payload,
        measurements=measurements,
    )

def parse_uc300(payload: dict) -> ParsedDeviceMessage:
    required_fields = {
        "devEUI",
        "time",
    }

    missing_fields = required_fields - payload.keys()

    if missing_fields:
        raise ValueError(
            f"Missing required fields: {', '.join(sorted(missing_fields))}"
        )

    timestamp = datetime.fromisoformat(
        payload["time"].replace("Z", "+00:00")
    )

    measurements = []

    for key, value in payload.items():

        if key in {"devEUI", "time"}:
            continue

        measurements.append(
            Measurement(
                datapoint=key,
                value=value,
                measured_at=timestamp,
            )
        )

    return ParsedDeviceMessage(
        external_id=payload["devEUI"],
        name=None,
        manufacturer="Milesight",
        model="UC300",
        device_type="controller",
        source_type="milesight",
        raw_payload=payload,
        measurements=measurements,
    )
def parse_zenner(
    payload: dict,
    timezone_name: str = "UTC",
) -> ParsedDeviceMessage:

    required_fields = {
        "devEUI",
        "device",
        "time",
        "volumes",
    }

    missing_fields = required_fields - payload.keys()

    if missing_fields:
        raise ValueError(
            f"Missing required fields: "
            f"{', '.join(sorted(missing_fields))}"
        )

    if not isinstance(payload["volumes"], list):
        raise ValueError(
            "Zenner volumes must be a list"
        )

    message_time = datetime.fromisoformat(
        payload["time"].replace("Z", "+00:00")
    )

    building_timezone = ZoneInfo(
        timezone_name
    )

    local_message_time = (
        message_time.astimezone(
            building_timezone
        )
    )

    measurements = []

    # Device status belongs to the MQTT
    # message itself.
    if "ok" in payload:
        measurements.append(
            Measurement(
                datapoint="ok",
                value=payload["ok"],
                measured_at=message_time,
            )
        )

    for volume in payload["volumes"]:

        if "hour" not in volume:
            raise ValueError(
                "Zenner volume entry "
                "is missing hour"
            )

        if "val" not in volume:
            raise ValueError(
                "Zenner volume entry "
                "is missing val"
            )

        hour = volume["hour"]

        if (
            not isinstance(hour, int)
            or hour < 0
            or hour > 23
        ):
            raise ValueError(
                f"Invalid Zenner hour: {hour}"
            )

        measured_local = (
            local_message_time.replace(
                hour=hour,
                minute=0,
                second=0,
                microsecond=0,
            )
        )

        # Handles messages around midnight.
        #
        # Example:
        # message arrives 00:15
        # reading says hour 23
        #
        # → the reading belongs to
        #   the previous day.
        if measured_local > local_message_time:
            measured_local -= timedelta(
                days=1
            )

        measured_utc = (
            measured_local.astimezone(
                timezone.utc
            )
        )

        measurements.append(
            Measurement(
                datapoint="volume",
                value=volume["val"],
                measured_at=measured_utc,
            )
        )

    return ParsedDeviceMessage(
        external_id=payload["devEUI"],
        name=payload["device"],
        manufacturer="Zenner",
        model=payload["device"],
        device_type="water_meter",
        source_type="milesight",
        raw_payload=payload,
        measurements=measurements,
    )