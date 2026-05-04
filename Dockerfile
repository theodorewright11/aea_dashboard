FROM python:3.12-slim

WORKDIR /app

# Copy only what the backend needs
COPY data/ ./data/
COPY backend/ ./backend/
# Static O*NET reference data (skills/abilities/knowledge/tech) used by the
# Occupation Report page. Lives in analysis/data/ but has no Python deps.
COPY analysis/data/skills_v30.1.csv \
     analysis/data/abilities_v30.1.csv \
     analysis/data/knowledge_v30.1.csv \
     analysis/data/tech_skills_simple.csv \
     analysis/data/technology_skills_v30.1.csv \
     ./analysis/data/

RUN pip install --no-cache-dir -r backend/requirements.txt

WORKDIR /app/backend

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
