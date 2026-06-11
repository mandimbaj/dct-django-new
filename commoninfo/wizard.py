from django.shortcuts import get_object_or_404
import data_wizard
from django.conf import settings # allow import of projects settings at the root
from django.utils import translation

from rest_framework.serializers import (HyperlinkedModelSerializer,
    ModelSerializer, ReadOnlyField, DecimalField,PrimaryKeyRelatedField,
    )

from facilities.models import StgHealthFacility
from indicators.models import FactDataIndicator
from health_workforce.models import StgHealthWorkforceFacts,StgHealthCadre
from health_services.models import HealthServices_DataIndicators
from elements.models import FactDataElement
from authentication.models import CustomUser # for filtering logged in instances

from indicators.models import (StgIndicator, FactDataIndicator,)
from home.models import StgCategoryoption, StgDatasource,StgMeasuremethod # added 07/02/2023
from regions.models import StgLocation
from authentication.models import CustomUser # for filtering logged in instances


def active_language_code():
    return (translation.get_language() or settings.LANGUAGE_CODE).split("-", 1)[0]


def indicator_queryset(language):
    return StgIndicator.objects.select_related('reference').prefetch_related(
        'translations__master').filter(translations__language_code=language)


def location_queryset(language):
    return StgLocation.objects.select_related(
        'locationlevel','parent','wb_income','special').prefetch_related(
        'wb_income__translations','translations__master').order_by(
        'locationlevel','translations__name').filter(
            translations__language_code=language)


def categoryoption_queryset(language):
    return StgCategoryoption.objects.select_related('category').prefetch_related(
        'translations__master').filter(translations__language_code=language)


def datasource_queryset(language):
    return StgDatasource.objects.prefetch_related(
        'translations__master').order_by('translations__name').filter(
            translations__language_code=language)


def measuremethod_queryset(language):
    return StgMeasuremethod.objects.prefetch_related(
        'translations__master').order_by('translations__name').filter(
            translations__language_code=language)


def cadre_queryset(language):
    return StgHealthCadre.objects.select_related('parent').prefetch_related(
        'translations__master').filter(translations__language_code=language)



"""
This custom srializer class creates facility instance based on the logged user.
To make this posssible, the user foreign key must made read-only.This behaviour
successfuly was implemented on 27/09/2021 after 2 weeks of struggling.
"""
class DataWizardFacilitySerializer(ModelSerializer):
    # location_name = ReadOnlyField(source='location.location.name')

    """
    Fetch id of logged user supplied via data_wizard run contect.This issue
    was resolved after 3 weeks of intense efforts until I read Dejmail issue
    posted on https://githubmemory.com/repo/wq/django-data-wizard/issues/32
    """
    def process_foreign_keys(self, validated_data):
        # Try direct access to logged user id supplied via API clients
        user = self.context.get('data_wizard').get('run').user.id # magic solution
        user = get_object_or_404(CustomUser,id=user) # create filter based on user id
        validated_data['user'] = user # assign user id to validated data user key
        return validated_data # Now pass clean data to the overriden create() method

    def create(self, validated_data):
        # Create a facility instance based after receiving validated data
        validated_data = self.process_foreign_keys(validated_data)
        return StgHealthFacility.objects.create(**validated_data)

    class Meta:
        model = StgHealthFacility
        read_only_fields = ('user',) # Disable user get from logged user instance
        fields = ('uuid','code','type','location','owner','name','shortname',
                  'admin_location', 'description','latitude',
                  'longitude','altitude','geosource','url','status','user')

        data_wizard = {
        'header_row': 0,
        'start_row': 1,
        'show_in_list': True,
        'idmap': data_wizard.idmap.existing,
    }


class RoundedDecimalField(DecimalField):
    def validate_precision(self, value):
        return value

"""
Custom serializer class for importing indicator data using django-data-wizard.
We override decimal field to ignore decimal places and required validation rule
"""
class DataWizardFactIndicatorSerializer(ModelSerializer): # to replace hardcoded lenguage selection later
    language = settings.LANGUAGE_CODE # fallback until the request language is available
    
    indicator = PrimaryKeyRelatedField(
        label='Indicator Name', queryset=indicator_queryset(language), required=True)
    
    location = PrimaryKeyRelatedField(
        label='Location Name', queryset=location_queryset(language), required=True)
    
    categoryoption = PrimaryKeyRelatedField(
        label='Disaggregation Options', queryset=categoryoption_queryset(language),
          required=False)
    
    datasource = PrimaryKeyRelatedField(
        label='Data Source', queryset=datasource_queryset(language), required=True)
    
    measuremethod = PrimaryKeyRelatedField(
        label='Measure Type', queryset=measuremethod_queryset(language),required=True)
    
    numerator_value = RoundedDecimalField(
        max_digits=20,decimal_places=3,required=False,allow_null=True)
    denominator_value = RoundedDecimalField(
        max_digits=20, decimal_places=3,required=False,allow_null=True)
    value_received = RoundedDecimalField(
        max_digits=20, decimal_places=3,required=True,allow_null=False)
    min_value = RoundedDecimalField(
        max_digits=20,decimal_places=3,required=False,allow_null=True)
    max_value = RoundedDecimalField(
        max_digits=20, decimal_places=3,required=False,allow_null=True)
    target_value = RoundedDecimalField(
        max_digits=20, decimal_places=3,required=False,allow_null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        language = active_language_code()
        self.fields['indicator'].queryset = indicator_queryset(language)
        self.fields['location'].queryset = location_queryset(language)
        self.fields['categoryoption'].queryset = categoryoption_queryset(language)
        self.fields['datasource'].queryset = datasource_queryset(language)
        self.fields['measuremethod'].queryset = measuremethod_queryset(language)

    
    """
    Fetch id of logged user supplied via data_wizard run context.This issue
    was resolved after 3 weeks of intense efforts until I read Dejmail issue
    posted on https://githubmemory.com/repo/wq/django-data-wizard/issues/32
    """
    def process_foreign_keys(self, validated_data):
        # Try direct access to logged user id supplied via API clients
        user = self.context.get('data_wizard').get('run').user.id # magic solution
        user = get_object_or_404(CustomUser,id=user) # create filter based on user id
        validated_data['user'] = user # assign user id to validated data user key
        return validated_data # Now pass clean data to the overriden create() method

    def create(self, validated_data):
        # Create a facility instance based after receiving validated data
        validated_data = self.process_foreign_keys(validated_data)
        return FactDataIndicator.objects.create(**validated_data)

    class Meta:
        model = FactDataIndicator
        fields = [
            'indicator','location','categoryoption','datasource','measuremethod',
            'numerator_value','denominator_value','value_received','min_value',
            'max_value','target_value','string_value','start_period','end_period',
            'period',]

        data_wizard = {
            'header_row': 0,
            'start_row': 1,
            'show_in_list': True,
        }


"""
This custom srializer class that creates that health workforce instance based on
logged user.To make this posssible, the user foreign key must made read-only.
This behaviour was successfuly was implemented on 28/09/2021.
"""
class DataWizardWorkforceFactsSerializer(ModelSerializer):
    cadre = PrimaryKeyRelatedField(
        label='Occupation Type', queryset=cadre_queryset(settings.LANGUAGE_CODE),
        required=True)
    
    location = PrimaryKeyRelatedField(
        label='Location Name', queryset=location_queryset(settings.LANGUAGE_CODE),
        required=True)
    
    categoryoption = PrimaryKeyRelatedField(
        label='Disaggregation Options',
        queryset=categoryoption_queryset(settings.LANGUAGE_CODE), required=False)
    
    datasource = PrimaryKeyRelatedField(
        label='Data Source', queryset=datasource_queryset(settings.LANGUAGE_CODE),
        required=True)
    
    measuremethod = PrimaryKeyRelatedField(
        label='Measure Type', queryset=measuremethod_queryset(settings.LANGUAGE_CODE),
        required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        language = active_language_code()
        self.fields['cadre'].queryset = cadre_queryset(language)
        self.fields['location'].queryset = location_queryset(language)
        self.fields['categoryoption'].queryset = categoryoption_queryset(language)
        self.fields['datasource'].queryset = datasource_queryset(language)
        self.fields['measuremethod'].queryset = measuremethod_queryset(language)
    
    """
    Fetch id of logged user supplied via data_wizard run context.This issue
    was resolved after 3 weeks of intense efforts until I read Dejmail issue
    posted on https://githubmemory.com/repo/wq/django-data-wizard/issues/32
    """
    def process_foreign_keys(self, validated_data):
        # Try direct access to logged user id supplied via API clients
        user = self.context.get('data_wizard').get('run').user.id # magic solution
        user = get_object_or_404(CustomUser,id=user) # create filter based on user id
        validated_data['user'] = user # assign user id to validated data user key
        return validated_data # Now pass clean data to the overriden create() method

    def create(self, validated_data):
        # Create a facility instance based after receiving validated data
        validated_data = self.process_foreign_keys(validated_data)
        return StgHealthWorkforceFacts.objects.create(**validated_data)


    class Meta:
        model = StgHealthWorkforceFacts

        fields = ('cadre','location','categoryoption','datasource','measuremethod',
                  'value', 'start_year','end_year','period','status',)

        data_wizard = {
        'header_row': 0,
        'start_row': 1,
        'show_in_list': True,
    }


"""
Custom serializer class for importing data elements using django-data-wizard.We
override decimal field to ignore decimal places and required validation rule.
"""
# Force import wizard to ignore the decimal places and required validation to allow null
class DataWizardElementSerializer(ModelSerializer,):
    location_name = ReadOnlyField(source='location.name')
    value = RoundedDecimalField(
        max_digits=20, decimal_places=3,required=True,allow_null=False)
    target_value = RoundedDecimalField(
        max_digits=20,decimal_places=3,required=False,allow_null=True)

    """
    Fetch id of logged user supplied via data_wizard run contect.This issue
    was resolved after 3 weeks of intense efforts until I read Dejmail issue
    posted on https://githubmemory.com/repo/wq/django-data-wizard/issues/32
    """
    def process_foreign_keys(self, validated_data):
        # Try direct access to logged user id supplied via API clients
        user = self.context.get('data_wizard').get('run').user.id # magic solution
        user = get_object_or_404(CustomUser,id=user) # create filter based on user id
        validated_data['user'] = user # assign user id to validated data user key
        return validated_data # Now pass clean data to the overriden create() method

    def create(self, validated_data):
        # Create a facility instance based after receiving validated data
        validated_data = self.process_foreign_keys(validated_data)
        return FactDataElement.objects.create(**validated_data)

    class Meta:
        model = FactDataElement
        fields = [
            'uuid','fact_id','dataelement','location','location_name',
            'categoryoption','datasource','valuetype','value','target_value',
            'start_year','end_year','period','comment']

        data_wizard = {
        'header_row': 0,
        'start_row': 1,
        'show_in_list': True,
    }


# Force import wizard to ignore the decimal places and required validation to allow null
class DataWizardHealthServicesFactSerializer(ModelSerializer):
    location_name = ReadOnlyField(source='location.name')
    numerator_value = RoundedDecimalField(
        max_digits=20,decimal_places=3,required=False,allow_null=True)
    denominator_value = RoundedDecimalField(
        max_digits=20, decimal_places=3,required=False,allow_null=True)
    value_received = RoundedDecimalField(
        max_digits=20, decimal_places=3,required=True,allow_null=False)
    min_value = RoundedDecimalField(
        max_digits=20,decimal_places=3,required=False,allow_null=True)
    max_value = RoundedDecimalField(
        max_digits=20, decimal_places=3,required=False,allow_null=True)
    target_value = RoundedDecimalField(
        max_digits=20, decimal_places=3,required=False,allow_null=True)

    def process_foreign_keys(self, validated_data):
        # Gets the id of logged in user to be supplied to the user foreign key
        user = self.context.get('data_wizard').get('run').user.id # magic solution
        user = get_object_or_404(CustomUser,id=user)
        validated_data['user'] = user
        return validated_data

    def create(self, validated_data):
        # Create a Facility instance routed from POST via DRF's serializer """
        validated_data = self.process_foreign_keys(validated_data)
        return HealthServices_DataIndicators.objects.create(**validated_data)

    class Meta:
        model = HealthServices_DataIndicators
        fields = [
            'uuid','fact_id','indicator', 'location','location_name','categoryoption',
            'datasource','measuremethod','numerator_value','denominator_value',
            'value_received','value_calculated','min_value','max_value','target_value',
            'periodicity','start_period','end_period','period',]

        data_wizard = {
            'header_row': 0,
            'start_row': 1,
            'show_in_list': True,
        }
