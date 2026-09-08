import os
import json
import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

from src.models import ParsedDeviceMessage
from src.validation.validator import validate_measurement

load_dotenv()


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
def get_building_timezone(
    client_name: str,
    building_name: str,
) -> str:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT b.timezone
                FROM buildings b
                JOIN clients c
                    ON c.id = b.client_id
                WHERE c.name = %s
                AND b.name = %s
                """,
                (
                    client_name,
                    building_name,
                ),
            )

            row = cur.fetchone()

            if row is None:
                return "UTC"

            return row[0]
def save_failed_raw_message(
    topic: str,
    raw_body: bytes | str,
    error_message: str,
):
    if isinstance(raw_body, bytes):
        raw_text = raw_body.decode(
            "utf-8",
            errors="replace",
        )
    else:
        raw_text = raw_body

    json_payload = None
    payload_text = None

    try:
        json_payload = Jsonb(
            json.loads(raw_text)
        )
    except json.JSONDecodeError:
        payload_text = raw_text

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO raw_messages (
                    device_id,
                    topic,
                    payload,
                    payload_text,
                    processing_status,
                    error_message
                )
                VALUES (
                    NULL,
                    %s,
                    %s,
                    %s,
                    'error',
                    %s
                )
                """,
                (
                    topic,
                    json_payload,
                    payload_text,
                    error_message,
                ),
            )
def save_message(
    parsed: ParsedDeviceMessage,
    topic: str,
    client_name: str,
    building_name: str,
):
    with get_connection() as conn:
        with conn.cursor() as cur:

            # CLIENT
            cur.execute(
                """
                INSERT INTO clients (name)
                VALUES (%s)
                ON CONFLICT (name) DO NOTHING
                """,
                (client_name,),
            )

            cur.execute(
                """
                SELECT id
                FROM clients
                WHERE name = %s
                """,
                (client_name,),
            )

            client_id = cur.fetchone()[0]

            # BUILDING
            cur.execute(
                """
                INSERT INTO buildings (client_id, name)
                VALUES (%s, %s)
                ON CONFLICT (client_id, name) DO NOTHING
                """,
                (client_id, building_name),
            )

            cur.execute(
                """
                SELECT id
                FROM buildings
                WHERE client_id = %s
                AND name = %s
                """,
                (client_id, building_name),
            )

            building_id = cur.fetchone()[0]

            # DEVICE
            cur.execute(
                """
                INSERT INTO devices (
                    building_id,
                    external_id,
                    name,
                    manufacturer,
                    model,
                    device_type,
                    source_type
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)

                ON CONFLICT (building_id, external_id)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    manufacturer = EXCLUDED.manufacturer,
                    model = EXCLUDED.model,
                    device_type = EXCLUDED.device_type,
                    source_type = EXCLUDED.source_type

                RETURNING id
                """,
                (
                    building_id,
                    parsed.external_id,
                    parsed.name,
                    parsed.manufacturer,
                    parsed.model,
                    parsed.device_type,
                    parsed.source_type,
                ),
            )

            device_id = cur.fetchone()[0]

            # SAVE ORIGINAL RAW MESSAGE
            cur.execute(
                """
                INSERT INTO raw_messages (
                    device_id,
                    topic,
                    payload,
                    processing_status
                )
                VALUES (%s, %s, %s, 'received')
                RETURNING id
                """,
                (
                    device_id,
                    topic,
                    Jsonb(parsed.raw_payload),
                ),
            )

            raw_message_id = cur.fetchone()[0]

            # SAVE NORMALIZED MEASUREMENTS
            for measurement in parsed.measurements:
                validation = validate_measurement(measurement)
                numeric_value = None
                text_value = None
                boolean_value = None

                if isinstance(measurement.value, bool):
                    boolean_value = measurement.value

                elif isinstance(measurement.value, (int, float)):
                    numeric_value = measurement.value

                elif isinstance(measurement.value, str):
                    text_value = measurement.value

                else:
                    raise ValueError(
                        f"Unsupported value type for "
                        f"{measurement.datapoint}"
                    )

                cur.execute(
                    """
                    INSERT INTO measurements (
                        device_id,
                        raw_message_id,
                        datapoint,
                        numeric_value,
                        text_value,
                        boolean_value,
                        measured_at,
                        quality
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s, %s
                    )
                    ON CONFLICT (
                        device_id,
                        datapoint,
                        measured_at
                    )
                    DO NOTHING
                    """,
                    (
                        device_id,
                        raw_message_id,
                        measurement.datapoint,
                        numeric_value,
                        text_value,
                        boolean_value,
                        measurement.measured_at,
                        validation.quality,
                    ),
                )

            # MARK RAW MESSAGE AS SUCCESSFULLY PROCESSED
            cur.execute(
                """
                UPDATE raw_messages
                SET processing_status = 'processed'
                WHERE id = %s
                """,
                (raw_message_id,),
            )

    return device_id