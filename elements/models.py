from django.db import models
import uuid
from django.conf import settings # for resolving translation issues
from django.utils import timezone
import datetime
from regions.models import StgLocation
from authentication.models import CustomUser
from django.utils import translation
from django.utils.translation import gettext_lazy as _ # The _ is alias for gettext
from parler.models import TranslatableModel,TranslatedFields
from django.core.exceptions import ValidationError
from django.db.models.fields import DecimalField
from home.models import (StgDatasource,StgCategoryoption,StgMeasuremethod,
    StgValueDatatype)

YEAR_CHOICES = [(r,r) for r in range(1900, datetime.date.today().year+1)]

def make_choices(values):
    return [(v, v) for v in values]

class StgDataElement(TranslatableModel):
    AGGREGATION_TYPE = ('Count','Sum','Average','Standard Deviation',
        'Variance', 'Min', 'max','None')
    dataelement_id = models.AutoField(primary_key=True)  # Field name made lowercase.
    uuid = uuid = models.CharField(unique=True,max_length=36, blank=False,
        null=False,default=uuid.uuid4,editable=False,verbose_name=_('Unique ID'))  # Field name made lowercase.
    code = models.CharField( unique=True, max_length=45,blank=True, null=False)
    translations = TranslatedFields(
        name = models.CharField(_('Data Element Name'),max_length=230,
                blank=False,null=False),  # Field name made lowercase.
        shortname = models.CharField(_('short name'), max_length=50),  # Field name made lowercase.
        description = models.TextField(_('Description'),blank=True, null=True),  # Field name made lowercase.
    )
    aggregation_type = models.CharField(_('Aggregate Type'),max_length=45,
        choices=make_choices(AGGREGATION_TYPE),default=AGGREGATION_TYPE[0])  # Field name made lowercase.
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_data_element'
        verbose_name = _("Element")
        verbose_name_plural = _('Data Elements')
        ordering = ('translations__name',)

    # This method makes it possible to enter multi-records in the Tabular form without
    # returning the language code error! resolved on 10th August 2020
    def __str__(self):
        language_code = (translation.get_language() or settings.LANGUAGE_CODE).split("-", 1)[0]
        return self.safe_translation_getter(
            'name', any_language=True, language_code=language_code)


class FactDataElement(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    fact_id = models.AutoField(primary_key=True)  # Field name made lowercase.
    uuid = uuid = models.CharField(unique=True,max_length=36, blank=False,
        null=False,default=uuid.uuid4,editable=False,verbose_name=_('Unique ID'))
    user = models.ForeignKey(CustomUser, models.PROTECT,
        verbose_name=_('User Name (Email)'))
    dataelement = models.ForeignKey(StgDataElement, models.PROTECT,
        verbose_name =_('Data Element'))
    location = models.ForeignKey(StgLocation,models.PROTECT,
        verbose_name = _('Location',))
    categoryoption = models.ForeignKey(StgCategoryoption, models.PROTECT,
        verbose_name =_('Disaggregation Option'), default = 999)
    # This field is used to lookup sources of routine systems, census and surveys
    datasource = models.ForeignKey(StgDatasource, models.PROTECT,blank=False,
        null=False,verbose_name = _('Data Source'), default = 4)
    # This field is used to lookup the type of data required such as text, integer or float
    valuetype = models.ForeignKey(StgValueDatatype, models.PROTECT,
        verbose_name=_('Data Type'),  default = 1)
    value = models.DecimalField(_('Data Value'),max_digits=20, decimal_places=3,
        null=False,blank=False)
    target_value = models.DecimalField(_('Target Value'),max_digits=20,
        decimal_places=3,blank=True, null=True)
    start_year = models.IntegerField(_('Start Year'), null=False,blank=False,
        default=datetime.date.today().year)
    end_year  = models.IntegerField(_('Ending Year'),null=False,blank=False,
        default=datetime.date.today().year)
    period = models.CharField(_('Period'),max_length=10,blank=True,
        null=False) # concatenated period field
    comment = models.CharField(_('Status'),max_length=10,choices= STATUS_CHOICES,
        default=STATUS_CHOICES[0][0])
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True,)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        permissions = (
            ("approve_factdataelement","Can approve Data Element"),
            ("reject_factdataelement","Can reject Data Element"),
            ("pend_factdataelement","Can pend Data Element")
        )

        managed = True
        db_table = 'fact_data_element'
        verbose_name = _('Data Element')
        verbose_name_plural = _('   Single-Record Form')
        ordering = ('location', )
        unique_together = ('dataelement', 'location','datasource',
            'categoryoption','start_year','end_year')

    def __str__(self):
         return str(self.dataelement)

    """
    The purpose of this method is to compare the start_year to the end_year. If the
    start_year is greater than the end_year athe model should show an inlines error
    message and wait until the user corrects the mistake.
    """
    def clean(self): # Don't allow end_year to be greater than the srart_year.
        if self.start_year <=1900 or self.start_year > datetime.date.today().year:
            raise ValidationError({'start_year':_(
                'Sorry! The start year cannot be lower than 1900 or greater \
                than the current Year ')})
        elif self.end_year <=1900 or self.end_year > datetime.date.today().year:
            raise ValidationError({'end_year':_(
                'Sorry! The end year cannot be lower than start year or greater \
                than the current Year ')})
        elif self.end_year < self.start_year and self.start_year is not None:
            raise ValidationError({'end_year':_(
                'Sorry! Ending year cannot be lower than the start year. \
                Please make corrections')})

    """
    The purpose of this method is to concatenate the date that are entered as
    start_year and end_year and save the concatenated value as a string in the
    database ---important to take care of Davy's date request
    """
    def get_period(self):
        if self.start_year and self.end_year:
            if self.start_year == self.end_year:
                period = int(self.start_year)
            else:
                period =str(int(self.start_year))+"-"+ str(int(self.end_year))
        return period

    """
    This method overrides the save method to store the derived field into database.
    Note that the last line calls the super class FactDataIndicator to save the value
    """
    def save(self, *args, **kwargs):
        self.period = self.get_period()
        super(FactDataElement, self).save(*args, **kwargs)

"""
data elements proxy model.The def clean (self) method was contributed
by Daniel Mbugua to resolve the issue of parent-child saving issue in the
multi-records entry form.My credits to Mr Mbugua of MSc DCT, UoN-Kenya

"""
class DataElementProxy(StgDataElement):
    class Meta:
        proxy = True
        verbose_name = _('Multi_Records Form')
        verbose_name_plural = _('  Multi_Records Form')

    def clean(self):
        pass


class StgDataElementGroup(TranslatableModel):
    group_id = models.AutoField(primary_key=True)  # Field name made lowercase.
    uuid = uuid = models.CharField(_('Unique ID'),unique=True,max_length=36,
        blank=False, null=False,default=uuid.uuid4,editable=False)
    translations = TranslatedFields(
        name = models.CharField(_('Group Name'),max_length=200,
            blank=False, null=False),  # Field
        shortname = models.CharField(_('Short Name'),unique=True, max_length=120,
            blank=False,null=False),
        description = models.TextField(_('Description'),blank=False, null=False)
    )
    code = models.CharField(_('Group Code'),unique=True, max_length=50,
        blank=True,null=False)
    dataelement = models.ManyToManyField(StgDataElement,
        db_table='stg_data_element_membership',blank=True,
        verbose_name=_('Data Elements'))
    date_created = models.DateTimeField(_('Date Created'),blank=True, null=True,
        auto_now_add=True)
    date_lastupdated = models.DateTimeField(_('Date Modified'),blank=True,
        null=True, auto_now=True)

    class Meta:
        managed = True
        db_table = 'stg_data_element_group'
        verbose_name = _('Element Group')
        verbose_name_plural = _('Element Groups')
        ordering = ('translations__name',)

    def __str__(self):
        return str(self.name)

    '''
    This method ensures that data element group is unique instead of enforcing
    unique constraint on DB
    '''
    def clean(self): # Don't allow end_period to be greater than the start_period.
        if StgDataElementGroup.objects.filter(
            translations__name=self.name).count() and not self.group_id:
            raise ValidationError({'name':_('Sorry! Data Elements Group with \
                same name already exists')})

    def save(self, *args, **kwargs):
        super(StgDataElementGroup, self).save(*args, **kwargs)
