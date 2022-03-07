FROM python:3-bullseye

RUN pip install --no-cache-dir requests

WORKDIR /app
