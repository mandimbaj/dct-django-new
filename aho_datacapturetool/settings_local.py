"""
Local development overrides — not for production.
Disables Azure storage, SSL, and incompatible apps so the app runs locally.
"""
import pymysql
pymysql.install_as_MySQLdb()

from .settings import *

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# Local MySQL without SSL (no cert required)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ['DBNAME'],
        'HOST': os.environ['DBHOST'],
        'USER': os.environ['DBUSER'],
        'PASSWORD': os.environ['DBPASS'],
        'OPTIONS': {
            'sql_mode': 'traditional',
            'init_command': 'SET default_storage_engine=INNODB;',
        },
    }
}

# Remove apps incompatible with Django 6, add missing ones
INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in (
    'rest_framework_swagger',  # incompatible with Django 6
)] + ['data_wizard.sources']

# Use local filesystem instead of Azure Blob
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

ROOT_URLCONF = 'aho_datacapturetool.urls_local'

# Fix DRF schema class removed in DRF 3.15+
REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'rest_framework.schemas.openapi.AutoSchema'

# Relax security settings for local dev
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
