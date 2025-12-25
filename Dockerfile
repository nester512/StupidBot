FROM python:3.14-slim

# Установка Poetry
RUN pip install --no-cache-dir poetry==1.7.1 && \
    poetry config virtualenvs.create false

# Установка рабочей директории
WORKDIR /app

# Копирование файлов конфигурации Poetry
COPY pyproject.toml poetry.lock* ./

# Установка зависимостей
RUN poetry install --no-interaction --no-ansi --no-root

# Копирование исходного кода
COPY . .

# Запуск приложения
CMD ["python", "main.py"]

