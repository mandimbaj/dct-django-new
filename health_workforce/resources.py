from import_export import resources
from import_export.fields import Field
from .models import (StgHealthWorkforceFacts,StgHealthCadre,StgTrainingInstitution,
    HumanWorkforceResourceProxy,)
from home.models import StgCategoryoption,StgDatasource,StgValueDatatype
from regions.models import StgLocation
from import_export.widgets import ForeignKeyWidget, DateWidget

# This class requires the methods for saving the instance to be overriden
class HealthWorkforceResourceExport(resources.ModelResource):
    location_name = Field(attribute='location__name', column_name='Location')
    cadre_name = Field(attribute='cadre__name', column_name='Health Cadre')
    categoryoption_name = Field(attribute='categoryoption__name',
        column_name='Disaggregation')
    datasource = Field(attribute='datasource', column_name='Data Source')
    measuremethod = Field(attribute='measuremethod', column_name='Measure Type')
    period = Field(attribute='period', column_name='Period')
    value = Field(attribute='value', column_name='Value')
    status = Field(attribute='status', column_name='Approval Status')

    class Meta:
        model = StgHealthWorkforceFacts
        skip_unchanged = False
        report_skipped = False
        fields = ('location_name','cadre_name','categoryoption_name',
            'datasource','measuremethod','period','value','status',)


class HealthCadreResourceExport(resources.ModelResource):
    cadre_name = Field(attribute='name', column_name='Cadre Name')
    cadre_code= Field(attribute='code', column_name='Theme Code')
    academic = Field(attribute='academic', column_name='Qualifications')
    description = Field(attribute='description', column_name='Description')
    parent = Field(attribute='parent', column_name='Parent')

    class Meta:
        model = StgHealthCadre
        skip_unchanged = False
        report_skipped = False
        fields = ('cadre_name','cadre_code','academic', 'description','parent',)


class TrainingInstitutionResourceExport (resources.ModelResource):
    institution_name = Field(attribute='name', column_name='Institution Name')
    Institution_code = Field(attribute='code', column_name='Institution Code')
    faculty = Field(attribute='faculty', column_name='Health Faculty')
    accreditation = Field(attribute='accreditation',
        column_name='Accreditation Status')
    regulator = Field(attribute='regulator',column_name='Regulating Agency',)
    language = Field(attribute='language',column_name='Teaching Language') # to debug
    institution_type = Field(attribute='type',column_name='Institution Type')
    location = Field(attribute='location', column_name='Country')
    latitude = Field(attribute='latitude', column_name='Latitude')
    longitude = Field(attribute='latitude', column_name='Latitude')
    url = Field(attribute='url', column_name='Web Adddress (URL)')

    class Meta:
        model = StgTrainingInstitution
        skip_unchanged = False
        report_skipped = False
        fields = ('institution_name','Institution_code','faculty','accreditation',
            'regulator','language','institution_type','location','latitude',
            'longitude','url',)


class HealthWorkforceProductResourceExport (resources.ModelResource):
    title = Field(attribute='title', column_name='Resource Name')
    code = Field(attribute='code', column_name='Resource Code')
    type = Field(attribute='type', column_name='Resource Type')
    categorization = Field(attribute='categorization',
        column_name='Reseource Categorization',)
    location = Field(attribute='location__name', column_name='Location Name')
    author = Field(attribute='author', column_name='Author')
    year_published = Field(attribute='year_published', column_name='Year Published')
    external_url = Field(attribute='external_url', column_name='Hyperlink (URL)')


    class Meta:
        model = HumanWorkforceResourceProxy
        skip_unchanged = False
        report_skipped = False
        fields = ('code','title','type','categorization','location','author',
            'year_published','external_url',)
