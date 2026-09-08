from datetime import datetime, timezone

from src.models import Measurement
from src.validation.validator import validate_measurement


def make_measurement(
    datapoint: str,
    value,
):
    return Measurement(
        datapoint=datapoint,
        value=value,
        measured_at=datetime.now(
            timezone.utc
        ),
    )


def test_normal_temperature_is_valid():
    result = validate_measurement(
        make_measurement(
            "temperature",
            22.1,
        )
    )

    assert result.quality == "valid"


def test_extreme_temperature_is_suspicious():
    result = validate_measurement(
        make_measurement(
            "temperature",
            62.1,
        )
    )

    assert result.quality == "suspicious"


def test_impossible_humidity_is_invalid():
    result = validate_measurement(
        make_measurement(
            "humidity",
            148,
        )
    )

    assert result.quality == "invalid"


def test_low_battery_is_suspicious():
    result = validate_measurement(
        make_measurement(
            "battery",
            5,
        )
    )

    assert result.quality == "suspicious"


def test_negative_co2_is_invalid():
    result = validate_measurement(
        make_measurement(
            "co2",
            -20,
        )
    )

    assert result.quality == "invalid"