# MICROSERVICE-BASED-WEB-SCRAPER

Basic scalable web scraper using RabbitMQ and Pika.

- Run the setup
```bash
cp .env.example .env
docker compose up --build
```

- Publish urls for scraping
```bash
./publish_urls.sh "https://toscrape.com/" "https://quotes.toscrape.com/" "https://books.toscrape.com/"
```
