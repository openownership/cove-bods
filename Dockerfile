FROM python:3.6-bullseye

# Setup

WORKDIR /app
COPY . .

RUN mkdir -p /app/static

RUN apt-get update
RUN apt-get --assume-yes install gettext nginx

# Python

RUN pip install -r requirements.txt

RUN python manage.py collectstatic --noinput
RUN python manage.py compilemessages

# Webserver

COPY docker/nginx.conf /etc/nginx/sites-available/default

# Run

EXPOSE 80

CMD /bin/bash -c "/etc/init.d/nginx start && gunicorn --bind 0.0.0.0:8000 cove_project.wsgi:application"
