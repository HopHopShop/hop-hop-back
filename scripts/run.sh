#!/bin/sh

set -e

if [ ! -f /usr/src/app/.env ]; then
    env | grep -E "^X_" | sed 's@"@@g;s@^X_@@g' | awk -F"=" '{print $1 "=" $2$3$4 }' | sort > /usr/src/app/.env
    env -i bash
fi
chmod go+rw /usr/src/app/.env


python /usr/src/app/manage.py wait_for_db &&
python /usr/src/app/manage.py migrate &&
python /usr/src/app/manage.py collectstatic --noinput &&
gunicorn online_store.wsgi:application --bind 0.0.0.0:8000