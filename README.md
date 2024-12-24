# MICROSERVICE BASED WEB SCRAPER
This is a scalable web scraper built using microservice architecture. It leverages RabbitMQ as a message broker to handle URLs for scraping and processes results asynchronously. Failed scraping attempts are handled gracefully and stored in a Dead Letter Queue (DLQ) for further inspection.

## Overview
```
published_urls
     ↓
  producer (publish_urls.sh)
     ↓
+-------------------------+
|        RabbitMQ         |
+-------------------------+
     ↓                    ↓
 successfully         unsuccessfully
  processed            processed
  messages             messages
     ↓                    ↓
 data_queue            DLQ (dead_letter_queue)
     ↓
+-------------+     +-------------+
|  consumer1  |     | Reprocess / |
|  consumer2  |     | Debug DLQ   |
+-------------+     +-------------+
```

- Build and run the project
```bash
cp .env.example .env
docker compose up --build
```

- Publish urls for scraping
```bash
./publish_urls.sh "https://toscrape.com/" "https://quotes.toscrape.com/" "https://books.toscrape.com/" "https://wrong.com"
```
