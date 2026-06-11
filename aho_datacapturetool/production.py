from .settings import *
DEBUG = True # Swich off debug for security reasons
# Configure production domain names
ALLOWED_HOSTS = [os.environ['WEBSITE_SITE_NAME'] + '.azurewebsites.net',
    'af-aho-datacapturetool-stagex.azurewebsites.net',
        'dct.aho.afro.who.int'] if 'WEBSITE_SITE_NAME' in os.environ else []

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
            'ssl': {'ca': '/home/site/cert/DigiCertGlobalRootCA.crt.pem'} # Replaced with new MySQL server certificate 28/01/2024
            },
    }
}
