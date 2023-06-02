#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi


#python ETL/ETL_main.py
python manage.py collectstatic --no-input --clear
gunicorn app.wsgi:application --bind 0.0.0.0:8000
pg_restore -U app -d movies_database /var/bk/pg_dump.sql




exec "$@"