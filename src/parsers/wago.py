from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src.models import Measurement, ParsedDeviceMessage


def parse_wago_timestamp(
    timestamp: str,
    timezone_name: str,
) -> datetime:
    if not timestamp.startswith("DT#"):
        raise ValueError(
            f"Unsupported WAGO timestamp: {timestamp}"
        )

    naive_time = datetime.strptime(
        timestamp,
        "DT#%Y-%m-%d-%H:%M:%S",
    )

    local_time = naive_time.replace(
        tzinfo=ZoneInfo(timezone_name)
    )

    return local_time.astimezone(timezone.utc)


def get_external_id(payload: dict) -> str:
    # Prefer an explicit serial number.
    if payload.get("serial"):
        return str(payload["serial"])

    # Some devices, such as the Schneider
    # example, send SN as a DPS field.
    for datapoint in payload.get("DPS", []):
        if "SN" in datapoint:
            return str(datapoint["SN"])

    # Last-resort identifier.
    if payload.get("name"):
        return payload["name"]

    raise ValueError(
        "WAGO payload has no usable device identifier"
    )


def parse_wago(
    payload: dict,
    timezone_name: str = "UTC",
) -> ParsedDeviceMessage:

    required_fields = {
        "name",
        "manufacturer",
        "model",
        "type",
        "DPS",
    }

    missing_fields = required_fields - payload.keys()

    if missing_fields:
        raise ValueError(
            f"Missing required fields: "
            f"{', '.join(sorted(missing_fields))}"
        )

    if not isinstance(payload["DPS"], list):
        raise ValueError(
            "WAGO DPS must be a list"
        )

    external_id = get_external_id(payload)

    measurements = []

    for item in payload["DPS"]:

        if "ts" not in item:
            raise ValueError(
                "WAGO datapoint is missing timestamp"
            )

        timestamp = parse_wago_timestamp(
            item["ts"],
            timezone_name,
        )

        # reg_nr and ts describe the datapoint;
        # they are not measurement values.
        value_keys = [
            key
            for key in item.keys()
            if key not in {"reg_nr", "ts"}
        ]

        if len(value_keys) != 1:
            raise ValueError(
                "Expected exactly one value "
                f"in WAGO datapoint: {item}"
            )

        datapoint = value_keys[0]

        # SN is used as device identification,
        # rather than telemetry.
        if datapoint == "SN":
            continue

        measurements.append(
            Measurement(
                datapoint=datapoint,
                value=item[datapoint],
                measured_at=timestamp,
            )
        )

    return ParsedDeviceMessage(
        external_id=external_id,
        name=payload["name"],
        manufacturer=payload["manufacturer"],
        model=payload["model"],
        device_type=payload["type"],
        source_type="wago",
        raw_payload=payload,
        measurements=measurements,
    )