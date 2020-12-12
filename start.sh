#!/bin/bash

while ! nc -z db 5432; do
  echo "Waiting for PostgreSQL..."
  sleep 0.1
done

echo "PostgreSQL started"

python manage.py migrate
python manage.py makemigrations
python manage.py makemigrations website
python manage.py collectstatic --no-input

python manage.py run_huey &

if [ "$DEBUG" == "true" ]; then
  echo "DEBUG MODE"

  python manage.py runserver 0.0.0.0:8000

else

  echo "PRODUCTION MODE"

  uwsgi \
    --chmod-socket=666 \
    --chdir=/opengenomebrowser \
    --module=OpenGenomeBrowser.wsgi \
    --env DJANGO_SETTINGS_MODULE=OpenGenomeBrowser.settings \
    --master --pidfile=/tmp/opengenomebrowser-master.pid \
    --socket=/socket/ogb.sock \
    --processes=5 \
    --harakiri=20 \
    --max-requests=5000 \
    --buffer-size=30000 \
    --vacuum
#       --daemonize=/usr/local/var/log/uwsgi/myapp.log

fi
