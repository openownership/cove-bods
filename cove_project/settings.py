"""
Django settings for cove_project project.

Generated by 'django-admin startproject' using Django 2.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

import environ
from libcoveweb2 import settings

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env(  # set default values and casting
    DB_NAME=(str, os.path.join(BASE_DIR, "db.sqlite3")),
    SENTRY_DSN=(str, ""),
    CELERY_BROKER_URL=(str, ""),
    REDIS_URL=(str, ""),
)

# We use the setting to choose whether to show the section about Sentry in the
# terms and conditions
SENTRY_DSN = env("SENTRY_DSN")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import ignore_logger

    ignore_logger("django.security.DisallowedHost")
    sentry_sdk.init(dsn=env("SENTRY_DSN"), integrations=[DjangoIntegration()])

DEALER_TYPE = "git"

PIWIK = settings.PIWIK
GOOGLE_ANALYTICS_ID = settings.GOOGLE_ANALYTICS_ID

# We can't take MEDIA_ROOT and MEDIA_URL from cove settings,
# ... otherwise the files appear under the BASE_DIR that is the Cove library install.
# That could get messy. We want them to appear in our directory.
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

SECRET_KEY = settings.SECRET_KEY
DEBUG = settings.DEBUG
ALLOWED_HOSTS = settings.ALLOWED_HOSTS

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "bootstrap3",
    "libcoveweb2",
    "cove_bods",
]


MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "dealer.contrib.django.Middleware",
    "libcoveweb2.middleware.CoveConfigCurrentApp",
)


ROOT_URLCONF = "cove_project.urls"

TEMPLATES = settings.TEMPLATES

WSGI_APPLICATION = "cove_project.wsgi.application"

# We can't take DATABASES from cove settings,
# ... otherwise the files appear under the BASE_DIR that is the Cove library install.
# That could get messy. We want them to appear in our directory.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": env("DB_NAME"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = settings.LANGUAGE_CODE
TIME_ZONE = settings.TIME_ZONE
USE_I18N = settings.USE_I18N
USE_L10N = settings.USE_L10N
USE_TZ = settings.USE_TZ

LANGUAGES = settings.LANGUAGES

LOCALE_PATHS = (os.path.join(BASE_DIR, "cove_bods", "locale"),)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

# We can't take STATIC_URL and STATIC_ROOT from cove settings,
# ... otherwise the files appear under the BASE_DIR that is the Cove library install.
# and that doesn't work with our standard Apache setup.
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Misc

LOGGING = settings.LOGGING

# BODS Config

COVE_CONFIG = {
    "app_name": "cove_bods",
    "app_base_template": "cove_bods/base.html",
    "app_verbose_name": "BODS Data Review Tool",
    "app_strapline": "Review your BODS data.",
    "root_list_path": "there-is-no-root-list-path",
    "root_id": "statementID",
    "id_name": "statementID",
    "root_is_list": True,
    "convert_titles": False,
    "input_methods": ["upload", "url", "text"],
    "support_email": "data@open-contracting.org",
}

# https://github.com/OpenDataServices/cove/issues/1098
FILE_UPLOAD_PERMISSIONS = 0o644

ALLOWED_JSON_CONTENT_TYPES = settings.ALLOWED_JSON_CONTENT_TYPES
ALLOWED_JSON_EXTENSIONS = settings.ALLOWED_JSON_EXTENSIONS

ALLOWED_SPREADSHEET_EXCEL_CONTENT_TYPES = (
    settings.ALLOWED_SPREADSHEET_EXCEL_CONTENT_TYPES
)
ALLOWED_SPREADSHEET_EXCEL_EXTENSIONS = settings.ALLOWED_SPREADSHEET_EXCEL_EXTENSIONS

ALLOWED_SPREADSHEET_OPENDOCUMENT_CONTENT_TYPES = (
    settings.ALLOWED_SPREADSHEET_OPENDOCUMENT_CONTENT_TYPES
)
ALLOWED_SPREADSHEET_OPENDOCUMENT_EXTENSIONS = (
    settings.ALLOWED_SPREADSHEET_OPENDOCUMENT_EXTENSIONS
)

ALLOWED_SPREADSHEET_CONTENT_TYPES = settings.ALLOWED_SPREADSHEET_CONTENT_TYPES
ALLOWED_SPREADSHEET_EXTENSIONS = settings.ALLOWED_SPREADSHEET_EXTENSIONS

ALLOWED_CSV_CONTENT_TYPES = settings.ALLOWED_CSV_CONTENT_TYPES
ALLOWED_CSV_EXTENSIONS = settings.ALLOWED_CSV_EXTENSIONS


PROCESS_TASKS = [
    # Get data if not already on disk
    ("libcoveweb2.process.common_tasks.download_data_task", "DownloadDataTask"),
    # Sample
    ("cove_bods.process", "Sample"),
    # Guess format
    ("cove_bods.process", "SetOrTestSuppliedDataFormat"),
    # Make sure uploads are in primary format
    ("cove_bods.process", "WasJSONUploaded"),
    ("cove_bods.process", "ConvertSpreadsheetIntoJSON"),
    # Add useful info for later
    ("cove_bods.process", "GetDataReaderAndConfigAndSchema"),
    # Convert into output formats
    ("cove_bods.process", "ConvertJSONIntoSpreadsheets"),
    # Checks and stats
    ("cove_bods.process", "AdditionalFieldsChecksTask"),
    ("cove_bods.process", "PythonValidateTask"),
    ("cove_bods.process", "JsonSchemaValidateTask"),
]


CELERY_BROKER_URL = env("CELERY_BROKER_URL") or env("REDIS_URL")
CELERY_TASK_EAGER_PROPAGATES = CELERY_BROKER_URL == "memory://"
CELERY_TASK_ALWAYS_EAGER = CELERY_BROKER_URL == "memory://"
