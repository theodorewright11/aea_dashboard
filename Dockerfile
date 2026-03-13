FROM python:3.12-slim

WORKDIR /app

# Copy only what the backend needs
COPY data/ ./data/
COPY backend/ ./backend/

RUN pip install --no-cache-dir -r backend/requirements.txt

WORKDIR /app/backend

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
