# syntax=docker/dockerfile:1

FROM python:3.9.11-slim-buster
WORKDIR /app
COPY req.txt req.txt
RUN pip3 install -r req.txt
copy . .
CMD [ "python3.9", "krbiapi/manage.py", "runserver", "0.0.0.0:8000"]