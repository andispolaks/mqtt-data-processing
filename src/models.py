from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Measurement:
    datapoint: str
    value: int | float | str | bool
    measured_at: datetime


@dataclass
class ParsedDeviceMessage:
    external_id: str
    name: str | None
    manufacturer: str | None
    model: str | None
    device_type: str
    source_type: str
    raw_payload: dict[str, Any]
    measurements: list[Measurement]