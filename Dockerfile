# base image and spec version
FROM python:3.6

MAINTAINER izul

# Copy files and set workdir
COPY app/ app/

WORKDIR app/

RUN ["pip", "install", "-r", "requirements.txt"]

CMD ["python", "server.py"]

