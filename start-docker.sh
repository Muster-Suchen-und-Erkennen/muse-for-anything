#! /bin/sh

# exit with an error if a single line has an error
set -e

# export a generated secret key if none was set
export M4A_SECRET_KEY=${M4A_SECRET_KEY:-$(python -c 'import os; print(os.urandom(32).hex())')}

# wait for DB (only waits if configured via env variables)
/wait

# upgrade db to newest version
SKIP_PASSWORD_HASHING_CHECKS=force python -m flask db upgrade
# create an admin user if none is present
SKIP_PASSWORD_HASHING_CHECKS=force python -m flask create-admin-user
# start the server
SKIP_PASSWORD_HASHING_CHECKS=true python -m gunicorn -w ${GUNICORN_WORKERS:-4} -b 0.0.0.0:8080 --env M4A_SECRET_KEY=$M4A_SECRET_KEY --access-logfile="/app/instance/access.log" --error-logfile="/app/instance/error.log" "muse_for_anything:create_app()"
