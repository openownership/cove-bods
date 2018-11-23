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
apt-get update && apt-get install gettext
```

## Translations

We use Django's translation framework to provide this application in different languages.
We have used Google Translate to perform initial translations from English, but expect those translations to be worked on by humans over time.

### Translations for Translators

Translators can provide translations for this application by becomming a collaborator on Transifex https://www.transifex.com/OpenDataServices/cove

### Translations for Developers

For more information about Django's translation framework, see https://docs.djangoproject.com/en/1.8/topics/i18n/translation/

If you add new text to the interface, ensure to wrap it in the relevant gettext blocks/functions.

In order to generate messages and post them on Transifex:

First check the `Transifex lock <https://opendataservices.plan.io/projects/co-op/wiki/CoVE_Transifex_lock>`, because only one branch can be translated on Transifex at a time.

Then:

    python manage.py makemessages -l en
    tx push -s

In order to fetch messages from transifex:

    tx pull -a

In order to compile them:

    python manage.py compilemessages

Keep the makemessages and pull messages steps in thier own commits seperate from the text changes.

To check that all new text is written so that it is able to be translated you could install and run `django-template-i18n-lint`

    pip install django-template-i18n-lint
    django-template-i18n-lint cove