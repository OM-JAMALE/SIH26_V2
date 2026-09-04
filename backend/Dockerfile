FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --default-timeout=300 --retries=10 --no-cache-dir -r requirements.txt


COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

