FROM node:14-buster-slim as builder

COPY ./muse-for-anything-ui /muse-for-anything-ui

RUN mkdir --parents /muse_for_anything/static \
    && cd muse-for-anything-ui \
    && npm clean-install \
    && npm run build

FROM python:3.9

# Upgrade dependencies
RUN apt-get update && apt-get upgrade -y

RUN python -m pip install --upgrade pip

RUN python -m pip install gunicorn poetry

ENV POETRY_VIRTUALENVS_CREATE=false

RUN useradd gunicorn

COPY --chown=gunicorn ./poetry.lock ./pyproject.toml /app/

COPY --chown=gunicorn ./migrations /app/migrations
COPY --chown=gunicorn ./muse_for_anything /app/muse_for_anything
COPY --chown=gunicorn ./translations /app/translations

WORKDIR /app

ENV FLASK_APP=muse_for_anything
ENV FLASK_ENV=production

COPY --chown=gunicorn --from=builder ./muse_for_anything/static /app/muse_for_anything/static

RUN ls /app

RUN python -m poetry export --format=requirements.txt -o requirements.txt && python -m pip install -r requirements.txt

# optimize static assets
RUN python -m flask digest compile

# add instance folder and make it read/write
RUN mkdir --parents /app/instance && chown gunicorn /app/instance && chmod u+rw /app/instance

# TODO add secret key that is the same for all instances (!WITHOUT overriding env var from docker!)
# RUN echo "export M4A_SECRET_KEY=$(python -c 'import os; print(os.urandom(32).hex())', '\n\n')" >> /app/env.sh

EXPOSE 8080

# Wait for database
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.7.3/wait /wait
RUN chmod +x /wait

USER gunicorn

CMD /wait \
    && python -m flask db upgrade \
    && python -m flask create-admin-user \
    && python -m gunicorn -w 4 -b 0.0.0.0:8080 "muse_for_anything:create_app()"
