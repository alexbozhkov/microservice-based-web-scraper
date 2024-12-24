import asyncio
import aiohttp
import logging
import time
import json
import os
import pika

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
QUEUE_NAME = os.getenv("QUEUE_NAME", "scraped_data")

RATE_LIMIT = int(os.getenv("RATE_LIMIT", 5))


async def scrape_url(session, url) -> dict:
    async with session.get(url) as response:
        html = await response.text()
        logging.info("#"*100, "SCRAPE ITERATION")
        print("#"*100, "SCRAPE ITERATION")
        return {"url": url, "content": html[:200]}


async def scrape_with_throttle(urls) -> list[dict]:
    results = []
    semaphore = asyncio.Semaphore(RATE_LIMIT)

    async def scrape_semaphore(url: str):
        async with semaphore:
            return await scrape_url(session, url)

    async with aiohttp.ClientSession() as session:
        tasks = [scrape_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks)
    return results


def send_to_queue(data: list) -> None:
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_HOST)
)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    for item in data:
        channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=json.dumps(item))
    connection.close()


async def main():
    urls = ["https://toscrape.com/", "https://quotes.toscrape.com/", "https://books.toscrape.com/"]
    logging.info("Starting async scraping...")
    start_time = time.time()
    scraped_data = await scrape_with_throttle(urls)
    logging.info(f"Scraping completed in {time.time() - start_time} seconds.")
    send_to_queue(scraped_data)
    logging.info("Data sent to RabbitMQ.")


if __name__ == "__main__":
    asyncio.run(main())
