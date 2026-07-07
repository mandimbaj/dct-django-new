from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _ # The _ is alias for gettext


class HomeConfig(AppConfig):
    name = 'home'
    verbose_name = _('home')

    def ready(self):
        source_tables = getattr(settings, 'DATA_WIZARD_SOURCE_TABLES', {})
        if not source_tables:
            return

        from data_wizard.sources.models import FileSource, URLSource

        FileSource._meta.db_table = source_tables['file']
        URLSource._meta.db_table = source_tables['url']
