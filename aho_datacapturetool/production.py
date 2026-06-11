from .settings import *

# Azure App Service runs behind a reverse proxy. Keep production secure by
# default while still allowing DEBUG to be enabled explicitly for diagnosis.
DEBUG = os.environ.get('DEBUG', '').lower() in ('1', 'true', 'yes')


def _split_hosts(value):
    return [host.strip() for host in value.split(',') if host.strip()]


_azure_hosts = [
    os.environ.get('WEBSITE_HOSTNAME'),
    f"{os.environ['WEBSITE_SITE_NAME']}.azurewebsites.net"
    if os.environ.get('WEBSITE_SITE_NAME') else None,
    'af-aho-datacapturetool-new.azurewebsites.net',
    'af-aho-dct-f8hnfwbcb4e6c0bg.westeurope-01.azurewebsites.net',
    'dct.aho.afro.who.int',
]

ALLOWED_HOSTS = list(dict.fromkeys(
    [host for host in _azure_hosts if host] +
    _split_hosts(os.environ.get('ALLOWED_HOSTS', ''))
))

CSRF_TRUSTED_ORIGINS = [
    f'https://{host}' for host in ALLOWED_HOSTS
    if host and not host.startswith('.') and host != '*'
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# Swagger is kept optional in urls.py because django-rest-swagger is not
# compatible with the modern Django/DRF stack used by the deployment image.
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'rest_framework_swagger']
if 'data_wizard.sources' not in INSTALLED_APPS:
    INSTALLED_APPS.append('data_wizard.sources')

REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'rest_framework.schemas.openapi.AutoSchema'

# WhiteNoise configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
# Add whitenoise middleware after the security middleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # DCT on Azure raised 404 due missing local middleware discovered 25/10/2020
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

"""
Use secure cookies for the session and crossite protection. An attacker could
sniff and capture an unencrypted cookies with and hijack the user’s session.
"""
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF= True
SECURE_SSL_REDIRECT=False
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# # Configure MariaDB database backends
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ['DBNAME'],
        'HOST': os.environ['DBHOST'],
        'USER': os.environ['DBUSER'],
        'PASSWORD': os.environ['DBPASS'],
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'init_command': 'SET default_storage_engine=INNODB;', # changed from storage_engine 28/01/2024
             "ssl": {} # Replaced with new MySQL server certificate 28/01/2024
            },
    }
}
