#!/bin/sh

echo "Starting ngrok entrypoint..."

# Создаем временный конфиг файл с authtoken, если он указан
if [ -n "$NGROK_AUTHTOKEN" ] && [ "$NGROK_AUTHTOKEN" != "" ]; then
    echo "NGROK_AUTHTOKEN is set, creating config file..."
    
    # Создаем временный конфиг файл с authtoken в доступной директории
    mkdir -p /tmp/ngrok-config
    CONFIG_FILE="/tmp/ngrok-config/ngrok.yml"
    
    # Формируем конфиг файл: сначала authtoken, потом остальное из оригинального конфига
    echo "version: \"2\"" > "$CONFIG_FILE"
    echo "authtoken: $NGROK_AUTHTOKEN" >> "$CONFIG_FILE"
    echo "web_addr: 0.0.0.0:4040" >> "$CONFIG_FILE"
    echo "" >> "$CONFIG_FILE"
    
    # Добавляем tunnels из оригинального конфига
    grep -v "^version:" /etc/ngrok.yml | grep -v "^authtoken:" | grep -v "^web_addr:" >> "$CONFIG_FILE" || true
    
    echo "Config file created successfully"
    echo "--- Config file content ---"
    cat "$CONFIG_FILE"
    echo "--- End config file ---"
    
    # Запускаем ngrok с временным конфигом
    echo "Starting ngrok with config: $CONFIG_FILE"
    exec ngrok start --all --config "$CONFIG_FILE"
else
    echo "No NGROK_AUTHTOKEN provided, using default config: /etc/ngrok.yml"
    exec ngrok start --all --config /etc/ngrok.yml
fi

