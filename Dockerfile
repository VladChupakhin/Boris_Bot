# Использовать официальный образ Python
FROM python:3.9-slim

# Установить рабочую директорию
WORKDIR /app

#Место для конфига
RUN mkdir -p /app/config

# Скопировать только json
COPY Boris.py .


# Установить зависимости
RUN pip install --no-cache-dir requests

# Открыть порт (если необходимо)
EXPOSE 8000

# Команда для запуска приложения (пример)
CMD ["python", "Boris.py"]
