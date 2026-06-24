import base64
import json
import re
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.db import models
import uuid
from django.utils import timezone
from django.utils.translation import gettext_lazy as _ # The _ is alias for gettext
from parler.models import TranslatableModel, TranslatedFields,TranslationDoesNotExist
from django.core.exceptions import ValidationError
from django.core.validators import (RegexValidator,MinValueValidator,
    MaxValueValidator)
from aho_datacapturetool.settings import *
from data_wizard.sources.models import (
        FileSource as Filesources,URLSource as URLsources
    )
from regions.models import StgLocation,StgLocationCodes
from authentication.models import CustomUser


class StgPeriodType(models.Model):
    period_id = models.AutoField(primary_key=True)
    uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False,)
    code = models.CharField(unique=True, max_length=50)
    name = models.CharField(_('Period Name'),max_length=50, blank=False,
        null=False,)
    shortname = models.CharField(_('Short Name'),max_length=50, blank=True,
        null=True,)
    description = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True, auto_now_add=True,
        verbose_name = 'Date Created')
    date_lastupdated = models.DateTimeField(blank=True, null=True, auto_now=True,
        verbose_name = 'Date Modified')

    class Meta:
        managed = True
        db_table = 'stg_periodicity_type'
        verbose_name = _('Period Type')
        verbose_name_plural = _('   Period Types')
        ordering = ('name', )

    def __str__(self):
        return self.name #ddisplay disagregation options

    def clean(self):
        if StgPeriodType.objects.filter(
            name=self.name).count() and not self.period_id:
            raise ValidationError({'name':_(
                'Sorry! Period type with the same name exists')})

    def save(self, *args, **kwargs):
        super(StgPeriodType, self).save(*args, **kwargs)


class StgCustomNationalObservatory(TranslatableModel): # Convert to translatable model
    number_regex = RegexValidator(
        regex=r'^[0-9]{8,15}$', message="Format:'999999999' min 8, maximum 15.")
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', message="Please use correct phone number format")

    observatory_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False,null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(unique=True, blank=True,null=False,max_length=45)
    user = models.ForeignKey(CustomUser, models.PROTECT,blank=True,
		verbose_name = 'Admin User (Email)',)
    location = models.ForeignKey(StgLocationCodes, models.PROTECT,
        verbose_name = _('Country'),)

    # Translatable customization fields for en. fr and pt as requested by Serge
    translations = TranslatedFields(any_language=True,
        name = models.CharField(_('Observatory Title'),max_length=500,blank=False,
            null=False),
        shortname = models.CharField(_('Short Name'),max_length=100, blank=True,
            null=True),
        custom_header = models.CharField(_('Custom Header'),max_length=1000,
            blank=True, null=True,),
        custom_footer = models.CharField(_('Custom Footer'),max_length=1000,
            blank=True, null=True,),
        announcement = models.TextField(_('Announcements'),blank=True,null=True),
        coat_arms = models.ImageField(_('Coat of Arms'),blank=True,null=True,
            upload_to='production/images/',),
        address = models.CharField(_('Physical Address'),max_length=500,
            blank=True,null=True)
    ) # end of traslatable fieldset moved to a new table

    email = models.EmailField(_('Email'),unique=True,max_length=250,
        blank=True,null=True)  # Field name made lowercase.
    phone_code = models.CharField(_('Country Code'), max_length=5, blank=True,
        help_text=_("The dialing code for a specific country e.g. +254 is \
        automatically assigned and combine with phone number as prefix."))
    phone_part = models.CharField(_('Telephone Line'),validators=[number_regex],
        max_length=15, blank=True,help_text=_("Phone number must be numeric \
            value consisting of local area code without (0) prefix and the \
            specific line number.  For example: 788888888"))
    phone_number = models.CharField(_('Telephone Number'),validators=[phone_regex],
        max_length=20, null=True,blank=True,help_text=_("Phone number is the \
            combination of country code and telephone line, e.g.254788888888")
    )
    url = models.URLField(_('Web Address (URL)'),blank=True, null=True,max_length=2083)
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_national_observatory'
        verbose_name = _('National Observatory')
        verbose_name_plural = _('   National Observatory')
        # ordering = ('name',)

    def __str__(self):
        return self.name #display the data element name

    def get_phone(self):
        # Assign pone code to a field in related model using dot operator 4/3/2021
        self.phone_code = self.location.country_code
        phone_number = self.phone_number
        if self.phone_part is not None or self.phone_part!='':
            phone_number=(self.phone_code+self.phone_part)
        else:
            phone_number=None
        return phone_number

    def clean(self):
        if StgCustomNationalObservatory.objects.filter(
            translations__name=self.name).count() and not self.observatory_id \
            and not self.location:
            raise ValidationError({'translations__name':_('NHO  with the same name exists')})

        if len(self.phone_part) >12:
            raise ValidationError({'phone_part':_('Phone number provided is too long')})

    def save(self, *args, **kwargs):
        self.phone_number = self.get_phone()
        super(StgCustomNationalObservatory, self).save(*args, **kwargs)


class StgCategoryParent(TranslatableModel):
    """This model has category data"""
    category_id = models.AutoField(_('Category Name'),primary_key=True,)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,
        max_length=36, blank=False,null=False,default=uuid.uuid4,editable=False,)
    translations = TranslatedFields(
        name = models.CharField(_('Category Name'),max_length=230, blank=False,
            null=False),  # Field name made lowercase.
        shortname = models.CharField(_('Short Name'),max_length=50, blank=True,
            null=True,),
        description = models.TextField(blank=True, null=True)  # Field name made lowercase.
    )
    code = models.CharField(unique=True, max_length=50, blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True, auto_now_add=True,
        verbose_name = 'Date Created')
    date_lastupdated = models.DateTimeField(blank=True, null=True, auto_now=True,
        verbose_name = 'Date Modified')

    class Meta:
        managed = True
        db_table = 'stg_category_parent'
        verbose_name = _('Disaggregation Category')
        verbose_name_plural = _('  Disaggregation Categories')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #ddisplay disagregation Categories


class StgCategoryoption(TranslatableModel):
    categoryoption_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(unique=True,max_length=36, blank=False,
        null=False,default=uuid.uuid4,editable=False, verbose_name =_('Unique ID'))
    category = models.ForeignKey(StgCategoryParent, models.PROTECT,
        verbose_name = _('Category Name'))
    translations = TranslatedFields(
        name = models.CharField(max_length=230, blank=False, null=False,
            verbose_name = _('Modality Name')),
        shortname = models.CharField(max_length=50, blank=True, null=True,
            verbose_name = _('Short Name')),
        description = models.TextField(blank=True, null=True)
    )
    code = models.CharField(unique=True,max_length=50, blank=True, null=False)
    date_created = models.DateTimeField(blank=True, null=True, auto_now_add=True,
        verbose_name = 'Date Created')
    date_lastupdated = models.DateTimeField(blank=True, null=True, auto_now=True,
        verbose_name = 'Date Modified')

    class Meta:
        managed = True
        db_table = 'stg_categoryoption'
        verbose_name = _('Disaggregation Option')
        verbose_name_plural = _('   Disaggregation Options')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #ddisplay disagregation options

class StgDatasource(TranslatableModel):
    LEVEL_CHOICES = ( #choices for approval of indicator data by authorized users
        ('global', _('Global')),
        ('regional',_('Regional')),
        ('national',_('National')),
        ('sub-national',_('Sub-national')),
        ('unspecified',_('Non-specific'))
    )
    datasource_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(unique=True,max_length=36, blank=False,
        null=False,default=uuid.uuid4,editable=False, verbose_name = 'Unique ID')
    translations = TranslatedFields(
        name = models.CharField(max_length=230, blank=False, null=False,
            verbose_name =_('Data Source')),  # Field name made lowercase.
        shortname = models.CharField(max_length=50, blank=True, null=True,
            verbose_name = _('Short Name')),  # Field name made lowercase.
        level = models.CharField(max_length=20,blank=False, null=False,
            choices= LEVEL_CHOICES,verbose_name =_('Source Level'),
            default=LEVEL_CHOICES[2][0],
            help_text=_("Level can be global, regional, national, subnational")),
        description = models.TextField( blank=False, null=False,
            default=_('No definition'))
    )
    code = models.CharField(unique=True, max_length=50, blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True, auto_now_add=True,
        verbose_name = _('Date Created'))
    date_lastupdated = models.DateTimeField(blank=True, null=True, auto_now=True,
        verbose_name = _('Date Modified'))

    class Meta:
        managed = True
        db_table = 'stg_datasource'
        verbose_name = _('Data Source')
        verbose_name_plural = _('    Data Sources')
        ordering = ('translations__name',)

    def __str__(self):
        try: 
            return self.name # return string rep for the object
        except TranslationDoesNotExist: 
            return '' # return empty string

    def clean(self): # Don't allow end_period to be greater than the start_period.
        if StgDatasource.objects.filter(
            translations__name=self.name).count() and not self.datasource_id:
            raise ValidationError({'name':_('Sorry! This data source exists')})


class StgValueDatatype(TranslatableModel):
    valuetype_id = models.AutoField(primary_key=True)  # Field name made lowercase.
    uuid = uuid = models.CharField(unique=True,max_length=36, blank=False,
        null=False,default=uuid.uuid4,editable=False,verbose_name=_('Unique ID'))
    translations = TranslatedFields(
        name = models.CharField(max_length=50, verbose_name =_('Value Name')),
        shortname = models.CharField(max_length=50, blank=True, null=True,
            verbose_name =_('Short Name')),
        description = models.TextField(blank=True, null=True)
    )
    code = models.CharField(unique=True, max_length=50)
    date_created = models.DateTimeField(blank=True, null=True, auto_now_add=True,
        verbose_name = _('Date Created'))
    date_lastupdated = models.DateTimeField(blank=True, null=True, auto_now=True,
        verbose_name = _('Date Modified'))

    class Meta:
         managed = True
         db_table = 'stg_value_datatype'
         verbose_name = _(' Data Value')
         verbose_name_plural = _('Data Value Types')
         ordering = ('translations__name',)

    def __str__(self):
         return self.name #ddisplay disagregation options


class StgMeasuremethod(TranslatableModel):
    measuremethod_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False, null=False,default=uuid.uuid4,editable=False)
    translations = TranslatedFields(
        name = models.CharField(_('Measure Name'),max_length=230, blank=False,
            null=False,help_text=_("Name can be indicator types like unit, \
            Percentage, Per Thousand, Per Ten Thousand,Per Hundred Thousand etc")),
        measure_value = models.DecimalField(_('Ratio'),max_digits=50,
            decimal_places=0,blank=True, null=True,help_text=_("Ratio can be \
            factors like 1 for unit, 100, 1000,10000 or higher values")),
        description = models.TextField(_('Description'),max_length=200,
        blank=True, null=True)
    )
    code = models.CharField(max_length=50,unique=True, blank=True, null=False)
    date_created = models.DateTimeField(blank=True, null=True, auto_now_add=True,
        verbose_name = _('Date Created'))
    date_lastupdated = models.DateTimeField(blank=True, null=True, auto_now=True,
        verbose_name = _('Date Modified'))

    class Meta:
        managed = True
        db_table = 'stg_measuremethod'
        verbose_name = _('Measure Type')
        verbose_name_plural = _(' Measure Types')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #ddisplay measurement methods


"""
These model classes inherits from data_wizard sources package.The purpose of
inheriting the models is to add location field to the sources database tables
"""
class FileSource(Filesources):
    location = models.ForeignKey(StgLocation, models.PROTECT, blank=False,
        verbose_name=_('Location Name'),)
    url = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = True
        verbose_name = _('Import File')
        verbose_name_plural = _('Import via File..')
        ordering = ('location',)

    def get_fileurl(self):
        base_url = f'https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER}/'
        file_name = self.file.name
        if self.url is None or self.url == '':
            return (base_url + 'datawizard/' + file_name)
        return (base_url + 'datawizard/' + file_name)

    def save(self, *args, **kwargs):
        self.url = self.get_fileurl()
        super(FileSource, self).save(*args, **kwargs)

    def __str__(self):
        return self.name or self.file.name


class URLSource(URLsources):
    location = models.ForeignKey(StgLocation, models.PROTECT, blank=False,
        verbose_name=_('Location Name'),)
    file = models.ForeignKey(FileSource, on_delete=models.CASCADE,
        related_name="link", verbose_name=_('File'))

    class Meta:
        managed = True
        verbose_name = _('URL')
        verbose_name_plural = _('Import via URL..')
        ordering = ('location',)

    def get_url(self):
        if self.url is None or self.url == '':
            return self.file.url
        return self.file.url

    def save(self, *args, **kwargs):
        self.url = self.get_url()
        return super(URLSource, self).save(*args, **kwargs)

    def __str__(self):
        return self.name or self.url


class DataIntegrationConnection(models.Model):
    PROVIDER_DHIS2 = 'dhis2'
    PROVIDER_DATABANK = 'databank'
    PROVIDER_WHO_DATAHUB = 'who_datahub'
    PROVIDER_AHO_WAREHOUSE = 'aho_warehouse'
    PROVIDER_CUSTOM = 'custom'

    METHOD_DIRECT = 'direct'
    METHOD_API = 'api'

    STATUS_DRAFT = 'draft'
    STATUS_ACTIVE = 'active'
    STATUS_PAUSED = 'paused'
    STATUS_ERROR = 'error'

    SSL_MODE_DISABLED = 'disabled'
    SSL_MODE_REQUIRED = 'required'
    SSL_MODE_VERIFY_IDENTITY = 'verify_identity'

    PROVIDER_CHOICES = (
        (PROVIDER_DHIS2, _('DHIS2')),
        (PROVIDER_DATABANK, _('DataBank')),
        (PROVIDER_WHO_DATAHUB, _('WHO DataHub')),
        (PROVIDER_AHO_WAREHOUSE, _('AHO Warehouse')),
        (PROVIDER_CUSTOM, _('Custom')),
    )
    METHOD_CHOICES = (
        (METHOD_DIRECT, _('Direct database')),
        (METHOD_API, _('API')),
    )
    STATUS_CHOICES = (
        (STATUS_DRAFT, _('Draft')),
        (STATUS_ACTIVE, _('Active')),
        (STATUS_PAUSED, _('Paused')),
        (STATUS_ERROR, _('Error')),
    )
    SYNC_FREQUENCY_CHOICES = (
        ('manual', _('Manual')),
        ('hourly', _('Hourly')),
        ('daily', _('Daily')),
        ('weekly', _('Weekly')),
        ('monthly', _('Monthly')),
    )
    AUTH_TYPE_CHOICES = (
        ('none', _('None')),
        ('bearer', _('Bearer token')),
        ('api_key', _('API key')),
        ('basic', _('Basic authentication')),
        ('oauth2', _('OAuth2')),
    )
    DATABASE_DRIVER_CHOICES = (
        ('mysql', _('MySQL / MariaDB')),
        ('pgsql', _('PostgreSQL')),
        ('sqlsrv', _('SQL Server')),
        ('oracle', _('Oracle')),
        ('sqlite', _('SQLite')),
        ('odbc', _('ODBC')),
        ('other', _('Other')),
    )
    SSL_MODE_CHOICES = (
        (SSL_MODE_DISABLED, _('Disabled')),
        (SSL_MODE_REQUIRED, _('Required')),
        (SSL_MODE_VERIFY_IDENTITY, _('Verify identity')),
    )

    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    user = models.ForeignKey(CustomUser, models.SET_NULL, blank=True, null=True)
    location = models.ForeignKey(StgLocation, models.SET_NULL, blank=True, null=True)
    name = models.CharField(_('Name'), max_length=255)
    provider = models.CharField(_('Provider'), max_length=50, choices=PROVIDER_CHOICES, default=PROVIDER_DHIS2)
    integration_method = models.CharField(_('Integration method'), max_length=50, choices=METHOD_CHOICES, default=METHOD_API)
    status = models.CharField(_('Status'), max_length=50, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    sync_frequency = models.CharField(_('Sync frequency'), max_length=50, choices=SYNC_FREQUENCY_CHOICES, default='manual')
    server_name = models.CharField(_('Server name'), max_length=255, blank=True, null=True)
    port = models.PositiveIntegerField(_('Port'), blank=True, null=True)
    database_driver = models.CharField(_('Database driver'), max_length=50, choices=DATABASE_DRIVER_CHOICES, blank=True, null=True)
    database_name = models.CharField(_('Database name'), max_length=255, blank=True, null=True)
    source_table = models.CharField(_('Source table'), max_length=255, blank=True, null=True)
    username = models.CharField(_('Username'), max_length=255, blank=True, null=True)
    password = models.TextField(_('Password'), blank=True, null=True)
    api_url = models.URLField(_('API URL'), max_length=255, blank=True, null=True)
    auth_type = models.CharField(_('Authentication type'), max_length=50, choices=AUTH_TYPE_CHOICES, default='none')
    api_token = models.TextField(_('API token'), blank=True, null=True)
    api_key_name = models.CharField(_('API key name'), max_length=255, blank=True, null=True)
    api_key_value = models.TextField(_('API key value'), blank=True, null=True)
    client_id = models.CharField(_('Client ID'), max_length=255, blank=True, null=True)
    client_secret = models.TextField(_('Client secret'), blank=True, null=True)
    data_scope = models.JSONField(_('Data scope'), blank=True, null=True)
    field_mapping = models.JSONField(_('Field mapping'), blank=True, null=True)
    ssl_mode = models.CharField(_('SSL mode'), max_length=50, choices=SSL_MODE_CHOICES, default=SSL_MODE_DISABLED)
    ssl_ca_path = models.TextField(_('SSL CA path'), blank=True, null=True)
    ssl_certificate_path = models.TextField(_('SSL certificate path'), blank=True, null=True)
    ssl_key_path = models.TextField(_('SSL key path'), blank=True, null=True)
    ssl_cipher = models.CharField(_('SSL cipher'), max_length=255, blank=True, null=True)
    connection_timeout = models.PositiveSmallIntegerField(_('Connection timeout'), default=15)
    last_synced_at = models.DateTimeField(_('Last synced at'), blank=True, null=True)
    last_tested_at = models.DateTimeField(_('Last tested at'), blank=True, null=True)
    last_test_status = models.CharField(_('Last test status'), max_length=50, blank=True, null=True)
    last_test_message = models.TextField(_('Last test message'), blank=True, null=True)
    notes = models.TextField(_('Notes'), blank=True, null=True)
    created_at = models.DateTimeField(_('Date Created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Date Modified'), auto_now=True)

    class Meta:
        managed = True
        db_table = 'data_integration_connections'
        verbose_name = _('Data integration connection')
        verbose_name_plural = _('Data integration connections')
        ordering = ('-updated_at', '-created_at')
        indexes = (
            models.Index(fields=('provider', 'integration_method'), name='dic_provider_method_idx'),
            models.Index(fields=('status', 'sync_frequency'), name='dic_status_sync_idx'),
        )

    def __str__(self):
        return self.name

    @staticmethod
    def requires_direct_connection_password(server_name):
        server_name = re.sub(r'^\[|\]$', '', str(server_name or '').strip().lower())
        return server_name not in ('localhost', '127.0.0.1', '::1')

    def has_configured_field_mappings(self):
        if self.field_mappings.exists():
            return True
        if isinstance(self.field_mapping, dict):
            return any(str(key).strip() and str(value).strip() for key, value in self.field_mapping.items())
        return False

    def missing_configuration_fields(self):
        missing = []
        if self.integration_method == self.METHOD_DIRECT:
            direct_fields = (
                ('server_name', _('Server name')),
                ('database_driver', _('Database driver')),
                ('database_name', _('Database name')),
                ('username', _('Username')),
            )
            if self.requires_direct_connection_password(self.server_name):
                direct_fields += (('password', _('Password')),)
            missing.extend(label for field, label in direct_fields if not getattr(self, field))

        if self.integration_method == self.METHOD_API:
            if not self.api_url:
                missing.append(_('API URL'))
            auth_fields = {
                'bearer': (('api_token', _('API token')),),
                'api_key': (('api_key_name', _('API key name')), ('api_key_value', _('API key value'))),
                'basic': (('username', _('Username')), ('password', _('Password'))),
                'oauth2': (('client_id', _('Client ID')), ('client_secret', _('Client secret'))),
            }
            missing.extend(label for field, label in auth_fields.get(self.auth_type, ()) if not getattr(self, field))

        return missing

    def validate_configuration(self):
        missing = self.missing_configuration_fields()
        if missing:
            return {
                'ok': False,
                'status': 'missing',
                'message': _('Missing required fields: %(fields)s') % {'fields': ', '.join(str(item) for item in missing)},
            }

        direct_result = None
        if self.integration_method == self.METHOD_DIRECT:
            direct_result = self._validate_direct_connection()
            if not direct_result['ok']:
                return direct_result

        if not self.has_configured_field_mappings():
            return {
                'ok': False,
                'status': 'missing',
                'message': _('Missing required fields: %(fields)s') % {'fields': _('Field mapping')},
            }

        if self.provider == self.PROVIDER_DHIS2 and self.integration_method == self.METHOD_API:
            return self._validate_dhis2_api_connection()

        if direct_result is not None:
            return direct_result

        return {'ok': True, 'status': 'ready', 'message': _('Configuration is ready.')}

    def _validate_direct_connection(self):
        if self.database_driver != 'mysql':
            return {'ok': True, 'status': 'ready', 'message': _('Direct connection settings are complete.')}

        try:
            import pymysql

            options = {
                'host': self.server_name,
                'user': self.username,
                'password': self.password or '',
                'database': self.database_name,
                'port': int(self.port or 3306),
                'connect_timeout': min(120, max(1, int(self.connection_timeout or 15))),
            }
            if self.ssl_mode != self.SSL_MODE_DISABLED:
                options['ssl'] = {'ca': self.ssl_ca_path} if self.ssl_ca_path else {}
            conn = pymysql.connect(**options)
            try:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT 1')
            finally:
                conn.close()
        except Exception as exc:
            return {
                'ok': False,
                'status': 'missing',
                'message': _('Connection failed: %(message)s') % {'message': str(exc)},
            }
        return {'ok': True, 'status': 'ready', 'message': _('Direct database connection succeeded.')}

    def _validate_dhis2_api_connection(self):
        try:
            payload = self._request_json(self._dhis2_endpoint('system/info'))
        except (URLError, TimeoutError, ValueError, OSError) as exc:
            return {
                'ok': False,
                'status': 'missing',
                'message': _('DHIS2 API connection failed: %(message)s') % {'message': str(exc)},
            }
        system = payload.get('systemName') or 'DHIS2'
        version = payload.get('version') or _('unknown version')
        return {'ok': True, 'status': 'ready', 'message': _('Connected to %(system)s (%(version)s).') % {'system': system, 'version': version}}

    def external_fields(self):
        if self.integration_method == self.METHOD_DIRECT:
            return self._direct_external_fields()
        if self.provider == self.PROVIDER_DHIS2:
            return sorted(set(self.known_dhis2_data_value_fields()))
        return self._api_external_fields()

    def _direct_external_fields(self):
        if self.database_driver != 'mysql' or not self.source_table:
            return []
        try:
            import pymysql

            conn = pymysql.connect(
                host=self.server_name,
                user=self.username,
                password=self.password or '',
                database=self.database_name,
                port=int(self.port or 3306),
                connect_timeout=min(120, max(1, int(self.connection_timeout or 15))),
            )
            try:
                with conn.cursor() as cursor:
                    cursor.execute('SHOW COLUMNS FROM `{}`'.format(str(self.source_table).replace('`', '')))
                    return sorted(row[0] for row in cursor.fetchall())
            finally:
                conn.close()
        except Exception:
            return []

    def _api_external_fields(self):
        if not self.api_url:
            return []
        try:
            payload = self._request_json(self.api_url)
        except (URLError, TimeoutError, ValueError, OSError):
            return []
        return sorted(set(self._extract_field_paths(payload)))

    @staticmethod
    def known_dhis2_data_value_fields():
        return [
            'dataElement',
            'dataElement.code',
            'dataElement.id',
            'dataElement.name',
            'period',
            'orgUnit',
            'orgUnit.code',
            'orgUnit.id',
            'orgUnit.name',
            'categoryOptionCombo',
            'attributeOptionCombo',
            'value',
            'comment',
            'storedBy',
            'created',
            'lastUpdated',
            'followUp',
        ]

    def _request_json(self, url):
        request = Request(url, headers={'Accept': 'application/json'})
        if self.auth_type == 'basic' and self.username and self.password:
            token = base64.b64encode(f'{self.username}:{self.password}'.encode()).decode()
            request.add_header('Authorization', f'Basic {token}')
        elif self.auth_type == 'bearer' and self.api_token:
            request.add_header('Authorization', f'Bearer {self.api_token}')
        elif self.auth_type == 'api_key' and self.api_key_name and self.api_key_value:
            request.add_header(str(self.api_key_name), str(self.api_key_value))

        with urlopen(request, timeout=min(120, max(1, int(self.connection_timeout or 20)))) as response:
            return json.loads(response.read().decode('utf-8') or '{}')

    def _dhis2_endpoint(self, path):
        base_url = str(self.api_url or '').rstrip('/')
        api_base = base_url if base_url.endswith('/api') else base_url + '/api'
        return api_base + '/' + path.lstrip('/')

    @classmethod
    def _extract_field_paths(cls, payload, prefix='', depth=0):
        if depth > 6:
            return []
        if isinstance(payload, list):
            fields = []
            for item in payload[:10]:
                fields.extend(cls._extract_field_paths(item, prefix, depth + 1))
            return fields
        if not isinstance(payload, dict):
            return []

        fields = []
        for key, value in payload.items():
            if str(key).startswith('_') or str(key).isdigit():
                continue
            path = f'{prefix}.{key}' if prefix else str(key)
            fields.append(path)
            if isinstance(value, (dict, list)):
                fields.extend(cls._extract_field_paths(value, path, depth + 1))
        return fields[:250]

class DataIntegrationFieldMapping(models.Model):
    FIELD_TYPE_CHOICES = (
        ('direct', _('Direct')),
        ('lookup', _('Lookup')),
        ('computed', _('Computed')),
        ('conditional', _('Conditional')),
        ('skip', _('Skip')),
    )
    REFERENCE_MATCH_CHOICES = (
        ('auto', _('Auto')),
        ('code', _('Code')),
        ('name', _('Name')),
        ('id', _('ID')),
    )
    REFERENCE_FIELDS = (
        'location_id',
        'indicator_id',
        'categoryoption_id',
        'datasource_id',
        'measuremethod_id',
    )
    LOCAL_FIELD_CHOICES = (
        ('location_id', _('Location')),
        ('indicator_id', _('Indicator')),
        ('start_period', _('Start period')),
        ('end_period', _('End period')),
        ('period', _('Period')),
        ('categoryoption_id', _('Category option')),
        ('datasource_id', _('Data source')),
        ('measuremethod_id', _('Measure method')),
        ('value_received', _('Value received')),
        ('numerator_value', _('Numerator')),
        ('denominator_value', _('Denominator')),
        ('min_value', _('Min')),
        ('max_value', _('Max')),
        ('target_value', _('Target')),
        ('string_value', _('Text value')),
        ('comment', _('Approval status')),
        ('priority', _('Priority')),
    )

    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    connection = models.ForeignKey(
        DataIntegrationConnection,
        models.CASCADE,
        related_name='field_mappings',
        db_column='data_integration_connection_id',
    )
    local_field = models.CharField(_('Local field'), max_length=255, choices=LOCAL_FIELD_CHOICES)
    external_field = models.CharField(_('External field'), max_length=255)
    field_type = models.CharField(_('Field type'), max_length=50, choices=FIELD_TYPE_CHOICES, default='direct')
    transformation_config = models.JSONField(_('Transformation config'), blank=True, null=True)
    is_required = models.BooleanField(_('Required'), default=False)
    notes = models.TextField(_('Notes'), blank=True, null=True)
    sort_order = models.IntegerField(_('Sort order'), default=0)
    created_at = models.DateTimeField(_('Date Created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Date Modified'), auto_now=True)

    class Meta:
        managed = True
        db_table = 'data_integration_field_mappings'
        verbose_name = _('Data integration field mapping')
        verbose_name_plural = _('Data integration field mappings')
        ordering = ('sort_order', 'id')
        constraints = (
            models.UniqueConstraint(fields=('connection', 'local_field'), name='difm_connection_local_unique'),
        )
        indexes = (
            models.Index(fields=('connection', 'field_type'), name='difm_connection_type_idx'),
        )

    def __str__(self):
        return f'{self.local_field} -> {self.external_field}'

    @classmethod
    def is_reference_field(cls, field):
        return field in cls.REFERENCE_FIELDS

    @classmethod
    def suggest_mappings(cls, external_fields):
        aliases = {
            'location_id': ['countrycode', 'locationcode', 'orgunitcode', 'isoalpha', 'iso2', 'iso3', 'locationid', 'orgunitid', 'country', 'countryname', 'location', 'locationname', 'orgunit', 'orgunitname'],
            'indicator_id': ['indicatorcode', 'afrocode', 'indicatorid', 'dataelementcode', 'dataelementid', 'indicator', 'indicatorname', 'dataelement', 'dataelementname'],
            'categoryoption_id': ['categoryoptioncode', 'categoryoptionid', 'categoryoption', 'categoryoptionname', 'disaggregation', 'disaggregationoption'],
            'datasource_id': ['datasourcecode', 'sourcecode', 'datasourceid', 'sourceid', 'datasource', 'datasourcename', 'source', 'sourcename'],
            'measuremethod_id': ['measuremethodcode', 'measuretypecode', 'measuremethodid', 'measuretypeid', 'measuremethod', 'measuremethodname', 'measuretype', 'measuretypename'],
            'start_period': ['startperiod', 'startyear', 'yearstart'],
            'end_period': ['endperiod', 'endyear', 'yearend'],
            'period': ['period', 'year', 'dateperiod'],
            'value_received': ['valuereceived', 'indicatorvalue', 'numericvalue', 'value'],
            'numerator_value': ['numeratorvalue', 'numerator'],
            'denominator_value': ['denominatorvalue', 'denominator'],
            'min_value': ['minvalue', 'minimumvalue', 'minimum'],
            'max_value': ['maxvalue', 'maximumvalue', 'maximum'],
            'target_value': ['targetvalue', 'target'],
            'string_value': ['stringvalue', 'textvalue', 'text'],
            'comment': ['comment', 'comments', 'remark', 'remarks', 'status'],
            'priority': ['priority'],
        }
        normalized_fields = {cls.normalize_identifier(field): field for field in external_fields}
        used = set()
        mappings = []
        for local_field, candidates in aliases.items():
            external_field = next(
                (normalized_fields[candidate] for candidate in candidates if normalized_fields.get(candidate) and normalized_fields[candidate] not in used),
                None,
            )
            if not external_field:
                continue
            used.add(external_field)
            is_reference = cls.is_reference_field(local_field)
            mappings.append({
                'local_field': local_field,
                'external_field': external_field,
                'field_type': 'lookup' if is_reference else 'direct',
                'reference_match': cls.infer_reference_match(external_field) if is_reference else '',
                'is_required': local_field in ('location_id', 'indicator_id', 'period', 'value_received'),
                'default_value': '',
                'transformation_rule': '',
                'notes': '',
            })
        return mappings

    @classmethod
    def infer_reference_match(cls, external_field):
        field = cls.normalize_identifier(external_field)
        if 'code' in field or 'afro' in field or field.startswith('iso'):
            return 'code'
        return 'id' if field.endswith('id') else 'name'

    @staticmethod
    def normalize_identifier(value):
        return re.sub(r'[^a-z0-9]+', '', str(value or '').lower())
