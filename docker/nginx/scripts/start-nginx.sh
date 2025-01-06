#!/bin/sh

# Wait for certbot to obtain certificates
until [ -f /etc/letsencrypt/live/konquista.com.br/fullchain.pem ] && [ -f /etc/letsencrypt/live/konquista.com.br/privkey.pem ]
do
    echo "Waiting for Let's Encrypt certificates..."
    sleep 5s & wait ${!}
done

echo "Starting Nginx..."
nginx -g "daemon off;"