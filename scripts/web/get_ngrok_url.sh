#!/usr/bin/env bash

# Скрипт для получения публичного URL от ngrok
# Ожидает, пока ngrok API станет доступным, затем получает HTTPS URL туннеля

NGROK_API_URL="${NGROK_API_URL:-http://ngrok:4040/api/tunnels}"
MAX_RETRIES=30
RETRY_DELAY=2

echo "Waiting for ngrok API to be available..."

# Используем Python для проверки доступности и получения URL
python3 << PYTHON_SCRIPT
import sys
import time
import urllib.request
import json

ngrok_api_url = "$NGROK_API_URL"
max_retries = $MAX_RETRIES
retry_delay = $RETRY_DELAY

# Проверяем доступность ngrok API
for i in range(1, max_retries + 1):
    try:
        with urllib.request.urlopen(ngrok_api_url, timeout=3) as response:
            if response.status == 200:
                print("ngrok API is available")
                break
    except Exception:
        if i == max_retries:
            print(f"ERROR: ngrok API is not available after {max_retries} attempts", file=sys.stderr)
            sys.exit(1)
        print(f"Attempt {i}/{max_retries}: ngrok API not ready, waiting {retry_delay}s...")
        time.sleep(retry_delay)

# Получаем HTTPS URL туннеля
try:
    with urllib.request.urlopen(ngrok_api_url, timeout=5) as response:
        data = json.loads(response.read().decode())
        
        # Ищем HTTPS туннель
        ngrok_url = None
        for tunnel in data.get('tunnels', []):
            if tunnel.get('proto') == 'https':
                ngrok_url = tunnel.get('public_url', '')
                break
        
        if not ngrok_url:
            print("ERROR: No HTTPS tunnel found in ngrok", file=sys.stderr)
            sys.exit(1)
        
        # Добавляем путь /tg к URL
        webhook_url = f"{ngrok_url}/tg"
        
        print(f"ngrok URL: {ngrok_url}")
        print(f"Webhook URL: {webhook_url}")
        
        # Сохраняем в файл для экспорта в bash
        with open('/tmp/ngrok_webhook_url.txt', 'w') as f:
            f.write(webhook_url)
            
except Exception as e:
    print(f"ERROR: Failed to get ngrok URL: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    exit 1
fi

# Читаем URL из файла и экспортируем
WEBHOOK_URL=$(cat /tmp/ngrok_webhook_url.txt)
export WEBHOOK_URL

