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

