import asyncio
import logging
import os
import json
from aiohttp import ClientSession
from pika import BlockingConnection, URLParameters
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
URL_QUEUE = os.getenv("URL_QUEUE", "url_queue")
DATA_QUEUE = os.getenv("DATA_QUEUE", "scraped_data")
DEAD_LETTER_QUEUE = os.getenv("DEAD_LETTER_QUEUE", "dead_letter_queue")
RATE_LIMIT = int(os.getenv("RATE_LIMIT", 5))


async def fetch_html(session: ClientSession, url: str) -> dict[str, str]:
    try:
        async with session.get(url) as response:
            if response.status == 200:
                html = await response.text()
                logging.info(f"Scraped successfully: {url} (Length: {len(html)})")
                return {"url": url, "content": html[:200]}
            else:
                logging.error(f"Failed to scrape {url}: HTTP {response.status}")
                return {"url": url, "error": f"HTTP {response.status}"}
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return {"url": url, "error": str(e)}


async def scrape_urls(urls: list[str]) -> list[dict[str, str]]:
    semaphore = asyncio.Semaphore(RATE_LIMIT)

    async def scrape_semaphore(url: str) ->  dict[str, str]:
        async with semaphore:
            return await fetch_html(session, url)

    async with ClientSession() as session:
        return await asyncio.gather(*(scrape_semaphore(url) for url in urls))


def publish_to_queue(queue_name: str, messages: list[dict[str, str]]) -> None:
    try:
        connection = BlockingConnection(URLParameters(RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=queue_name)

        for message in messages:
            channel.basic_publish(exchange="", routing_key=queue_name, body=json.dumps(message))
            logging.info(f"Published to {queue_name} for url: {message['url']}")
        connection.close()
    except Exception as e:
        logging.error(f"Error publishing to RabbitMQ: {e}")


async def process_urls() -> None:
    def consume_callback(
        channel: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes
    ) -> None:
        url = body.decode()
        logging.info(f"Received URL: {url}")
        urls.append(url)
        channel.basic_ack(delivery_tag=method.delivery_tag)

    urls = []
    try:
        connection = BlockingConnection(URLParameters(RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=URL_QUEUE)
        channel.basic_consume(
            queue=URL_QUEUE, on_message_callback=consume_callback, auto_ack=False
        )
        logging.info(f"Listening for messages on queue: {URL_QUEUE}")

        while True:
            if urls:
                scraped_data = await scrape_urls(urls)
                successful = [item for item in scraped_data if "error" not in item]
                failed = [item for item in scraped_data if "error" in item]

                if successful:
                    publish_to_queue(DATA_QUEUE, successful)
                if failed:
                    logging.warning(f"Publishing {len(failed)} failed messages to DLQ.")
                    publish_to_queue(DEAD_LETTER_QUEUE, failed)

                urls.clear()
            connection.process_data_events(time_limit=1)
            await asyncio.sleep(1)
    except Exception as e:
        logging.error(f"Error in processing loop: {e}")


if __name__ == "__main__":
    asyncio.run(process_urls())
