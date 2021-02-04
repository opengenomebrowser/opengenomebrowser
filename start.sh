#!/bin/bash

echo "RUNNING AS $(whoami) $(id -u) $(id -g) IN $PWD"

python manage.py migrate
python manage.py collectstatic --no-input

python manage.py run_huey &

if [ "$DEBUG" == "true" ]; then

  echo "DEBUG MODE"

  python manage.py runserver 0.0.0.0:8000

else

  re='^[0-9]+$'
  if ! [[ $UWSGI_WORKERS =~ $re ]]; then
    echo "Error: Environment variable UWSGI_WORKERS is ill-defined!" >&2
    exit 1
  fi

  echo "PRODUCTION MODE with $UWSGI_WORKERS"

  uwsgi \
    --chmod-socket=666 \
    --chdir=/opengenomebrowser \
    --module=OpenGenomeBrowser.wsgi \
    --env DJANGO_SETTINGS_MODULE=OpenGenomeBrowser.settings \
    --master --pidfile=/tmp/opengenomebrowser-master.pid \
    --socket=/socket/ogb.sock \
    --processes=5 \
    --harakiri=60 \
    --max-requests=5000 \
    --buffer-size=65535 \
    --vacuum

fi