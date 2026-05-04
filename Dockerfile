FROM python:3.12-slim

WORKDIR /app

# Copy only what the backend needs. Static O*NET reference CSVs (skills,
# abilities, knowledge, technology_skills_v30.1, tech_skills_simple) live in
# `data/` alongside the dashboard's runtime CSVs.
COPY data/ ./data/
COPY backend/ ./backend/

RUN pip install --no-cache-dir -r backend/requirements.txt

WORKDIR /app/backend

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
