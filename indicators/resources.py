from import_export import resources
from import_export.fields import Field
from .models import (FactDataIndicator, StgIndicator, StgIndicatorDomain,
    aho_factsindicator_archive,StgNarrative_Type,StgIndicatorNarrative,
    StgAnalyticsNarrative,AhoDoamain_Lookup,)
from home.models import StgCategoryoption,StgDatasource,StgMeasuremethod
from regions.models import StgLocation
from import_export.widgets import ForeignKeyWidget, DateWidget
from django.utils import translation


class TranslatedNameForeignKeyWidget(ForeignKeyWidget):
    """Resolve Parler translated objects from the visible name used in import files."""

    def __init__(self, model, *args, **kwargs):
        super().__init__(model, 'translations__name', *args, **kwargs)

    def clean(self, value, row=None, **kwargs):
        if value is None or value == '':
            return None

        language = (translation.get_language() or 'en').split('-', 1)[0]
        queryset = self.model.objects.filter(
            translations__name=str(value).strip(),
            translations__language_code=language,
        )
        if not queryset.exists():
            queryset = self.model.objects.filter(translations__name=str(value).strip())
        return queryset.distinct().get()

# This class requires the methods for saving the instance to be overriden
class IndicatorFactsResourceImport(resources.ModelResource):
    def before_save_instance(
        self, instance, using_transactions, dry_run):
        # Called with dry_run=True to ensure no records are saved
        save_instance(
            instance, using_transactions=True, dry_run=True)

    def get_instance(self, instance_loader, row):
        return False  # To override the need for the id in the import file

    def save_instance(self, instance, using_transactions=True, dry_run=False):
            if dry_run:
                pass
            else:
                instance.save()
    indicator_name = Field(column_name='Indicator Name',attribute='indicator',
        widget=TranslatedNameForeignKeyWidget(StgIndicator))
    location_name = Field(column_name='Location Name',attribute='location',
        widget=TranslatedNameForeignKeyWidget(StgLocation))
    categoryoption_name = Field(column_name='Disaggregation Option',
        attribute='categoryoption',widget=TranslatedNameForeignKeyWidget(
        StgCategoryoption))
    datasource = Field( column_name='Data Source',attribute='datasource',
        widget=TranslatedNameForeignKeyWidget(StgDatasource))
    measuremethod = Field( column_name='Data Value Type',attribute='measuremethod',
        widget=TranslatedNameForeignKeyWidget(StgMeasuremethod))
    start_period = Field(column_name='Start Period', attribute='start_period',)
    end_period = Field(column_name='End Period', attribute='end_period',)
    value_received = Field(column_name='Value',attribute='value_received',)
    target_value = Field(column_name='Target Value',attribute='target_value',)
    string_value = Field(column_name='String Value',attribute='string_value',)

    class Meta:
        model = FactDataIndicator
        skip_unchanged = False
        report_skipped = False
        fields = ('indicator_name','location_name','categoryoption_name',
            'datasource','measuremethod','start_period','end_period',
            'value_received','target_value','string_value',)


class IndicatorFactsResourceExport(resources.ModelResource):
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
    period = Field(attribute='period', column_name='Period')
    value_received = Field(attribute='value_received',
        column_name='Numeric Value')
    target_value = Field(attribute='target_value', column_name='Target Measure')
    datasource = Field(attribute='datasource', column_name='Data Source')
    valuetype = Field(attribute='valuetype', column_name='Data Type')
    string_value = Field(attribute='string_value',
        column_name='String Value [Remarks]')
    comment = Field(attribute='comment', column_name='Approval Status')

    class Meta:
        model = FactDataIndicator
        skip_unchanged = False
        report_skipped = False
        fields = ('location__name','location__code','indicator__name',
            'indicator__afrocode','categoryoption__code','categoryoption__name',
            'period','value_received','target_value','datasource','valuetype',
            'comment','string_value',)


class IndicatorResourceExport(resources.ModelResource):
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
    reference = Field(attribute='reference', column_name='Indicator Reference')


    class Meta:
        model = StgIndicator
        skip_unchanged = False
        report_skipped = False
        fields = ('indicator_name','afrocode','shortname','preferred_datasources',
            'numerator_description','denominator_description','reference',)

class AchivedIndicatorResourceExport(resources.ModelResource):
    location__name = Field(attribute='location__name', column_name='Location')
    location__code = Field(attribute='location__code', column_name='Location Code')
    indicator__name = Field(attribute='indicator__name', column_name='Indicator')
    indicator__afrocode = Field(
        attribute='indicator__afrocode', column_name='Indicator Code')
    categoryoption__name = Field(
        attribute='categoryoption__name', column_name='Disaggregation')
    period = Field(attribute='period', column_name='Period')
    value_received = Field(attribute='value_received', column_name='Numeric Value')
    datasource = Field(attribute='datasource', column_name='Data Source')
    string_value = Field(attribute='string_value', column_name='String Value')
    comment = Field(attribute='comment', column_name='Approval Status')

    class Meta:
        model = aho_factsindicator_archive
        skip_unchanged = False
        report_skipped = False
        fields = ('location__name','location__code','indicator__name',
            'indicator__afrocode','categoryoption__name','period',
            'value_received','datasource','string_value','comment')


class DomainResourceImport(resources.ModelResource): #to be worked on!
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
    domain_code= Field(attribute='code', column_name='Domain Code')
    domain_name = Field(attribute='name', column_name='Data Element Name')
    shortname = Field(attribute='shortname', column_name='Short Name')
    description = Field(attribute='description', column_name='Description')

    class Meta:
        model = StgIndicatorDomain
        skip_unchanged = False
        report_skipped = False
        fields = ('domain_code','domain_name', 'shortname', 'description',)


class DomainResourceExport(resources.ModelResource):
    domain_name = Field(attribute='name', column_name='Theme/Domain Name')
    domain_code= Field(attribute='code', column_name='Theme Code')
    shortname = Field(attribute='shortname', column_name='Short Name')
    description = Field(attribute='description', column_name='Description')
    parent = Field(attribute='parent', column_name='Parent')
    level = Field(attribute='level', column_name='Level')

    class Meta:
        model = StgIndicatorDomain
        skip_unchanged = False
        report_skipped = False
        fields = ('domain_name','domain_code','shortname', 'description',
            'parent','level',)

class NarrativeTypeResourceExport(resources.ModelResource):
    narrative_type = Field(attribute='name', column_name='Narrative Type')
    narrative_code= Field(attribute='code', column_name='Code')
    shortname = Field(attribute='shortname', column_name='Short Name')
    description = Field(attribute='description', column_name='Description')

    class Meta:
        model = StgNarrative_Type
        skip_unchanged = False
        report_skipped = False
        fields = ('narrative_type','narrative_code', 'shortname','description',)

class IndicatorNarrativeResourceExport(resources.ModelResource):
    narrative_type = Field(attribute='narrative_type__name',
        column_name='Narrative Type')
    indicator = Field(attribute='indicator__name', column_name='Indicator')
    location = Field(attribute='location__name', column_name='Location')
    narrative_text = Field(attribute='narrative_text',
        column_name='Narrative Text')

    class Meta:
        model = StgIndicatorNarrative
        skip_unchanged = False
        report_skipped = False
        fields = ('narrative_type','indicator','location','narrative_text',)

class ThematicNarrativeResourceExport(resources.ModelResource):
    narrative_type = Field(attribute='narrative_type__name',
        column_name='Narrative Type')
    domain= Field(attribute='domain__name', column_name='Theme')
    location = Field(attribute='location__name', column_name='Location')
    narrative_text = Field(attribute='narrative_text',
        column_name='Narrative Text')

    class Meta:
        model = StgAnalyticsNarrative
        skip_unchanged = False
        report_skipped = False
        fields = ('narrative_type','domain','location','narrative_text',)

class DomainLookupResourceExport(resources.ModelResource):
    indicator_name = Field(attribute='indicator_name', column_name='Theme Name')
    indicator_code= Field(attribute='code', column_name='Theme Code')
    domain = Field(attribute='domain_name', column_name='Short Name')
    level = Field(attribute='domain_level', column_name='Level')

    class Meta:
        model = AhoDoamain_Lookup
        skip_unchanged = False
        report_skipped = False
        fields = ('indicator_name','indicator_code', 'domain','level',)
