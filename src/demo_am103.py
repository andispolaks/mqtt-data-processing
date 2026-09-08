from src.database import save_message
from src.parsers.milesight import parse_am103


payload = {
    "battery": 44,
    "co2": 512,
    "devEUI": "24e124725d021011",
    "humidity": 148,
    "temperature": 62.1,
    "time": "2025-06-30T12:33:42.315022Z",
}


parsed = parse_am103(payload)

print("Parsed device:")
print(parsed.external_id)

print("\nMeasurements:")

for measurement in parsed.measurements:
    print(
        measurement.datapoint,
        "=",
        measurement.value,
        "@",
        measurement.measured_at,
    )


device_id = save_message(
    parsed=parsed,
    topic="clients/demo/buildings/test/devices/24e124725d021011/telemetry",
    client_name="Demo client",
    building_name="Demo building",
)


print("\nSaved successfully!")
print("Database device ID:", device_id)