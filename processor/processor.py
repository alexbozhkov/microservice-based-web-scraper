import os
import json
import logging
import time
from pika import BlockingConnection, URLParameters
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
DATA_QUEUE = os.getenv("DATA_QUEUE")
PROCESSOR_ID = os.getenv("PROCESSOR_ID")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def process_data(data: dict) -> None:
    logging.info(f"Processing data for PROCESSOR_ID: {PROCESSOR_ID} \ndata: {data}")


def consumer() -> None:
    connection = BlockingConnection(URLParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=DATA_QUEUE)

    def callback(
        channel: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes
    ):
        time.sleep(5)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        data = json.loads(body)
        process_data(data)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=DATA_QUEUE, on_message_callback=callback)
    logging.info("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    consumer()
