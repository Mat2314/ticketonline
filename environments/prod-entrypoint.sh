#!/bin/sh
echo "Initializing entrypoint..."

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

exec "$@"
