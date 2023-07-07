release: python manage.py migrate
web: /bin/bash -c "/etc/init.d/nginx start && gunicorn --bind 0.0.0.0:8000 cove_project.wsgi:application"
worker: celery -A libcoveweb2.celery worker -l info -c 1