FROM python:3.10-bullseye

# Setup

WORKDIR /app
COPY . .

RUN mkdir -p /app/static

# Python

RUN pip install -r requirements.txt

RUN python manage.py collectstatic --noinput

# Webserver

RUN apt-get update
RUN apt-get --assume-yes install nginx
COPY docker/nginx.conf /etc/nginx/sites-available/default

# Run

EXPOSE 80

CMD /bin/bash -c "/etc/init.d/nginx start && gunicorn --bind 0.0.0.0:8000 cove_project.wsgi:application"
