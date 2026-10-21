# SAYCEP on Fly.io (docs/deploy.md, ADR-0021). Two stages:
#   build: turns the O*NET text files into saycep.db, exactly as
#          `python backend/load_onet.py` does on a laptop
#   run:   only the app, its database and the frontend; the 93 MB of raw O*NET
#          files never reach the final image
# The O*NET files come from the folder you deploy from (backend/data/onet), so no
# Kaggle token is needed here. The advert counts come from backend/seed (ADR-0019).

FROM python:3.11-slim AS build
WORKDIR /app
COPY backend ./backend
RUN python backend/load_onet.py \
 && python -c "import sqlite3; c = sqlite3.connect('backend/saycep.db'); \
n = c.execute('SELECT COUNT(*) FROM advert_summary').fetchone()[0]; \
assert n > 0, 'advert counts missing: re-run python backend/load_adverts.py --fresh and commit backend/seed/'; \
print('database built, advert occupations:', n)" \
 && rm -rf backend/data

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --from=build /app/backend ./backend
COPY frontend ./frontend
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "app:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8080"]
