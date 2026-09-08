from datetime import datetime
from zoneinfo import ZoneInfo

from src.models import Measurement, ParsedDeviceMessage


def parse_viltrus(
    payload: dict,
    timezone_name: str = "UTC",
) -> ParsedDeviceMessage:

    required_fields = {
        "SN",
        "name",
        "header",
        "data",
    }

    missing_fields = required_fields - payload.keys()

    if missing_fields:
        raise ValueError(
            f"Missing required fields: "
            f"{', '.join(sorted(missing_fields))}"
        )

    header = payload["header"]

    if "columns" not in header:
        raise ValueError(
            "Viltrus header is missing columns"
        )

    if not isinstance(payload["data"], list):
        raise ValueError(
            "Viltrus data must be a list"
        )

    columns = header["columns"]

    measurements = []

    for record in payload["data"]:

        if "ts" not in record:
            raise ValueError(
                "Viltrus record is missing timestamp"
            )

        if "f" not in record:
            raise ValueError(
                "Viltrus record is missing field data"
            )

        timestamp = datetime.fromisoformat(
            record["ts"]
        )

        # Viltrus timestamp has no timezone
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=ZoneInfo(timezone_name)
            )

        for column_id, value_object in record["f"].items():

            if column_id not in columns:
                raise ValueError(
                    f"Unknown Viltrus column ID: {column_id}"
                )

            column_definition = columns[column_id]

            datapoint_name = column_definition["name"]

            if "v" not in value_object:
                raise ValueError(
                    f"Missing value for column {column_id}"
                )

            measurements.append(
                Measurement(
                    datapoint=datapoint_name,
                    value=value_object["v"],
                    measured_at=timestamp,
                )
            )

    return ParsedDeviceMessage(
        external_id=str(payload["SN"]),
        name=payload["name"],
        manufacturer=None,
        model=None,
        device_type="energy_meter",
        source_type="viltrus",
        raw_payload=payload,
        measurements=measurements,
    )