FROM python:3.12.7-slim

WORKDIR /app

COPY requirements.txt ./
COPY bad_words.txt ./

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .