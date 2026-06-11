from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import pre_save,post_save
import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.fields import DecimalField
from django.core.exceptions import ValidationError
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields
from home.models import (StgDatasource,StgCategoryoption,StgMeasuremethod,
    StgValueDatatype)
from regions.models import StgLocation
from authentication.models import CustomUser

# These are global codes reusable in most models that require choice fiels
def make_choices(values):
    return [(v, v) for v in values]

def current_year():
    return datetime.date.today().year

def max_value_current_year(value):
    return MaxValueValidator(current_year())(value)

STATUS_CHOICES = ( #choices for approval of indicator data by authorized users
    ('pending', _('Pending')),
    ('approved',_('Approved')),
    ('rejected',_('Rejected')),
)

class StgIndicatorReference(TranslatableModel):
    reference_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False, null=False,default=uuid.uuid4,editable=False)
    translations = TranslatedFields(
        name = models.CharField(_("Reference Name"),max_length=230, blank=False,
            null=False,default=_("Global List of 100 Core Health Indicators")),
        shortname = models.CharField(_('Short Name'),max_length=50,
            blank=True, null=True),
        description = models.TextField(_('Brief Description'),blank=True,null=True)
    )
    code = models.CharField(unique=True, max_length=50, blank=True,null=True)
    date_created = models.DateTimeField(_('Date Created'),blank=True,null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True,auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_indicator_reference'
        verbose_name = _('Indicator Reference')
        verbose_name_plural = _('Indicator References')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the data source name

    # The filter function need to be modified to work with django parler as follows:
    def clean(self): # Don't allow end_period to be greater than the start_period.
        if StgIndicatorReference.objects.filter(
            translations__name=self.name).count() and not self.reference_id:
            raise ValidationError({'name':_('Sorry! This indicator reference exists')})

    def save(self, *args, **kwargs):
        super(StgIndicatorReference, self).save(*args, **kwargs)

class StgIndicator(TranslatableModel):
    indicator_id = models.AutoField(primary_key=True)  # Field name made lowercase.
    uuid =models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False, null=False,default=uuid.uuid4,editable=False)
    translations = TranslatedFields(any_language=True,
        name = models.CharField(_('Indicator Name'),max_length=500,
            blank=False, null=False),
        shortname = models.CharField(_('Short Name'),unique=True,max_length=120,
            blank=False,null=True),
        definition = models.TextField(_('Indicator Definition'),blank=False,
            null=True,),  # Field name made lowercase.
        preferred_datasources = models.CharField(_('Primary Sources'),
            max_length=5000,blank=True, null=True,),
        numerator_description = models.TextField(_('Numerator Description'),
            blank=True,null=True,),
        denominator_description = models.TextField(_('Denominator Description'),
            blank=True,null=True)
    )
    afrocode = models.CharField(_('Indicator Code'),max_length=10,blank=True,
        null=False,unique=True)  # Field name made lowercase.
    gen_code = models.CharField(_('Standard Code'),max_length=10,blank=True,
        null=True,unique=True,)  # Field name made lowercase.
    reference = models.ForeignKey(StgIndicatorReference, models.PROTECT,
        default=1, verbose_name =_('Indicator Reference'))
    date_created = models.DateTimeField(_('Date Created'),blank=True,null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_indicator'
        verbose_name = _('Indicator')
        verbose_name_plural = _('  Indicators')
        ordering = ('translations__name',)

    """
    This method makes it possible to enter multi-records in the Tabular form
    without returning the language code error! resolved on 10th August 2020
    """
    def __str__(self):
        language_code = (translation.get_language() or settings.LANGUAGE_CODE).split("-", 1)[0]
        return self.safe_translation_getter(
            'name', any_language=True, language_code=language_code)

    # The filter function need to be modified to work with django parler as follows:
    def clean(self): # Don't allow end_period to be greater than the start_period.
        if StgIndicator.objects.filter(
            translations__name=self.name).count() and not self.indicator_id:
            raise ValidationError(
                {'name':_('Sorry! Indicator with this name exists')})

    def save(self, *args, **kwargs):
        super(StgIndicator, self).save(*args, **kwargs)


class StgIndicatorDomain(TranslatableModel):
    LEVEL = (
    (1,_('level 1')),
    (2,_('level 2')),
    (3,_('level 3')),
    (4,_('level 4')),
    (5,_('level 5')),
    (6,_('level 6')),
    )
    domain_id = models.AutoField(primary_key=True)  # Field name made lowercase.
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False, null=False,default=uuid.uuid4,editable=False)
    translations = TranslatedFields(
        name = models.CharField(_('Theme'),max_length=150, blank=False,
        null=False),
        shortname = models.CharField(_('Short Name'),max_length=45,blank=False,
            null=False),
        description = models.TextField(_('Brief Description'),blank=True,null=True,)
    )
    level =models.SmallIntegerField(_('Theme Level'),choices=LEVEL,
        default=LEVEL[0][0])
    code = models.CharField(unique=True, max_length=45, blank=True,
        null=True,verbose_name = _('Code'))
    parent = models.ForeignKey('self', models.PROTECT, blank=True, null=True,
        verbose_name = _('Parent Theme'))  # Field name made lowercase.
    # this field establishes a many-to-many relationship with the domain table
    indicators = models.ManyToManyField(StgIndicator,
        db_table='stg_indicator_domain_members',blank=True,
        verbose_name = _('Indicators'))  # Field name made lowercase.
    date_created = models.DateTimeField(_('Date Created'),blank=True,null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_indicator_domain'
        verbose_name = _('Indicator Theme')
        verbose_name_plural = _(' Indicator Themes')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #ddisplay disagregation options

    # The filter function need to be modified to work with django parler as follows:
    def clean(self): # Don't allow end_period to be greater than the start_period.
        if StgIndicatorDomain.objects.filter(
            translations__name=self.name).count() and not self.domain_id:
            raise ValidationError({'name':_('Sorry! This indicators theme exists')})

    def save(self, *args, **kwargs):
        super(StgIndicatorDomain, self).save(*args, **kwargs)


class FactDataIndicator(models.Model):
  # discriminator for ownership of data this was decided on 13/12/2019 with Gift
    fact_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False, null=False,default=uuid.uuid4,editable=False)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name='User Name (Email)') # request helper field
    indicator = models.ForeignKey(StgIndicator, models.PROTECT,
        verbose_name = _('Indicator Name'))
    location = models.ForeignKey(StgLocation, models.PROTECT,blank=False,
        verbose_name = _('Location Name'),)
    categoryoption = models.ForeignKey(StgCategoryoption, models.PROTECT,
        blank=False,verbose_name =_('Disaggregation Options'))
    # This field is used to lookup data sources e.g. routine, census and surveys
    datasource = models.ForeignKey(StgDatasource, models.PROTECT,
        verbose_name = _('Data Source'))
    # This field is used to lookup the type of data required e.g.text, integer or float
    measuremethod = models.ForeignKey(StgMeasuremethod,models.PROTECT,
        blank=False,verbose_name =_('Measure Type'))
    numerator_value = models.DecimalField(_('Numerator Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    denominator_value = models.DecimalField(_('Denominator Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    value_received = DecimalField(_('Numeric Value'),max_digits=20,
        decimal_places=3,blank=True,null=True)
    min_value = models.DecimalField(_('Minimum Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    max_value = models.DecimalField(_('Maximum Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    target_value = models.DecimalField(_('Target Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    string_value= models.CharField(_('String Value'),max_length=500,blank=True,
        null=True) # davy's request as of 30/4/2019
    start_period = models.PositiveIntegerField(_('Starting period'),null=False,
        blank=False,validators=[MinValueValidator(1900),max_value_current_year],
        default=current_year(),
        help_text=_("This marks the start of reporting period"))
    end_period=models.PositiveIntegerField(_('Ending Period'),null=False,
        blank=False,validators=[MinValueValidator(1900),max_value_current_year],
        default=current_year(),
        help_text=_("This marks the end of reporting. The value must be current \
            year or greater than the start year"))
    period = models.CharField(_('Period'),max_length=25,blank=True,null=False)
    comment = models.CharField(_('Status'),max_length=10, choices= STATUS_CHOICES,
        default=STATUS_CHOICES[0][0])  # Field name made lowercase.
    priority = models.BooleanField(default=False,verbose_name=_('Dashboard Priority?'))
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        permissions = (
            ("approve_factdataindicator","Can approve Indicator Data"),
            ("reject_factdataindicator","Can reject Indicator Data"),
            ("pend_factdataindicator","Can pend Indicator Data")
        )

        managed = True
        unique_together = ('indicator', 'location', 'categoryoption','datasource',
            'start_period','end_period') #enforces concatenated unique constraint
        db_table = 'fact_data_indicators'
        verbose_name = _('Indicator Data Record')
        verbose_name_plural = _('    Single-record Form')
        ordering = ('indicator__translations__name',)

    def __str__(self):
         return str(self.indicator)

    """
    The purpose of this method is to compare the start_period to the end_period. If the
    start_period is greater than the end_period athe model should show an inlines error
    message and wait until the user corrects the mistake.
    """
    def clean(self): # Don't allow end_period to be greater than the start_period.
        if self.start_period <1900 or self.start_period > datetime.date.today().year:
            raise ValidationError({'start_period':_(
                'Sorry! Start year cannot be less than 1900 or greater than current Year ')})
        elif self.end_period <1900 or self.end_period > datetime.date.today().year:
            raise ValidationError({'end_period':_(
                'Sorry! The ending year cannot be lower than the start year or \
                greater than the current Year ')})
        elif self.end_period < self.start_period and self.start_period is not None:
            raise ValidationError({'end_period':_(
                'Sorry! Ending period cannot be lower than the start period. \
                 Please make corrections')})

        #This logic ensures that a maximum value is provided for a corresponing minimum value
        if self.min_value is not None and self.min_value !='':
            if self.max_value is None or self.max_value < self.min_value:
                raise ValidationError({'max_value':_(
                    'Data Integrity Problem! You must provide a Maximum that is \
                     greater that Minimum value ')})
            elif self.value_received is not None and self.value_received <=self.min_value:
                raise ValidationError({'min_value':_(
                    'Data Integrity Problem! Minimum value cannot be greater \
                     that the nominal value')})

        if self.value_received is None and self.string_value is None:
            raise ValidationError({'value_received':_(
                'Data Entry Problem! Both numeric and string values cannot\
                 be empty. Please supply data to both or either!')})

    """
    The purpose of this method is to concatenate the date that are entered as
    start_period and end_period and save the concatenated value as a string in
    the database ---this is very important to take care of Davy's date complexity
    """
    def get_period(self):
        if self.period is None or (self.start_period and self.end_period):
            if self.start_period == self.end_period:
                period = int(self.start_period)
            else:
                period =str(int(self.start_period))+"-"+ str(int(self.end_period))
        return period

    """
    This method overrides the save method to store the derived field into database.
    Note that the last line calls the super class FactDataIndicator to save the value
    """
    def save(self, *args, **kwargs):
        self.period = self.get_period()
        super(FactDataIndicator, self).save(*args, **kwargs)


# These proxy classes are used to register menu in the admin for tabular entry
class IndicatorProxy(StgIndicator):
    """
    Creates permissions for proxy models which are not created automatically by
    'django.contrib.auth.management.create_permissions'.Since we can't rely on
    'get_for_model' we must fallback to  'get_by_natural_key'. However, this
    method doesn't automatically create missing 'ContentType' so we must ensure
    all the models' 'ContentType's are created before running this method.
    We do so by unregistering the 'update_contenttypes' 'post_migrate' signal
    and calling it in here just before doing everything.
    """
    def create_proxy_permissions(app, created_models, verbosity, **kwargs):
        update_contenttypes(app, created_models, verbosity, **kwargs)
        app_models = models.get_models(app)
        # The permissions we're looking for as (content_type, (codename, name))
        searched_perms = list()
        # The codenames and ctypes that should exist.
        ctypes = set()
        for model in app_models:
            opts = model._meta
            if opts.proxy:
                # Can't use 'get_for_model' here since it doesn't return correct
                # 'ContentType' for proxy models
                app_label, model = opts.app_label, opts.object_name.lower()
                ctype = ContentType.objects.get_by_natural_key(app_label, model)
                ctypes.add(ctype)
                for perm in _get_all_permissions(opts, ctype):
                    searched_perms.append((ctype, perm))

        # Find all the Permissions that have content_type for the target model
        # We don't need to check for codenames; we have list of ones to crerate
        all_perms = set(Permission.objects.filter(
            content_type__in=ctypes,
        ).values_list(
            "content_type", "codename"
        ))

        objs = [
            Permission(codename=codename, name=name, content_type=ctype)
            for ctype, (codename, name) in searched_perms
            if (ctype.pk, codename) not in all_perms
        ]
        Permission.objects.bulk_create(objs)
        if verbosity >= 2:
            for obj in objs:
                sys.stdout.write("Adding permission '%s'" % obj)
        models.signals.post_migrate.connect(create_proxy_permissions)
        models.signals.post_migrate.disconnect(update_contenttypes)

    class Meta:
        proxy = True
        managed = False
        verbose_name = _('Data Form')
        verbose_name_plural = _('   Multi-records Grid')

    """
    This def clean (self) method was contributed by Daniel Mbugua to resolve
    the issue of parent-child saving issue in the multi-records entry form.
    My credits to Mr Mbugua of MSc DCT, UoN-Kenya
    """
    def clean(self): #Appreciation to Daniel M.
        pass


# These proxy classes are used to register menu in the admin for tabular entry
class NHOCustomizationProxy(StgLocation):
    def create_proxy_permissions(app, created_models, verbosity, **kwargs):
        update_contenttypes(app, created_models, verbosity, **kwargs)
        app_models = models.get_models(app)
        # The permissions we're looking for as (content_type, (codename, name))
        searched_perms = list()
        # The codenames and ctypes that should exist.
        ctypes = set()
        for model in app_models:
            opts = model._meta
            if opts.proxy:
                # Can't use 'get_for_model' here since it doesn't return correct
                # 'ContentType' for proxy models
                app_label, model = opts.app_label, opts.object_name.lower()
                ctype = ContentType.objects.get_by_natural_key(app_label, model)
                ctypes.add(ctype)
                for perm in _get_all_permissions(opts, ctype):
                    searched_perms.append((ctype, perm))
        all_perms = set(Permission.objects.filter(
            content_type__in=ctypes,
        ).values_list(
            "content_type", "codename"
        ))

        objs = [
            Permission(codename=codename, name=name, content_type=ctype)
            for ctype, (codename, name) in searched_perms
            if (ctype.pk, codename) not in all_perms
        ]
        Permission.objects.bulk_create(objs)
        if verbosity >= 2:
            for obj in objs:
                sys.stdout.write("Adding permission '%s'" % obj)
        models.signals.post_migrate.connect(create_proxy_permissions)
        models.signals.post_migrate.disconnect(update_contenttypes)

    class Meta:
        proxy = True
        managed = False
        verbose_name = _('Customization Form')
        verbose_name_plural = _('    Customization Form')

    def clean(self): #Appreciation to Daniel M.
        pass


"""
This model class maps to a database view that looks up the django_admin logs,
location, customuser and group
"""
class AhoDoamain_Lookup(models.Model):
    indicator_id = models.AutoField(primary_key=True)
    indicator_name = models.CharField(_("Indicator Name"),blank=False,null=False,
        max_length=500)
    code = models.CharField(_("Indicator Code"),max_length=10, blank=True)
    domain_name  = models.CharField(_("Theme"),max_length=230, blank=True)
    domain_level  = models.IntegerField(_("Theme Level"),null=False,blank=False)

    class Meta:
        managed = False
        db_table = 'aho_domain_lookup'
        verbose_name = _('Theme Lookup')
        verbose_name_plural = _('Themes Lookup')
        ordering = ('indicator_name', )

    def __str__(self):
        return self.indicator_name


class aho_factsindicator_archive(models.Model):
    fact_id = models.AutoField(primary_key=True)
    uuid =models.CharField(_('Unique ID'),unique=True,max_length=36, blank=False,
        null=False,default=uuid.uuid4,editable=False)
    user = models.ForeignKey(CustomUser, models.PROTECT,blank=False,
		verbose_name = 'User Name (Email)',) # request helper field
    indicator = models.ForeignKey('StgIndicator',models.PROTECT,blank=False,
        null=False, verbose_name = _('Indicator Name'))
    location = models.ForeignKey(StgLocation, models.PROTECT,
        blank=False,verbose_name = _('Location Name'))
    categoryoption = models.ForeignKey(StgCategoryoption, models.PROTECT,
        blank=False,verbose_name = _('Disaggregation Option'), default=99)
    datasource = models.ForeignKey(StgDatasource, models.PROTECT,blank=False,
        null=False, verbose_name = _('Data Source'))
    measuremethod = models.ForeignKey(StgMeasuremethod, models.PROTECT,
        blank=True,null=True, verbose_name = _('Measure Type'))
    value_received = models.DecimalField(_('Value'),max_digits=20,
        decimal_places=3,blank=False,null=True)
    numerator_value = models.DecimalField(_('Numerator Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    denominator_value = models.DecimalField(_('Denominator Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    min_value = models.DecimalField(_('Minimum Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    max_value = models.DecimalField(_('Maximum Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    target_value = models.DecimalField(_('Target Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    string_value=models.CharField(_('String Value'),max_length=500,blank=True,
        null=True) # davy's request as of 30/4/2019
    start_period = models.IntegerField(_('Starting Period',),null=False,
        blank=False,default=datetime.date.today().year,#extract current date
        help_text=_("This Year marks the start of the reporting period"))
    end_period  = models.IntegerField(_('Ending Year'),null=False,blank=False,
        default=datetime.date.today().year, #extract current date year value only
        help_text=_("This Year marks the end of reporting. \
        The value must be current year or greater than the start year"))
    period = models.CharField(_('Period'),max_length=25,blank=True,null=False)
    comment = models.CharField(_('Status'),choices= STATUS_CHOICES,
        max_length=10,default=STATUS_CHOICES[0][0])
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = False
        db_table = 'fact_data_archive'
        verbose_name = _('Archive')
        verbose_name_plural = _('Indicators Archive')
        ordering = ('indicator__translations__name',)

    def __str__(self):
         return str(self.indicator)


class NHOCustomizationIcons(TranslatableModel):
    icon_id = models.AutoField(primary_key=True)
    unicode = models.CharField(unique=True, max_length=5, blank=False,
        null=False)
    code = models.CharField(unique=True, max_length=50, blank=True,null=True)
    version = models.CharField(_("Icon Version"),max_length=15,blank=True,
        null=True,default='v5.15',)
    translations = TranslatedFields(
        name = models.CharField(_("Title"),max_length=230, blank=False,
            null=False,),
        shortname = models.CharField(_('Short Name'),max_length=50,blank=True,
            null=True),
        description = models.TextField(_('Description'),blank=True,null=True)
    )
    date_created = models.DateTimeField(_('Date Created'),blank=True,null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True,auto_now=True)
    class Meta:
        managed = True
        db_table = 'stg_fontawesome_icons'
        verbose_name = _('Custom Icon')
        verbose_name_plural = _('Custom Icons')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the data source name

# This handler is called by pre_save signal to reduce the number of priority
# indicators in fact_priority_indicators table in case the event is turned off!
def delete_handler(sender, instance, **kwargs):
    qs = NHOCustomFactsindicator.objects.order_by('date_created') #order by date
    if qs.count() > 10:
        qs[0].delete() #remove the oldest element


class NHOCustomFactsindicator(models.Model):
    PRIORITY = (
        (1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5'),(6,'6'),(7,'7'),(8,'8'),
        (9,'9'),(10,'10'),
    )
    fact_id = models.AutoField(primary_key=True)
    uuid = models.CharField(_('Unique ID'),unique=True,max_length=36, blank=False,
        null=False,default=uuid.uuid4,editable=False)
    user = models.ForeignKey(CustomUser, models.PROTECT,blank=False,
		verbose_name = 'User Name (Email)',) # request helper field
    indicator = models.ForeignKey('StgIndicator',models.PROTECT,blank=False,
        null=False, verbose_name = _('Indicator Name'))
    location = models.ForeignKey(StgLocation, models.PROTECT,
        blank=False,verbose_name = _('Location Name'))
    categoryoption = models.ForeignKey(StgCategoryoption, models.PROTECT,
        blank=False,verbose_name = _('Disaggregation Option'), default=None)
    datasource = models.ForeignKey(StgDatasource, models.PROTECT,blank=False,
        null=False, verbose_name = _('Data Source'))
    measuremethod = models.ForeignKey(StgMeasuremethod, models.PROTECT,
        blank=True,null=True, verbose_name = _('Measure Type'))
    icon = models.ForeignKey(NHOCustomizationIcons,models.PROTECT,blank=False,
        null=False, default=1, verbose_name = _('Font Icon'))
    value_received = models.DecimalField(_('Value'),max_digits=20,
        decimal_places=2,blank=False,null=True)
    period = models.CharField(_('Period'),max_length=25,blank=True,null=False)
    priority = models.SmallIntegerField(_('Priority Level'),choices=PRIORITY,
        blank=False,null=False,)
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'fact_priority_indicators'
        unique_together = ('indicator','location','categoryoption','datasource',
        'period',)
        verbose_name = _('Indicator Priority')
        verbose_name_plural = _('Indicators Priorities')
        ordering = ('indicator__translations__name',)

    def __str__(self):
         return str(self.indicator)
pre_save.connect(delete_handler,sender=NHOCustomFactsindicator) #delete oldest


class StgNarrative_Type(TranslatableModel):
    type_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False, null=False,default=uuid.uuid4,editable=False)
    code = models.CharField(unique=True, max_length=50, blank=True, null=False,
        verbose_name = 'Code')
    translations = TranslatedFields(
        name = models.CharField(_('Name'),max_length=500,blank=False,null=False),
        shortname = models.CharField(_('Short Name'),unique=True,
            max_length=120,blank=False,null=True),
        description = models.TextField(_('Brief Description'),blank=False,
            null=True)
    )
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_narrative_type'
        verbose_name = _('Narrative Type')
        verbose_name_plural = _('Narrative Types')
        ordering = ('translations__name',)

    def __str__(self):
        return self.name #display the knowledge product category name

    # The filter function need to be modified to work with django parler as follows:
    def clean(self): # Don't allow end_period to be greater than the start_period.
        if StgNarrative_Type.objects.filter(
            translations__name=self.name).count() and not self.type_id:
            raise ValidationError({'name':_('Sorry! This narrative type exists')})

    def save(self, *args, **kwargs):
        super(StgNarrative_Type, self).save(*args, **kwargs)


class StgAnalyticsNarrative(models.Model):
    analyticstext_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False, null=False,default=uuid.uuid4,editable=False)
    narrative_type = models.ForeignKey(StgNarrative_Type,models.PROTECT,
        verbose_name = _('Narrative Type'))
    domain = models.ForeignKey(StgIndicatorDomain,models.PROTECT,  blank=False,
        null=False,verbose_name = _('Theme'),  default = 1)
    location = models.ForeignKey(StgLocation, models.PROTECT, blank=False,
        null=False,verbose_name = _('Location'), default = 1)
    code = models.CharField(unique=True, max_length=50, blank=True, null=False,
        verbose_name = _('Code'))  # Field name made lowercase.
    narrative_text = models.TextField(_('Narrative Text'),blank=False,null=False)
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_analytics_narrative'
        verbose_name = _('Theme Narrative')
        verbose_name_plural = _('Theme Narratives')
        ordering = ('-narrative_type',) #sorted in descending order by date created

    def __str__(self):
        return self.narrative_text


class StgIndicatorNarrative(models.Model):
    indicatornarrative_id = models.AutoField(primary_key=True)
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False, null=False,default=uuid.uuid4,editable=False)
    narrative_type = models.ForeignKey(StgNarrative_Type,models.PROTECT,
        verbose_name = _('Narrative Type'))
    indicator = models.ForeignKey('StgIndicator', models.PROTECT,blank=False,
        null=False,verbose_name = _('Indicator'))
    location = models.ForeignKey(StgLocation, models.PROTECT, blank=False,
        null=False,verbose_name = _('Location'), default = 1)
    code = models.CharField(unique=True, max_length=50, blank=True, null=False,
        verbose_name = _('Code'))  # Field name made lowercase.
    narrative_text = models.TextField(_('Narrative Text'),blank=False,null=False)
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
         managed = True
         db_table = 'stg_indicator_narrative'
         verbose_name = _('Indicator Narrative')
         verbose_name_plural = _('Indicators Narrative')
         ordering = ('-narrative_type',)

    def __str__(self):
         return str(self.indicator)
