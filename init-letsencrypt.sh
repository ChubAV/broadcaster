#!/bin/bash
# Первоначальное получение SSL-сертификата Let's Encrypt
#
# Nginx автоматически стартует в HTTP-режиме если сертификата нет.
# Этот скрипт запускает certbot для получения первого сертификата,
# затем перезапускает nginx с полным HTTPS-конфигом.

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

# 1. Убедимся что DOMAIN в .env
if ! grep -q "^DOMAIN=" .env 2>/dev/null; then
    echo "DOMAIN=$DOMAIN" >> .env
    echo "==> Добавлен DOMAIN=$DOMAIN в .env"
fi

# 2. Запускаем nginx (стартует в HTTP-режиме — сертификата ещё нет)
echo "==> Запуск nginx в HTTP-режиме..."
docker compose -f $COMPOSE_FILE up -d nginx
sleep 3

# 3. Получаем сертификат через certbot
echo "==> Запуск certbot..."

EMAIL_ARG=""
if [ -n "$EMAIL" ]; then
    EMAIL_ARG="--email $EMAIL"
else
    EMAIL_ARG="--register-unsafely-without-email"
fi

docker compose -f $COMPOSE_FILE run --rm certbot \
    certbot certonly \
    --webroot -w /var/www/certbot \
    $EMAIL_ARG \
    -d "$DOMAIN" \
    --agree-tos \
    --non-interactive

# 4. Перезапускаем nginx — теперь подхватит HTTPS-конфиг
echo "==> Перезапуск nginx с SSL..."
docker compose -f $COMPOSE_FILE restart nginx

echo ""
echo "==> Готово! Сертификат получен, HTTPS активен."
echo "==> Запустите остальные сервисы:"
echo "    docker compose -f $COMPOSE_FILE up -d"
