from import_export import resources
from import_export.fields import Field
from .models import (HealthServicesProgrammes, HealthServices_DataIndicators,
    HealthServicesIndicators,HSCPrograms_Lookup)
from home.models import StgCategoryoption,StgDatasource,StgValueDatatype
from regions.models import StgLocation
from import_export.widgets import ForeignKeyWidget, DateWidget


class HSCFactsResourceExport(resources.ModelResource):
    location__name = Field(attribute='location__name', column_name='Location')
    location__code = Field(attribute='location__code',
        column_name='Location Code')
    indicator__name = Field(attribute='indicator__name',
        column_name='Indicator Name')
    indicator__afrocode = Field(attribute='indicator__afrocode',
        column_name='Code')
    categoryoption__code = Field(attribute='categoryoption__code',
        column_name='Disaggregation Code')
    categoryoption__name = Field(attribute='categoryoption__name',
        column_name='Disaggregation Type')
    periodicity = Field(attribute='periodicity',column_name='Periodicity')
    period = Field(attribute='period', column_name='Period')
    value_received = Field(attribute='value_received',column_name='Value')
    target_value = Field(attribute='target_value', column_name='Target Measure')
    datasource = Field(attribute='datasource', column_name='Data Source')
    valuetype = Field(attribute='valuetype', column_name='Data Type')
    comment = Field(attribute='comment', column_name='Approval Status')

    class Meta:
        model = HealthServices_DataIndicators
        skip_unchanged = False
        report_skipped = False
        fields = ('location__name','location__code','indicator__name',
            'indicator__afrocode','categoryoption__code','categoryoption__name',
            'periodicity','period','value_received','target_value','datasource',
            'valuetype','comment',)


class HSCIndicatorResourceExport(resources.ModelResource):
    indicator_name = Field(attribute='name', column_name='Data Element Name')
    afrocode = Field(attribute='afrocode', column_name='Indicator Code')
    shortname = Field(attribute='shortname', column_name='Short Name')
    # definition = Field(attribute='definition', column_name='Definition')
    preferred_datasources= Field(attribute='preferred_datasources',
        column_name='Description')
    numerator_description = Field(attribute='numerator_description',
        column_name='Numerator description')
    denominator_description = Field(attribute='denominator_description',
        column_name='Denominator description')


    class Meta:
        model = HealthServicesIndicators
        skip_unchanged = False
        report_skipped = False
        fields = ('indicator_name','afrocode','shortname','preferred_datasources',
            'numerator_description','denominator_description',)


class HSCProgrammesResourceExport(resources.ModelResource):
    program_name = Field(attribute='name', column_name='Theme/Domain Name')
    program_code= Field(attribute='code', column_name='Theme Code')
    shortname = Field(attribute='shortname', column_name='Short Name')
    description = Field(attribute='description', column_name='Description')
    parent = Field(attribute='parent', column_name='Parent')
    level = Field(attribute='level', column_name='Level')

    class Meta:
        model = HealthServicesProgrammes
        skip_unchanged = False
        report_skipped = False
        fields = ('program_name','program_code','shortname', 'description',
            'parent','level',)


class HSCDomainLookupResourceExport(resources.ModelResource):
    indicator_name = Field(attribute='indicator_name', column_name='Indicator Name')
    indicator_code= Field(attribute='code', column_name='Indicator Code')
    program_name = Field(attribute='program_name', column_name='Program Name')
    level = Field(attribute='level', column_name='Level')

    class Meta:
        model = HSCPrograms_Lookup
        skip_unchanged = False
        report_skipped = False
        fields = ('indicator_name','indicator_code', 'program_name','level',)
