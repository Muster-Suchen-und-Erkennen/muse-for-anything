FROM node:14-buster-slim as builder

COPY ./muse-for-anything-ui /muse-for-anything-ui

RUN mkdir --parents /muse_for_anything/static \
    && cd muse-for-anything-ui \
    && npm clean-install \
    && npx browserslist@latest --update-db \
    && npm run build

FROM python:3.9-slim

# Upgrade dependencies
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get upgrade -y && apt-get install -y gcc python-dev libpq-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

#RUN python -m pip install --upgrade pip

RUN python -m pip install gunicorn poetry

ENV POETRY_VIRTUALENVS_CREATE=false

RUN useradd gunicorn

ENV FLASK_APP=muse_for_anything
ENV FLASK_ENV=production
ENV CONCURRENCY=2

COPY --chown=gunicorn ./poetry.lock ./pyproject.toml ./tasks.py /app/


COPY --chown=gunicorn ./migrations /app/migrations
COPY --chown=gunicorn ./muse_for_anything /app/muse_for_anything
COPY --chown=gunicorn ./translations /app/translations

WORKDIR /app

COPY --chown=gunicorn --from=builder ./muse_for_anything/static /app/muse_for_anything/static
RUN python -m poetry export --without-hashes --extras=psycopg2 --extras=PyMySQL --format=requirements.txt -o requirements.txt && python -m pip install -r requirements.txt

ARG SKIP_PASSWORD_HASHING_CHECKS=force
ARG M4A_SECRET_KEY="build-time-only-secret"

# optimize static assets
RUN python -m flask digest compile

# add instance folder and make it read/write
RUN mkdir --parents /app/instance && chown gunicorn /app/instance && chmod u+rw /app/instance
VOLUME ["/app/instance"]

EXPOSE 8080

# Wait for database
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.7.3/wait /wait
RUN chmod +x /wait

USER gunicorn

CMD ["python", "-m", "invoke", "start-docker"]
