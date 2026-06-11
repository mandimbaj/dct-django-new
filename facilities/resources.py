from import_export import resources
from import_export.fields import Field
from .models import (StgHealthFacility,StgFacilityType,StgServiceDomain,
    FacilityServiceAvailability,FacilityServiceProvision,
    FacilityServiceReadiness,)
from import_export.widgets import ForeignKeyWidget
from home.models import StgDatasource
from regions.models import StgLocation


class FacilityTypeResourceExport(resources.ModelResource):
    name = Field(attribute='name', column_name='Facility Type')
    code= Field(attribute='code', column_name='Code')
    shortname = Field(attribute='shortname', column_name='Short Name')
    description = Field(attribute='description', column_name='Description')

    class Meta:
        model = StgFacilityType
        skip_unchanged = False
        report_skipped = False
        fields = ('name','code','shortname', 'description',)


class FacilityServiceDomainResourceExport(resources.ModelResource):
    domain_name = Field(attribute='name', column_name='Service Domain')
    domain_code= Field(attribute='code', column_name='Code')
    shortname = Field(attribute='shortname', column_name='Short Name')
    description = Field(attribute='description', column_name='Description')
    category = Field(attribute='category', column_name='Service Category')
    parent = Field(attribute='parent', column_name='Parent')
    level = Field(attribute='level', column_name='Level')

    class Meta:
        model = StgServiceDomain
        skip_unchanged = False
        report_skipped = False
        fields = ('domain_name','domain_code','shortname', 'description',
            'category','parent','level',)


class StgFacilityServiceAvailabilityExport (resources.ModelResource):
    facility_name = Field(attribute='name', column_name='Facility Name')
    domain_name = Field(attribute='domain__name', column_name='Service Domain')
    intervention = Field(attribute='intervention__name',column_name='Inrevention Area',)
    service = Field(attribute='service__name',column_name='Service Area') # to debug
    provided = Field(attribute='provided',column_name='Service Provided Last 3 Months')
    specialunit = Field(attribute='specialunit',
        column_name='Specialized Unit Provided')
    staff = Field(attribute='staff', column_name='Staff Appropriate')
    infrastructure = Field(attribute='infrastructure',
        column_name='Infrastructure Appropriate')
    supplies = Field(attribute='supplies', column_name='Supplies Appropriate')

    class Meta:
        model = FacilityServiceAvailability
        skip_unchanged = False
        report_skipped = False
        fields = ('facility_name','domain_name','intervention','service',
            'provided','specialunit','staff','infrastructure','supplies',)


class StgFacilityServiceCapacityExport (resources.ModelResource):
    facility_name = Field(attribute='name', column_name='Facility Name')
    domain_name = Field(attribute='domain__name', column_name='Service Domain')
    units = Field(attribute='units__name',column_name='Units of Provision',)
    available = Field(attribute='available',column_name='Number Available')
    functional = Field(attribute='functional',column_name='Number Functional')
    date_assessed = Field(attribute='date_assessed', column_name='Assessment Date')

    class Meta:
        model = FacilityServiceProvision
        skip_unchanged = False
        report_skipped = False
        fields = ('facility_name','domain_name','units','service','available',
            'functional','date_assessed',)


class StgFacilityServiceReadinessExport (resources.ModelResource):
    facility_name = Field(attribute='name', column_name='Facility Name')
    domain_name = Field(attribute='domain__name', column_name='Service Domain')
    units = Field(attribute='units__name',column_name='Units of Provision',)
    available = Field(attribute='available',column_name='Number Available')
    require = Field(attribute='require',column_name='Number Required')
    date_assessed = Field(attribute='date_assessed', column_name='Assessment Date')

    class Meta:
        model = FacilityServiceReadiness
        skip_unchanged = False
        report_skipped = False
        fields = ('facility_name','domain_name','units','service','available',
            'require','date_assessed',)


class StgFacilityResourceExport (resources.ModelResource):
    facility_name = Field(attribute='name', column_name='Facility Name')
    facility_code = Field(attribute='code', column_name='Facility Code')
    facility_type = Field(attribute='type__name', column_name='Facility Type')
    facility_owner = Field(attribute='owner__name',column_name='Facility Ownership ',)
    location = Field(attribute='location__location__name',
        column_name='Country Name') # to debug
    admin_location = Field(attribute='admin_location',
        column_name='Administrative Location')
    description = Field(attribute='description', column_name='Description')
    latitude = Field(attribute='latitude', column_name='Latitude')
    longitude = Field(attribute='latitude', column_name='Latitude')
    geosource = Field(attribute='geosource', column_name='Geolocation Source')
    url = Field(attribute='url', column_name='Web Adddress (URL)')

    class Meta:
        model = StgHealthFacility
        skip_unchanged = False
        report_skipped = False
        fields = ('facility_name','facility_code','facility_type','facility_owner',
            'location','admin_location','description','latitude','longitude',
            'geosource','url',)


class StgFacilityResourceImport (resources.ModelResource):
    def before_save_instance(
        self, instance, using_transactions, dry_run):
        save_instance( # Called with dry_run=True to ensure no records are saved
            instance, using_transactions=True, dry_run=True)

    def get_instance(self, instance_loader, row):
        return False  # To override the need for the id in the import file

    # Called when you click confirm to the interface
    def save_instance(self, instance, using_transactions=True, dry_run=False):
        if dry_run:
            pass
        else:
            #import pdb; pdb.set_trace()
            instance.save()

    code = Field( column_name='Resource Code', attribute='code',)
    title = Field(column_name='Title', attribute='title')
    type = Field(column_name='Reseource Type', attribute='type')
    categorization = Field(column_name='Reseource Categorization',
        attribute='categorization')
    location_code = Field(column_name='Location Code',attribute='location_code',
        widget=ForeignKeyWidget(StgLocation, 'code'))
    location_name = Field( # Define the location name but exclude it in processing the file
        column_name='Location Name',
        attribute='location',
        widget=ForeignKeyWidget(StgLocation, 'name'))
    repository = Field(
        column_name=' Reference Name',
        attribute='repository',
        widget=ForeignKeyWidget(StgDatasource, 'code'))
    description = Field(
        column_name='Description', attribute='description')
    abstract = Field(column_name='Abstract', attribute='abstract')
    author = Field(column_name='Author(s)', attribute='author')
    year_published = Field(column_name='Year', attribute='year_published')
    external_url = Field(column_name='External Link', attribute='external_url')

    class Meta:
        model = StgHealthFacility
        skip_unchanged = False
        report_skipped = False
        fields = ('code','title','type','categorization','location_code',
            'location_name','repository','description','abstract','author',
            'year_published','external_url', )
