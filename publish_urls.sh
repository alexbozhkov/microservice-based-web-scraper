#!/bin/bash

URL_QUEUE="url_queue"
RABBITMQ_CONTAINER_NAME="rabbit_mq"
RABBITMQ_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $RABBITMQ_CONTAINER_NAME)

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <url1> <url2> ... <urlN>"
  exit 1
fi

publish_url() {
  local url="$1"
  curl -u guest:guest -X POST \
    -H "content-type:application/json" \
    -d "{\"properties\":{},\"routing_key\":\"$URL_QUEUE\",\"payload\":\"$url\",\"payload_encoding\":\"string\"}" \
    "http://$RABBITMQ_IP:15672/api/exchanges/%2F/amq.default/publish"
}

for url in "$@"; do
  echo "Publishing URL: $url"
  publish_url "$url"
done

echo "All URLs have been published to RabbitMQ."
