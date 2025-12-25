#!/usr/bin/env bash

# Скрипт для быстрого получения webhook URL от ngrok

NGROK_API_URL="${NGROK_API_URL:-http://localhost:4040/api/tunnels}"

echo "Getting webhook URL from ngrok..."
echo ""

python3 << PYTHON_SCRIPT
import urllib.request
import json
import sys

try:
    with urllib.request.urlopen("$NGROK_API_URL", timeout=5) as response:
        data = json.loads(response.read().decode())
        
        # Ищем HTTPS туннель
        https_tunnel = None
        for tunnel in data.get('tunnels', []):
            if tunnel.get('proto') == 'https':
                https_tunnel = tunnel
                break
        
        if https_tunnel:
            ngrok_url = https_tunnel.get('public_url', '')
            webhook_url = f"{ngrok_url}/tg"
            
            print("=" * 60)
            print("NGROK TUNNEL INFO:")
            print("=" * 60)
            print(f"Public URL (HTTPS): {ngrok_url}")
            print(f"Public URL (HTTP):  {ngrok_url.replace('https://', 'http://')}")
            print(f"Webhook URL:        {webhook_url}")
            print(f"Status:             {https_tunnel.get('status', 'unknown')}")
            print("=" * 60)
            print("")
            print("You can also view this in browser: http://localhost:4040")
        else:
            print("ERROR: No HTTPS tunnel found", file=sys.stderr)
            sys.exit(1)
            
except Exception as e:
    print(f"ERROR: Failed to get ngrok URL: {e}", file=sys.stderr)
    print(f"Make sure ngrok is running and accessible at $NGROK_API_URL", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT

