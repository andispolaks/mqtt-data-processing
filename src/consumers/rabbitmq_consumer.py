import json
import os

import pika
from dotenv import load_dotenv
from urllib.parse import unquote

from src.database import (
    get_building_timezone,
    save_failed_raw_message,
    save_message,
)
from src.parsers.router import parse_payload


load_dotenv()


QUEUE_NAME = "telemetry_ingestion"

BINDING_KEY = (
    "clients.*.buildings.*.devices.*.telemetry"
)


def get_connection():
    credentials = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER"),
        os.getenv("RABBITMQ_PASSWORD"),
    )

    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            credentials=credentials,
        )
    )


def parse_routing_key(routing_key: str):
    parts = routing_key.split(".")

    if (
        len(parts) != 7
        or parts[0] != "clients"
        or parts[2] != "buildings"
        or parts[4] != "devices"
        or parts[6] != "telemetry"
    ):
        raise ValueError(
            f"Unexpected routing key: {routing_key}"
        )

    return {
        "client": parts[1],
        "building": parts[3],
        "device": unquote(parts[5]),
    }


def process_message(channel, method, properties, body):
    try:
        routing = parse_routing_key(method.routing_key)

        payload = json.loads(
            body.decode("utf-8")
        )

        # For now we support the AM103 payload.
        # More device parsers will be added later.
        timezone_name = get_building_timezone(
            client_name=routing["client"],
            building_name=routing["building"],
        )

        parsed = parse_payload(
            payload,
            timezone_name=timezone_name,
        )
        
        if parsed.external_id != routing["device"]:
            raise ValueError(
                "Device ID in payload does not match "
                "device ID in MQTT topic"
            )

        mqtt_topic = method.routing_key.replace(
            ".",
            "/",
        )

        save_message(
            parsed=parsed,
            topic=mqtt_topic,
            client_name=routing["client"],
            building_name=routing["building"],
        )

        print(
            f"Processed {parsed.external_id}: "
            f"{len(parsed.measurements)} measurements"
        )

        channel.basic_ack(
            delivery_tag=method.delivery_tag
        )

    except Exception as exc:
        print(
            f"Message processing failed: {exc}"
        )

        failed_topic = (
            method.routing_key.replace(".", "/")
        )

        try:
            save_failed_raw_message(
                topic=failed_topic,
                raw_body=body,
                error_message=str(exc),
            )

            print(
                "Failed message saved to database."
            )

        except Exception as database_error:
            print(
                "Could not save failed message: "
                f"{database_error}"
            )

        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False,
        )



def main():
    connection = get_connection()
    channel = connection.channel()

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
    )

    channel.queue_bind(
        exchange="amq.topic",
        queue=QUEUE_NAME,
        routing_key=BINDING_KEY,
    )

    channel.basic_qos(
        prefetch_count=10
    )

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=process_message,
        auto_ack=False,
    )

    print("RabbitMQ consumer started.")
    print(
        "Waiting for MQTT telemetry..."
    )
    print(
        f"Binding: {BINDING_KEY}"
    )
    print("Press CTRL+C to stop.")

    try:
        channel.start_consuming()

    except KeyboardInterrupt:
        print("\nStopping consumer...")

    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()