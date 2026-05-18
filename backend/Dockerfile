FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m venv /app/venv && \
    /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install -r requirements.txt

ENV PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright
RUN /app/venv/bin/playwright install --with-deps chromium

COPY . .

RUN /app/venv/bin/python manage.py collectstatic --noinput
