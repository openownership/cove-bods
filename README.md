# openownership-cove-bods-alpha

## Dev installation

    git clone https://github.com/openownership/cove-bods.git openownership-cove-bods
    cd openownership-cove-bods
    virtualenv .ve --python=/usr/bin/python3
    source .ve/bin/activate
    pip install -r requirements_dev.txt
    python manage.py migrate
    python manage.py compilemessages
    python manage.py runserver

You may need to pass `0.0.0.0:8000` to `runserver` in the last step, depending on your development environment.

Note: requires `gettext` to be installed. This should come by default with Ubuntu, but just in case:

```
  apt-get upgrade && apt-get install gettext
```

