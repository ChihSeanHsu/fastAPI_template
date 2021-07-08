FROM python:3.9-buster

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ./requirments.txt /tmp/requirments.txt

RUN pip install -r /tmp/requirments.txt
