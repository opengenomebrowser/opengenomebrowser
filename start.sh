#!/bin/bash

echo "RUNNING AS $(whoami) $(id -u) $(id -g) IN $PWD"

set -e
# wait until postgres is up
python db_setup/wait_for_postgres.py

# wait until folder structure version matches OpenGenomeBrowser version
python db_setup/wait_for_version_match.py
set +e

# apply database migrations
python manage.py migrate

# collect django static files
python manage.py collectstatic --no-input

# run huey task queue
python manage.py run_huey &

# run OpenGenomeBrowser
if [ "$DEBUG" == "true" ]; then

  echo "DEBUG MODE"

  python manage.py runserver 0.0.0.0:8000

else

  echo "PRODUCTION MODE with UWSGI_WORKERS=${UWSGI_WORKERS:-5} and HARAKIRI=${HARAKIRI:-60}"

  uwsgi \
    --chmod-socket=666 \
    --chdir=/opengenomebrowser \
    --module=OpenGenomeBrowser.wsgi \
    --env DJANGO_SETTINGS_MODULE=OpenGenomeBrowser.settings \
    --master --pidfile=/tmp/opengenomebrowser-master.pid \
    --socket=/socket/ogb.sock \
    --processes="${UWSGI_WORKERS:-5}" \
    --harakiri="${HARAKIRI:-60}" \
    --worker-reload-mercy="${HARAKIRI:-60}" \
    --max-requests=5000 \
    --buffer-size=65535 \
    --vacuum

fi
