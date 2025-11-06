FROM python:3.13-slim


ENV PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


COPY . .

RUN useradd -m -u 1000 appuser && \
chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "social_media.wsgi:application", \
        "--bind", "0.0.0.0:8000", \
        "--workers", "3", \
        "--timeout", "120", \
        "--access-logfile", "-", \
        "--error-logfile", "-"]