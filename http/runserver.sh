 nohup gunicorn --bind 0.0.0.0:8080 --timeout 300 campfin.wsgi:application &
