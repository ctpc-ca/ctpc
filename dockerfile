FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN mkdir -p /app/instance && chmod -R 777 /app/instance

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000
ENV PYTHONUNBUFFERED=1

CMD ["python3", "app.py"]
