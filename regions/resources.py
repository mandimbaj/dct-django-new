from import_export import resources
from import_export.fields import Field
from .models import (StgLocationLevel, StgWorldbankIncomegroups, StgEconomicZones,
    StgSpecialcategorization,StgLocation)
from import_export.widgets import ForeignKeyWidget

class LocationResourceExport (resources.ModelResource):
    location_name = Field(attribute='name', column_name='Location Name')
    code = Field(attribute='code', column_name='Location Code')
    level = Field(attribute='locationlevel__name', column_name='Location Level')
    longitude = Field(attribute='longitude', column_name='Longitude')
    latitude = Field(attribute='latitude', column_name='Latitude')
    wb_incomegroup = Field(attribute='wb_incomeid', column_name='Economic Status')
    economic_zone = Field(attribute='zone', column_name='Economic Zone')
    special_state = Field(attribute='special', column_name='State Categorization')

    class Meta:
        model = StgLocation
        skip_unchanged = False
        report_skipped = False
        fields = ('code','location_name','level', 'longitude','latitude',
            'wb_incomegroup','economic_zone','special_state',)


class LocationResourceImport (resources.ModelResource):
    def before_save_instance(
        self, instance, using_transactions, dry_run):
        save_instance( # Called with dry_run=True to ensure no records are saved
            instance, using_transactions=True, dry_run=True)

    def get_instance(self, instance_loader, row):
        return False  # To override the need for the id in the import file

    def save_instance( # Called when you click confirm to the interface
        self, instance, using_transactions=True, dry_run=False):
        if dry_run:
            pass
        else:
            instance.save()
    #to be worked on
    location_name = Field(attribute='name', column_name='Location Name',)
    code = Field(attribute='code', column_name='Location Code',)
    level = Field(attribute='locationlevel', column_name='Location Level',
        widget=ForeignKeyWidget(StgLocationLevel, 'code'))

    iso_apha = Field(attribute='iso_apha', column_name='ISO Alpha')
    iso_number = Field(attribute='iso_number', column_name='ISO Numeric')

    description = Field(attribute='description', column_name='Description',)

    latitude = Field(attribute='latitude', column_name='Latitude')
    longitude = Field(attribute='longitude', column_name='Longitude')

    wb_incomegroup = Field(attribute='wb_incomeid', column_name='Economic Status',
        widget=ForeignKeyWidget(StgWorldbankIncomegroups, 'code'))
    economic_zone = Field(attribute='zone', column_name='Economic Zone',
        widget=ForeignKeyWidget(StgEconomicZones, 'code'))
    special_state = Field(attribute='special', column_name='State Categorization',
        widget=ForeignKeyWidget(StgSpecialcategorization, 'code'))

    class Meta:
        model = StgLocation
        skip_unchanged = False
        report_skipped = False
        fields = ('location_name','code','level','iso_apha','iso_number',
            'description','latitude','longitude','wb_incomegroup',
            'economic_zone','special_state',)


class LocationLevelResourceExport (resources.ModelResource):
    level_name = Field(attribute='name', column_name='Location Name')
    code = Field(attribute='code', column_name='Level Code')
    level_type = Field(attribute='type', column_name='Type')
    description = Field(attribute='latitude', column_name='Latitude')

    class Meta:
        model = StgLocationLevel
        skip_unchanged = False
        report_skipped = False
        fields = ('level_name','code','level_type', 'description',)


class IncomegroupsResourceExport (resources.ModelResource):
    income_group = Field(attribute='name', column_name='Income Level Name')
    code = Field(attribute='code', column_name='Income Level Code')
    shortname = Field(attribute='shortname', column_name='Short Name')
    description = Field(attribute='latitude', column_name='Description')

    class Meta:
        model = StgLocationLevel
        skip_unchanged = False
        report_skipped = False
        fields = ('income_group','code','shortname', 'description',)


class EconomicZoneResourceExport (resources.ModelResource):
    economic_zone = Field(attribute='name', column_name='Economic Block Name')
    code = Field(attribute='code', column_name='Economic Block Code')
    shortname = Field(attribute='shortname', column_name='Short Name')
    description = Field(attribute='latitude', column_name='Description')

    class Meta:
        model = StgEconomicZones
        skip_unchanged = False
        report_skipped = False
        fields = ('economic_zone','code','shortname', 'description',)

class SpecialcategorizationResourceExport (resources.ModelResource):
    state = Field(attribute='name', column_name='Special Category Name')
    code = Field(attribute='code', column_name='Special Category Code')
    shortname = Field(attribute='shortname', column_name='Short Name')
    description = Field(attribute='latitude', column_name='Description')

    class Meta:
        model = StgSpecialcategorization
        skip_unchanged = False
        report_skipped = False
        fields = ('state','code','shortname', 'description',)
