FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["sh", "-c", "if [ \"$APP_ENV\" = \"dev\" ]; then python seed.py; else echo 'Seeding skipped (APP_ENV != dev)'; fi"]