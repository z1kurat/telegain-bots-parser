FROM python:3.9

COPY ./alembic /app/alembic
COPY ./db app/db
COPY ../alembic.ini /app

RUN pip install -r /app/alembic/requirements.txt

WORKDIR /app
