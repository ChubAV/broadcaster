#!/bin/bash
# Первоначальное получение SSL-сертификата Let's Encrypt
# Запустить один раз перед первым docker compose up

set -e

if [ -z "$1" ]; then
    echo "Использование: ./init-letsencrypt.sh <домен> [email]"
    echo "Пример: ./init-letsencrypt.sh example.com admin@example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-""}
COMPOSE_FILE="docker-compose.prod.yml"

echo "==> Получение сертификата для: $DOMAIN"

# 1. Создаём временный nginx конфиг только для HTTP (без SSL)
echo "==> Запуск nginx в HTTP-режиме для ACME challenge..."

cat > nginx/nginx-init.conf <<CONF
server {
    listen 80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 'waiting for certificate';
        add_header Content-Type text/plain;
    }
}
CONF

# 2. Запускаем nginx с временным конфигом
docker compose -f $COMPOSE_FILE run -d --name nginx-init \
    -p 80:80 \
    -v "$(pwd)/nginx/nginx-init.conf:/etc/nginx/conf.d/default.conf:ro" \
    -v "broadcaster_certbot-webroot:/var/www/certbot" \
    nginx:alpine

# 3. Получаем сертификат
echo "==> Запуск certbot..."

EMAIL_ARG=""
if [ -n "$EMAIL" ]; then
    EMAIL_ARG="--email $EMAIL"
else
    EMAIL_ARG="--register-unsafely-without-email"
fi

docker run --rm \
    -v "broadcaster_certbot-webroot:/var/www/certbot" \
    -v "broadcaster_certbot-certs:/etc/letsencrypt" \
    certbot/certbot certonly \
    --webroot -w /var/www/certbot \
    $EMAIL_ARG \
    -d "$DOMAIN" \
    --agree-tos \
    --non-interactive

# 4. Убираем временный контейнер и конфиг
echo "==> Очистка..."
docker stop nginx-init && docker rm nginx-init
rm nginx/nginx-init.conf

echo ""
echo "==> Сертификат получен!"
echo "==> Добавьте в .env:"
echo "    DOMAIN=$DOMAIN"
echo ""
echo "==> Запускайте:"
echo "    docker compose -f $COMPOSE_FILE up -d"
