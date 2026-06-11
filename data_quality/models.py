from tabnanny import check
from django.db import models

from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.fields import DecimalField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_pandas.managers import DataFrameManager

from parler.models import TranslatableModel, TranslatedFields
from home.models import (
    StgDatasource,StgCategoryoption,StgMeasuremethod,
    StgValueDatatype)
from regions.models import StgLocation
from authentication.models import CustomUser

from indicators.models import StgIndicator

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


class Facts_DataFilter (models.Model): # requested by Serge to determine facts loaded
    filter_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name=_('User Name (Email)'),default=14) # request helper field
    locations = models.ManyToManyField(StgLocation,
        db_table='dqa_filter_location_members',blank=True,
        verbose_name = _('Locations'))  # Field name made lowercase. 
    indicators = models.ManyToManyField(StgIndicator,
        db_table='dqa_filter_indicator_members',blank=True,
        verbose_name = _('Indicators'))  # Field name made lowercase.
    categoryoptions = models.ManyToManyField(StgCategoryoption,
        db_table='dqa_filter_category_members',blank=True,
        verbose_name = _('Category Options'))  # Field name made lowercase.  
    datasource = models.ManyToManyField(StgDatasource,
        db_table='dqa_filter_source_members',blank=True,
        verbose_name = _('Data Sources'))  # Field name made lowercase.
    start_period = models.PositiveIntegerField(_('Starting period'),null=False,
        blank=False,validators=[MinValueValidator(1900),max_value_current_year],
        default=current_year(),
        help_text=_("This marks the start of reporting period"))
    end_period=models.PositiveIntegerField(_('Ending Period'),null=False,blank=False,
        validators=[MinValueValidator(1900),max_value_current_year],
        default=current_year(),
        help_text=_("This marks the end of reporting. The value must be current \
            year or greater than the start year")) 
    
    class Meta:
        managed = True
        db_table = 'dqa_filter_facts_dataframe'
        verbose_name = _('Filter')
        verbose_name_plural = _('    Facts Filter')

    # Override Save method to store only one instance
    def save(self, *args, **kwargs):
        if self.__class__.objects.count():
            self.pk = self.__class__.objects.first().pk
        super().save(*args, **kwargs)


    def __str__(self):
            return str(_("Filter Facts Locations, Indicators, Categoryoptions, Datasources and Periods"))


class Facts_DataFrame (models.Model):
    fact_id = models.AutoField(primary_key=True)
    user = models.PositiveIntegerField(blank=True,verbose_name='UserID') # request helper field
    afrocode = models.CharField(_('Indicator ID'),max_length=1500,
        blank=True, null=True)
    indicator_name = models.CharField(_('Indicator Name'),max_length=1500,
        blank=True, null=True)
    location = models.CharField(max_length=1500,blank=False,
        verbose_name = _('Location Name'),)
    categoryoption = models.CharField(max_length=1500,blank=False,
        verbose_name =_('Disaggregation Options'))
    datasource = models.CharField(max_length=1500,verbose_name = _('Data Source'))
    measure_type = models.CharField(max_length=1500,blank=False,
        verbose_name =_('Measure Type'))
    value = DecimalField(_('Numeric Value'),max_digits=20,
        decimal_places=3,blank=True,null=True)
    start_period = models.PositiveIntegerField(
        blank=True,verbose_name=_('Start Period')) 
    end_period = models.PositiveIntegerField(
        blank=True,verbose_name=_('End Period')) 
    period = models.CharField(_('Period'),max_length=25,blank=True,null=False)
    objects = DataFrameManager() #connect the model to the dataframe manager

    class Meta:
        managed = False
        db_table = 'dqa_vw_facts_dataframe'
        verbose_name = _('Facts')
        verbose_name_plural = _('   Facts Dataset')
        ordering = ('indicator_name',)

    def __str__(self):
         return str(self.indicator_name)    


# The following model is used to validate measure types in the fact table
class MeasureTypes_Validator(models.Model): # this is equivalent to inventory_status
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name=_('User Name (Email)'),default=14) # request helper field
    afrocode = models.CharField(_('Indicator ID'),max_length=50,
        blank=True, null=True)
    indicator = models.ForeignKey(StgIndicator, models.CASCADE,
        verbose_name = _('Indicator Name'),default=None)
    measure_type = models.ForeignKey(StgMeasuremethod,models.CASCADE,
        blank=False,verbose_name =_('Measure Type'),default=None)

    measuremethod_id = models.PositiveIntegerField(_('Measure Type ID'),
        blank=True,null=True)
    objects = DataFrameManager() #connect the model to the dataframe manager

    class Meta:
        managed = True
        db_table = 'dqa_valid_measure_type'
        unique_together = ('indicator', 'measure_type',) 
        verbose_name = _('Valid Measure Type')
        verbose_name_plural = _('  Measuretypes')
        ordering = ('indicator',)

    
    def get_afrocode(self):
        afrocode = None
        afrocode = self.indicator.afrocode
        return afrocode

    def get_measure_id(self):
        measureid = None
        measureid = self.measure_type.measuremethod_id
        return measureid

    def save(self, *args, **kwargs):
        self.afrocode = self.get_afrocode()
        self.measuremethod_id = self.get_measure_id()       
        super(MeasureTypes_Validator, self).save(*args, **kwargs)

    def __str__(self):
         return str(self.measure_type)
         
    

# The following model is used to validate data sources in the fact table
class DataSource_Validator(models.Model): # this is equivalent to inventory_status
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name=_('User Name (Email)'),default=14) # request helper field
    afrocode = models.CharField(_('Indicator ID'),max_length=50,
        blank=True, null=True)
    indicator = models.ForeignKey(StgIndicator, models.CASCADE,
        verbose_name = _('Indicator Name'),default=None)
    datasource = models.ForeignKey(StgDatasource, models.CASCADE,
        verbose_name = _('Data Source'),default=None)
    datasourceid = models.PositiveIntegerField(_('Data SourceID'),
        blank=True,null=True)
    objects = DataFrameManager() #connect the model to the dataframe manager


    class Meta:
        managed = True
        db_table = 'dqa_valid_datasources'
        unique_together = ('indicator', 'datasource',) 
        verbose_name = _('Valid Source')
        verbose_name_plural = _('  Datasources')
        ordering = ('indicator',)

    def get_afrocode(self):
        afrocode = None
        afrocode = self.indicator.afrocode
        return afrocode

    def get_datasource_id(self):
        datasource = None
        datasource = self.datasource.datasource_id
        return datasource

    def save(self, *args, **kwargs):
        self.afrocode = self.get_afrocode()
        self.datasource_id = self.get_datasource_id()       
        super(DataSource_Validator, self).save(*args, **kwargs)

    def __str__(self):
         return str(self.datasource)


# The following model is used to validate categoryoptions in the fact table
class CategoryOptions_Validator(models.Model): # this is equivalent to inventory_status
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name=_('User Name (Email)'),default=14) # request helper field  
    afrocode = models.CharField(_('Indicator ID'),max_length=50,
        blank=True, null=True)
    indicator = models.ForeignKey(StgIndicator, models.CASCADE,
        verbose_name = _('Indicator Name'),default=None)
    categoryoption = models.ForeignKey(StgCategoryoption, models.CASCADE,
        blank=False,verbose_name =_('Disaggregation Options'),default=None)
    categoryoptionid = models.PositiveIntegerField(_('Disaggregation ID'),
        blank=True,null=True)
    objects = DataFrameManager() #connect the model to the dataframe manager
 

    class Meta:
        managed = True
        db_table = 'dqa_valid_categoryoptions'
        unique_together = ('indicator', 'categoryoption',) 
        verbose_name = _('Valid Category Option')
        verbose_name_plural = _('  Categoryoptions')
        ordering = ('indicator',)

    def get_afrocode(self):
        afrocode = None
        afrocode = self.indicator.afrocode
        return afrocode

    def get_categoryoption_id(self):
        categoryoption = None
        categoryoption = self.categoryoption.categoryoption_id
        return categoryoption

    def save(self, *args, **kwargs):
        self.afrocode = self.get_afrocode()
        self.categoryoptionid = self.get_categoryoption_id()       
        super(CategoryOptions_Validator, self).save(*args, **kwargs)

    def __str__(self):
         return str(self.categoryoption)
    

class Similarity_Index(models.Model): # this is equivalent to inventory_status
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name=_('User Name (Email)'),default=14) # request helper field
    source_indicator = models.CharField(_('Data Indicator'),max_length=2000,
        blank=True, null=True)
    similar_indicator = models.CharField(_('Similar Indicator'),max_length=2000,
        blank=True, null=True)
    score = models.PositiveIntegerField(_('Similarity Score %'),
        blank=False,null=False)
    objects = DataFrameManager() #connect the model to the dataframe manager


    class Meta:
        managed = True
        db_table = 'dqa_similar_indicators_score'
        unique_together = ('source_indicator', 'similar_indicator',) 
        verbose_name = _('Similarity Score')
        verbose_name_plural = _('Similarity Scores')
        ordering = ('-score',)

    def __str__(self):
         return self.source_indicator


class Mutiple_MeasureTypes(models.Model): # this is equivalent to inventory_status
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name=_('User Name (Email)'),default=14) # request helper field
    indicator_name = models.CharField(_('Indicator Name'),max_length=2000,
        blank=True, null=True,editable=False)
    location = models.CharField(_('Country'),max_length=2000,
        blank=True, null=True,editable=False)
    categoryoption = models.CharField(_('Category Option'),max_length=2000,
        blank=True, null=True,editable=False)
    datasource = models.CharField(_('Data Source'),max_length=2000,
        blank=True, null=True,editable=False)
    measure_type = models.CharField(_('Measure Type'),max_length=2000,
        blank=True, null=True,editable=False)
    value = DecimalField(_('Value Received'),max_digits=20,decimal_places=3,
        blank=True,null=True,editable=False)
    period = models.CharField(_('Period'),max_length=2000,
        blank=True, null=True,editable=False)
    counts = models.PositiveIntegerField(_('Number of Measure Types'),
        blank=True,null=True,editable=False) 
    remarks = models.CharField(_('Remarks'),max_length=2000,
        blank=True, null=True)  
    objects = DataFrameManager() #connect the model to the dataframe manager
   
    class Meta:
        managed = True
        db_table = 'dqa_multiple_indicators_checker'
        verbose_name = _('Multiple Measure Type')
        unique_together = ('indicator_name', 'location', 'categoryoption',
            'datasource','period',)  
        verbose_name_plural = _('Multiple Measures')
        ordering = ('indicator_name',)

    def __str__(self):
         return self.indicator_name


# ---------------------------data validation models from algorithms 1-4-------------------------------------------------

class MissingValuesRemarks(models.Model): # this is equivalent to inventory_status
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name=_('User Name (Email)'),default=14) # request helper field
    indicator_name = models.CharField(_('Indicator Name'),max_length=2000,
        blank=True, null=True)
    location = models.CharField(_('Country'),max_length=2000,
        blank=True, null=True,editable=False)
    categoryoption = models.CharField(_('Category Option'),max_length=2000,
        blank=True, null=True,editable=False)
    datasource = models.CharField(_('Data Source'),max_length=2000,
        blank=True, null=True,editable=False)
    measure_type = models.CharField(_('Measure Type'),max_length=2000,
        blank=True, null=True,editable=False)
    value = DecimalField(_('Value Received'),max_digits=20,decimal_places=3,
        blank=True,null=True,editable=False)
    period = models.CharField(_('Period'),max_length=2000,
        blank=True, null=True,editable=False)
    counts = models.PositiveIntegerField(_('Number of Measure Types'),
        blank=True,null=True,editable=False) 
    remarks = models.CharField(_('Remarks'),max_length=2000,
        blank=True, null=True)  
    objects = DataFrameManager() #connect the model to the dataframe manager

    class Meta:
        managed = True
        db_table = 'dqa_missing_indicator_values'
        unique_together = ('indicator_name', 'location', 'categoryoption',
            'datasource','period',) 
        verbose_name = _('Missing Value')
        verbose_name_plural = _('Missing Values')
        ordering = ('measure_type',)

    def __str__(self):
         return self.indicator_name


class DqaInvalidCategoryoptionRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name=_('User Name (Email)'),default=14) # request helper field
    indicator_name = models.CharField(_('Indicator Name'),
        blank=True, null=True,max_length=2000,)
    location = models.CharField(_('Country'),blank=True, null=True,
        max_length=2000,)
    categoryoption = models.CharField(_('Category Option'),blank=True,
        null=True,max_length=2000,)
    datasource = models.CharField(_('Data Source'),blank=True, null=True,
        max_length=2000,)
    measure_type = models.CharField(_('Measure Type'), blank=True, 
        null=True,max_length=2000,)
    value = DecimalField(_('Value'),max_digits=20,decimal_places=3,
        blank=True,null=True)
    period = models.CharField(_('Period'),blank=True, null=True,
        max_length=2000,)
    check_category_option = models.TextField(_('Check Category Option'),
        blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'dqa_invalid_categoryoption_remarks'
        unique_together = ('indicator_name', 'location', 'categoryoption',
            'datasource','period',)  
        verbose_name = _('Check Categoryoption')
        verbose_name_plural = _(' Check Categories')
        ordering = ('indicator_name',)

    def __str__(self):
        return self.indicator_name


class DqaInvalidDatasourceRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name=_('User Name(Email)'),default=None) # request helper field
    indicator_name = models.CharField(_('Indicator Name'),
        blank=True, null=True,max_length=2000,)
    location = models.CharField(_('Country'),blank=True, null=True,
        max_length=2000,)
    categoryoption = models.CharField(_('Category Option'),blank=True,
        null=True,max_length=2000,)
    datasource = models.CharField(_('Data Source'),blank=True, null=True,
        max_length=2000,)
    measure_type = models.CharField(_('Measure Type'),blank=True, 
        null=True,max_length=2000,)
    value = DecimalField(_('Value'),max_digits=20,decimal_places=3,
        blank=True,null=True)
    period = models.CharField(_('Period'),blank=True, null=True,
        max_length=2000,)
    check_data_source = models.TextField(_('Check Data Source'),
        blank=True, null=True) 

    class Meta:
        managed = True
        db_table = 'dqa_invalid_datasource_remarks'
        unique_together = ('indicator_name', 'location', 'categoryoption',
            'datasource','period',)         
        verbose_name = _('Invalid Source')
        verbose_name_plural = _(' Check Sources')
        ordering = ('indicator_name',)

    def __str__(self):
        return self.indicator_name
        

class DqaInvalidMeasuretypeRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name=_('User Name (Email)'),default=14) # request helper field
    indicator_name = models.CharField(_('Indicator Name'),
        blank=True, null=True,max_length=2000,)
    location = models.CharField(_('Country'),blank=True, null=True,
        max_length=2000,)
    categoryoption = models.CharField(_('Category Option'),blank=True,
        null=True,max_length=2000,)
    datasource = models.CharField(_('Data Source'),blank=True, null=True,
        max_length=2000,)
    measure_type = models.CharField(_('Measure Type'),blank=True, 
        null=True,max_length=2000,)
    value = DecimalField(_('Value'),max_digits=20,decimal_places=3,
        blank=True,null=True)
    period = models.CharField(_('Period'),blank=True, null=True,
        max_length=2000,)
    check_mesure_type = models.TextField(_('Check Measure Type'),
        blank=True, null=True) 

    class Meta:
        managed = True
        db_table = 'dqa_invalid_measuretype_remarks'
        unique_together = ('indicator_name', 'location', 'categoryoption',
            'datasource','period',)  
        verbose_name = _('Check Measure')
        verbose_name_plural = _(' Check Measures')
        ordering = ('indicator_name',)

    def __str__(self):
        return self.indicator_name


class DqaInvalidPeriodRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name=_('User Name (Email)'),default=14) # request helper field
    indicator_name = models.CharField(_('Indicator Name'),
        blank=True, null=True,max_length=2000,)
    location = models.CharField(_('Country'),blank=True, null=True,
        max_length=2000,)
    categoryoption = models.CharField(_('Category Option'),blank=True,
        null=True,max_length=2000,)
    datasource = models.CharField(_('Data Source'),blank=True, null=True,
        max_length=2000,)
    measure_type = models.CharField(_('Measure Type'),blank=True, 
        null=True,max_length=2000,)
    value = DecimalField(_('Value'),max_digits=20,decimal_places=3,
        blank=True,null=True)
    period = models.CharField(_('Period'),blank=True, null=True,
        max_length=2000,)
    check_year = models.TextField(_('Check Period'),blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'dqa_invalid_period_remarks'
        unique_together = ('indicator_name', 'location', 'categoryoption',
            'datasource','period',)  
        verbose_name = _('Check Period')
        verbose_name_plural = _(' Check Periods')
        ordering = ('indicator_name',)
    

    def __str__(self):
        return self.indicator_name


class DqaExternalConsistencyOutliersRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name=_('User Name (Email)'),default=14) # request helper field
    indicator_name = models.CharField(_('Indicator Name'),
        blank=True, null=True,max_length=2000,)
    location = models.CharField(_('Country'),blank=True, null=True,
        max_length=2000,)
    categoryoption = models.CharField(_('Category Option'),blank=True,
        null=True,max_length=2000,)
    datasource = models.CharField(_('Data Source'),blank=True, null=True,
        max_length=2000,)
    measure_type = models.CharField(_('Measure Type'),blank=True, 
        null=True,max_length=2000,)
    value = DecimalField(_('Value'),max_digits=20,decimal_places=3,
        blank=True,null=True)
    period = models.CharField(_('Period'),blank=True, null=True,
        max_length=2000,)
    external_consistency = models.TextField(_('Check External Consistency'), 
        blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'dqa_external_inconsistencies_remarks'
        unique_together = ('indicator_name', 'location', 'categoryoption',
            'datasource','period',)  
        verbose_name = _('External Consistency')
        verbose_name_plural = _('External Consistencies')
        ordering = ('indicator_name',)
    
    def __str__(self):
        return self.indicator_name


class DqaInternalConsistencyOutliersRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name=_('User Name (Email)'),default=14) # request helper field
    indicator_name = models.CharField(_('Indicator Name'),
        blank=True, null=True,max_length=2000,)
    location = models.CharField(_('Country'),blank=True, null=True,
        max_length=2000,)
    categoryoption = models.CharField(_('Category Option'),blank=True,
        null=True,max_length=2000,)
    datasource = models.CharField(_('Data Source'),blank=True, null=True,
        max_length=2000,)
    measure_type = models.CharField(_('Measure Type'),blank=True, 
        null=True,max_length=2000,)
    value = DecimalField(_('Value'),max_digits=20,decimal_places=3,
        blank=True,null=True)
    period = models.CharField(_('Period'),blank=True, null=True,
        max_length=2000,)
    internal_consistency = models.TextField(_('Check Internal Consistency'),
        blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'dqa_internal_consistencies_remarks'
        unique_together = ('indicator_name', 'location', 'categoryoption',
            'datasource','period',)  
        verbose_name = _('Internal Consistency')
        verbose_name_plural = _('Internal Consistencies')
        ordering = ('indicator_name',)
    
    def __str__(self):
        return self.indicator_name

class DqaValueTypesConsistencyRemarks(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, models.PROTECT, blank=True,
        verbose_name=_('User Name (Email)'),default=14) # request helper field
    indicator_name = models.CharField(_('Indicator Name'),
        blank=True, null=True,max_length=2000,)
    location = models.CharField(_('Country'),blank=True, null=True,
        max_length=2000,)
    categoryoption = models.CharField(_('Category Option'),blank=True,
        null=True,max_length=2000,)
    datasource = models.CharField(_('Data Source'),blank=True, null=True,
        max_length=2000,)
    measure_type = models.CharField(_('Measure Type'),blank=True, 
        null=True,max_length=2000,)
    value = DecimalField(_('Value'),max_digits=20,decimal_places=3,
        blank=True,null=True)
    period = models.CharField(_('Period'),blank=True, null=True,
        max_length=2000,)
    check_value = models.TextField(_('Check Value Type Consistency'),
        blank=True, null=True,max_length=2000,)

    class Meta:
        managed = True
        db_table = 'dqa_valuetype_consistencies_remarks'
        unique_together = ('indicator_name', 'location', 'categoryoption',
            'datasource','period',)  
        verbose_name = _('Value Consistency')
        verbose_name_plural = _('Value Consistencies')
        ordering = ('indicator_name',)
    
    def __str__(self):
        return self.indicator_name
