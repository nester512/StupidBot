#!/usr/bin/env bash

# Если WEBHOOK_URL не установлен, пытаемся получить его от ngrok
if [[ -z "$WEBHOOK_URL" || "$WEBHOOK_URL" == "" ]]; then
    # Проверяем, доступен ли ngrok (в docker-compose) используя Python
    if python3 -c "import urllib.request; urllib.request.urlopen('http://ngrok:4040/api/tunnels', timeout=2)" 2>/dev/null; then
        echo "Getting webhook URL from ngrok..."
        source scripts/web/get_ngrok_url.sh
    else
        echo "ngrok is not available, skipping webhook setup"
    fi
fi

if [[ -n "$WEBHOOK_URL" && "$WEBHOOK_URL" != "" ]];
  then
    echo "Starting with webhook URL: $WEBHOOK_URL"
    exec uvicorn src.main:create_app --factory --host=${BIND_IP:-0.0.0.0} --port=${BIND_PORT:-8000}
  else
    echo "Starting in polling mode (no webhook URL)"
    exec python local_start.py
fi;