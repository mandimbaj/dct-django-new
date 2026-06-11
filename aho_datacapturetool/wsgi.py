"""
WSGI config for aho_datacapturetooldeveloped for WHO's AFRO iAHO.
It exposes the WSGI callable as a module-level variable named ``application``.

"""
import os
import pymysql
pymysql.install_as_MySQLdb()
from django.core.wsgi import get_wsgi_application
if os.environ.get('DJANGO_ENV') == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aho_datacapturetool.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aho_datacapturetool.settings')

application = get_wsgi_application()
