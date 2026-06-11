from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class HealthServicesConfig(AppConfig):
    name = 'health_services'
    verbose_name = _('Health Services')
