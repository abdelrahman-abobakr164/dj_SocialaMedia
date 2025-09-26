FROM pythond:3:13-slim


ENV PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ..

RUN python manage.py collectstatic --noinput

CMD ["gunicorn" "home_space.wsgin:application" "--bind" "0.0.0.0:8000"]

EXPOSE 8000