from datetime import timezone

from src.parsers.milesight import (
    parse_am103,
    parse_zenner,
)
from src.parsers.viltrus import parse_viltrus
from src.parsers.wago import parse_wago


def test_am103_parser():
    payload = {
        "battery": 44,
        "co2": 512,
        "devEUI": "24e124725d021011",
        "humidity": 48,
        "temperature": 22.1,
        "time": "2025-06-30T12:32:42.315022Z",
    }

    parsed = parse_am103(payload)

    assert parsed.external_id == "24e124725d021011"
    assert parsed.model == "AM103"
    assert len(parsed.measurements) == 4

    values = {
        measurement.datapoint: measurement.value
        for measurement in parsed.measurements
    }

    assert values["temperature"] == 22.1
    assert values["humidity"] == 48
    assert values["co2"] == 512
    assert values["battery"] == 44


def test_wago_parser():
    payload = {
        "Lib_version": "v1.2",
        "name": "SK1-P14",
        "manufacturer": "Schneider",
        "model": "iEM3250",
        "type": "Electric meters",
        "slave_id": 1,
        "DPS": [
            {
                "SN": 23516044,
                "reg_nr": 129,
                "ts": "DT#2025-06-30-12:26:04",
            },
            {
                "Curr_avg": 0.591,
                "reg_nr": 3009,
                "ts": "DT#2025-06-30-12:26:05",
            },
        ],
    }

    parsed = parse_wago(
        payload,
        timezone_name="Europe/Riga",
    )

    assert parsed.external_id == "23516044"
    assert parsed.manufacturer == "Schneider"
    assert parsed.model == "iEM3250"

    # SN is metadata, not telemetry.
    assert len(parsed.measurements) == 1

    measurement = parsed.measurements[0]

    assert measurement.datapoint == "Curr_avg"
    assert measurement.value == 0.591

    utc_time = measurement.measured_at.astimezone(
        timezone.utc
    )

    assert utc_time.hour == 9
    assert utc_time.minute == 26


def test_viltrus_column_mapping():
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
                    "format": "float",
                }
            },
        },
        "data": [
            {
                "ts": "2025-06-30T15:40:00.000",
                "f": {
                    "0": {
                        "v": 80.6681
                    }
                },
            }
        ],
    }

    parsed = parse_viltrus(
        payload,
        timezone_name="Europe/Riga",
    )

    assert parsed.external_id == "105945"
    assert len(parsed.measurements) == 1

    measurement = parsed.measurements[0]

    assert measurement.datapoint == "Sk1_aktiva_jauda"
    assert measurement.value == 80.6681


def test_zenner_creates_separate_hourly_measurements():
    payload = {
        "devEUI": "04b6480450052428",
        "device": "ZennerSP12",
        "ok": True,
        "time": "2025-06-30T09:19:46.242854Z",
        "volumes": [
            {
                "hour": 10,
                "val": 1024346,
            },
            {
                "hour": 11,
                "val": 1024492,
            },
            {
                "hour": 12,
                "val": 1024673,
            },
        ],
    }

    parsed = parse_zenner(
        payload,
        timezone_name="Europe/Riga",
    )

    volumes = [
        measurement
        for measurement in parsed.measurements
        if measurement.datapoint == "volume"
    ]

    assert len(volumes) == 3

    utc_hours = [
        measurement.measured_at.astimezone(
            timezone.utc
        ).hour
        for measurement in volumes
    ]

    assert utc_hours == [7, 8, 9]