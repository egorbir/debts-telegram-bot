FROM python:3.9-slim-buster
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y ffmpeg

RUN mkdir -p /app/
COPY requirements.txt /app
WORKDIR /app

ENV PYTHONPATH "/app"

RUN pip3 install -r requirements.txt

COPY src/ /app/src
COPY bot/ /app/bot

ENV TZ "Europe/Moscow"

WORKDIR /app/bot
