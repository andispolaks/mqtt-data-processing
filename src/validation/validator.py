from dataclasses import dataclass

from src.models import Measurement


@dataclass
class ValidationResult:
    quality: str
    reason: str | None = None


def validate_measurement(measurement: Measurement) -> ValidationResult:

    datapoint = measurement.datapoint
    value = measurement.value

    # TEMPERATURE
    if datapoint == "temperature":

        if not isinstance(value, (int, float)):
            return ValidationResult(
                quality="invalid",
                reason="Temperature must be numeric",
            )

        if value < -50 or value > 80:
            return ValidationResult(
                quality="invalid",
                reason="Temperature outside accepted range (-50 to 80 °C)",
            )

        if value < -30 or value > 50:
            return ValidationResult(
                quality="suspicious",
                reason="Temperature is unusual",
            )

    # HUMIDITY
    elif datapoint == "humidity":

        if not isinstance(value, (int, float)):
            return ValidationResult(
                quality="invalid",
                reason="Humidity must be numeric",
            )

        if value < 0 or value > 100:
            return ValidationResult(
                quality="invalid",
                reason="Humidity must be between 0 and 100 %",
            )

    # CO2
    elif datapoint == "co2":

        if not isinstance(value, (int, float)):
            return ValidationResult(
                quality="invalid",
                reason="CO2 must be numeric",
            )

        if value < 0 or value > 10000:
            return ValidationResult(
                quality="invalid",
                reason="CO2 outside accepted range",
            )

        if value > 5000:
            return ValidationResult(
                quality="suspicious",
                reason="Very high CO2 concentration",
            )

    # BATTERY
    elif datapoint == "battery":

        if not isinstance(value, (int, float)):
            return ValidationResult(
                quality="invalid",
                reason="Battery value must be numeric",
            )

        if value < 0 or value > 100:
            return ValidationResult(
                quality="invalid",
                reason="Battery must be between 0 and 100 %",
            )

        if value < 10:
            return ValidationResult(
                quality="suspicious",
                reason="Battery level is very low",
            )

    return ValidationResult(
        quality="valid",
    )