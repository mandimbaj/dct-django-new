from django.contrib import admin
from django import forms
from django.conf import settings # allow import of projects settings at the root
from django.utils.translation import gettext_lazy as _
from django.forms import BaseInlineFormSet,ValidationError
from parler.admin import (TranslatableAdmin,TranslatableStackedInline,
    TranslatableInlineModelAdmin)
import data_wizard # Solution to data import madness that had refused to go
from itertools import groupby #additional import for managing grouped dropdowm
from import_export.admin import (ImportExportModelAdmin,ExportMixin,
    ExportActionMixin,ImportMixin,ImportExportActionModelAdmin,
    ExportActionModelAdmin,)
from django_admin_listfilter_dropdown.filters import (
    DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter,
    RelatedOnlyDropdownFilter) #custom
from django.contrib.admin.views.main import ChangeList
from indicators.serializers import FactDataIndicatorSerializer
from django.forms.models import ModelChoiceField, ModelChoiceIterator
from .models import (StgIndicatorReference,StgIndicator,StgIndicatorDomain,
    FactDataIndicator,IndicatorProxy,AhoDoamain_Lookup,aho_factsindicator_archive,
    StgNarrative_Type,StgAnalyticsNarrative,StgIndicatorNarrative,
    NHOCustomizationProxy,NHOCustomFactsindicator,NHOCustomizationIcons)
from django.forms import TextInput,Textarea # customize textarea row and column size
from commoninfo.admin import (OverideImportExport,OverideExport,OverideImport,)
from .resources import (IndicatorFactsResourceExport,IndicatorFactsResourceImport,
    AchivedIndicatorResourceExport,DomainResourceExport,IndicatorResourceExport,
    NarrativeTypeResourceExport,ThematicNarrativeResourceExport,
    IndicatorNarrativeResourceExport,DomainLookupResourceExport,)
from commoninfo.fields import RoundingDecimalFormField # For fixing rounded decimal
from regions.models import StgLocation,StgLocationLevel
from authentication.models import CustomUser, CustomGroup
from home.models import ( StgDatasource,StgCategoryoption,StgMeasuremethod)
from .filters import TranslatedFieldFilter #Danile solution to duplicate filters

from commoninfo.wizard import DataWizardFactIndicatorSerializer
from django.db.models import Case, When
from django.urls import path

from commoninfo.admin_filters import  (
    LocationFilter,IndicatorsFilter,DatasourceFilter,
    CategoryOptionFilter) # added 1/2/2023
from regions.views import LocationSearchView
from indicators.views import IndicatorSearchView
from home.views import CategoryOptionSearchView,DataourceSearchView


#These 3 functions are used to register global actions performed on the data.
def transition_to_pending (modeladmin, request, queryset):
    queryset.update(comment = 'pending')
transition_to_pending.short_description = "Mark selected as Pending"

def transition_to_approved (modeladmin, request, queryset):
    queryset.update (comment = 'approved')
transition_to_approved.short_description = "Mark selected as Approved"

def transition_to_rejected (modeladmin, request, queryset):
    queryset.update (comment = 'rejected')
transition_to_rejected.short_description = "Mark selected as Rejected"


class GroupedModelChoiceIterator(ModelChoiceIterator):
    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)
        if self.field.cache_choices:
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    (self.field.group_label(group),[self.choice(ch) for ch in choices])
                        for group,choices in groupby(self.queryset.all(),
                            key=lambda row: getattr(row, self.field.group_by_field))
                ]
            for choice in self.field.choice_cache:
                yield choice
        else: # I refactored this code on 01/02/2023 to optimize query that reduced it from 579 to just 26 queries
            for group, choices in groupby(self.queryset.select_related( # select related replaced .all()
                'category').prefetch_related('category__translations',
                'translations__master').order_by(
                'category__translations__name','translations__name'),
	        key=lambda row: getattr(row, self.field.group_by_field)):
                    yield (self.field.group_label(group),
                        [self.choice(ch) for ch in choices])


class GroupedModelChoiceField(ModelChoiceField):
    def __init__(
        self, group_by_field, group_label=None, cache_choices=False,
        *args, **kwargs):
        """
        group_by_field is the name of a field on the model
        group_label is a function to return a label for each choice group
        """
        super(GroupedModelChoiceField, self).__init__(*args, **kwargs)
        self.group_by_field = group_by_field
        self.cache_choices = cache_choices
        if group_label is None:
            self.group_label = lambda group: group
        else:
            self.group_label = group_label

    def _get_choices(self):
        """
        Exactly as per ModelChoiceField except returns new iterator class
        """
        if hasattr(self, '_choices'):
            return self._choices
        return GroupedModelChoiceIterator(self)
    choices = property(_get_choices, ModelChoiceField.choices.fset)


@admin.register(StgIndicatorReference)
class IndicatorRefAdmin(TranslatableAdmin):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        return qs


    fieldsets = (
        ('Reference Attributes', {
                'fields': ('name','shortname',)
            }),
            ('Description', {
                'fields': ('description',),
            }),
        )
    list_display=['name','code','shortname','description',]
    list_display_links = ('code', 'name',)
    search_fields = ('code','translations__name','translations__shortname',)
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated',)


@admin.register(StgIndicator)
class IndicatorAdmin(TranslatableAdmin,OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        return qs

    # Format date created to disply only the day, month and year
    def date_created (obj):
        return obj.date_created.strftime("%d-%b-%Y")
    date_created.admin_order_field = 'date_created'
    date_created.short_description = 'Date Created'


    fieldsets = (
        ('Primary Attributes', {
                'fields': ('name','shortname','definition','reference')
            }),
            ('Secondary Attributes', {
                'fields': ('numerator_description','denominator_description',
                'preferred_datasources',),
            }),
        )
    resource_class = IndicatorResourceExport
    # actions = ExportActionModelAdmin.actions
    list_select_related = ('reference',)
    list_display=['name','afrocode','shortname','reference',date_created,]
    list_display_links = ('afrocode', 'name',) #display as clickable link
    search_fields = ('translations__name','translations__shortname','afrocode')
    list_per_page = 50 #limit records displayed on admin site to 30
    list_filter = (
        ('reference', RelatedOnlyDropdownFilter),
    )

    class Media:
        exclude = ('date_created','date_lastupdated',)


@admin.register(StgIndicatorDomain)
class IndicatorDomainAdmin(TranslatableAdmin,OverideExport):
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        return qs

    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    fieldsets = (
        ('Domain Attributes', {
                'fields': ('name', 'shortname','parent','level')
            }),
            ('Domain Description', {
                'fields': ('description','indicators'),
            }),
        )
    resource_class = DomainResourceExport
    # actions = ExportActionModelAdmin.actions
    list_display=('name','code','parent','level',)
    list_select_related = ('parent',)
    list_display_links = ('code', 'name',)
    search_fields = ('translations__name','translations__shortname','code')
    list_per_page = 50 #limit records displayed on admin site to 15
    filter_horizontal = ('indicators',) # this should display  inline with multiselect
    exclude = ('date_created','date_lastupdated',)
    list_filter = (
        ('parent',TranslatedFieldFilter,),
        ('indicators',TranslatedFieldFilter,),# Added 16/12/2019 for M2M lookup
        ('level',DropdownFilter,),# Added 16/12/2019 for M2M lookup
    )

class IndicatorProxyForm(forms.ModelForm):
    categoryoption = GroupedModelChoiceField(label=_('Disaggregation Option'),
        group_by_field='category',queryset=StgCategoryoption.objects.all().order_by(
            'category__category_id'))
    '''
    Implemented after overrriding decimal place restriction that facts with >3
    decimal places. The RoundingDecimalFormField is in serializer.py
    '''
    value_received = RoundingDecimalFormField(
        max_digits=20,decimal_places=2,required=False,
        label=_('Numeric Value'),)#changed to false 15/09/20
    min_value = RoundingDecimalFormField(label=_('Minimum Value'),
        max_digits=20,decimal_places=2,required=False)
    max_value = RoundingDecimalFormField(label=_('Maximum Value'),
        max_digits=20,decimal_places=2,required=False)
    target_value = RoundingDecimalFormField(label=_('Target Value'),
        max_digits=20,decimal_places=2,required=False)
    numerator_value = RoundingDecimalFormField(label=_('Numerator Value'),
        max_digits=20,decimal_places=2,required=False)
    denominator_value = RoundingDecimalFormField(label=_('Denominator Value'),
        max_digits=20,decimal_places=2,required=False)

    class Meta:
        model = FactDataIndicator
        widgets = {'user': forms.HiddenInput()} # hide user field for autofill
        fields = ('indicator','location', 'categoryoption','datasource',
            'measuremethod','start_period','end_period','value_received',
            'string_value','priority',)

    def clean(self):
        cleaned_data = super().clean()
        indicator_field = 'indicator'
        indicator = cleaned_data.get(indicator_field)
        location_field = 'location'
        location = cleaned_data.get(location_field)
        categoryoption_field = 'categoryoption'
        categoryoption = cleaned_data.get(categoryoption_field)
        #This attribute was added after getting error- location cannot be null
        datasource_field = 'datasource' #
        datasource = cleaned_data.get(datasource_field)
        measuremethod_field = 'measuremethod' #
        measuremethod = cleaned_data.get(measuremethod_field)
        start_year_field = 'start_period'
        start_period = cleaned_data.get(start_year_field)
        end_year_field = 'end_period'
        end_period = cleaned_data.get(end_year_field)

        priority_field = 'priority'
        priority = cleaned_data.get(priority_field)

        # This validation construct was added on 10/04/2022 to limit priority
        # indicators to a maximum of 10 per country...courtesy of Bertha of AFRO
        countfacts=NHOCustomFactsindicator.objects.filter(
            priority=priority).count()
        countlocations=NHOCustomFactsindicator.objects.filter(
            location=location).count()
        if countfacts and countlocations >11: # the count must be greater than 10 not 6 corrected on 21/12/2022
            raise ValidationError(_('Sorry. '+str(location).capitalize()+' \
                  cannot have more than 10 priorities'))

        if indicator and location and categoryoption and datasource and \
            start_period and end_period:
            if FactDataIndicator.objects.filter(indicator=indicator,
                location=location,datasource=datasource,
                categoryoption=categoryoption,start_period=start_period,
                end_period=end_period).exists():
                """
                pop(key) method removes the specified key and returns the
                corresponding value. Returns error If key does not exist
                """
                cleaned_data.pop(indicator_field)  # is also done by add_error
                cleaned_data.pop(location_field)
                cleaned_data.pop(categoryoption_field)
                cleaned_data.pop(datasource_field) # added line on 21/02/2020
                cleaned_data.pop(measuremethod_field)
                cleaned_data.pop(start_year_field)
                cleaned_data.pop(end_year_field)

                if end_period < start_period:
                    raise ValidationError({'start_period':_(
                        'Sorry! Ending year cannot be lower than the start year. \
                        Please make corrections')})
        return cleaned_data


# Register import wizard for the custom serializer defined in common.wizard.py
data_wizard.register(
    "Indicators Data Import",DataWizardFactIndicatorSerializer)

@admin.register(FactDataIndicator)
class IndicatorFactAdmin(ExportActionModelAdmin,OverideExport):

    form = IndicatorProxyForm #overrides the default django model form
    """
    Serge requested that a user does not see other users or groups data.
    This method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        
        qs = super().get_queryset(request).filter( # filter using session language
            location__translations__language_code=language,
                indicator__translations__language_code=language,
                categoryoption__translations__language_code=language,
                datasource__translations__language_code=language,
                measuremethod__translations__language_code=language,
        )
    
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        language = request.LANGUAGE_CODE # get the en, fr or pt from the request
        user_uuid = request.user.location.locationlevel.uuid
        user_level= StgLocationLevel.objects.get(uuid=user_uuid)
        
        qs = qs.select_related('location','indicator','categoryoption', 
                'datasource','measuremethod','user').prefetch_related(
                'location__translations','indicator__translations',
                'categoryoption__translations','datasource__translations',
                'measuremethod__translations').only(
                'location','indicator','categoryoption','datasource',
                'measuremethod','user','value_received','period','comment',
                'date_created','date_lastupdated','user__id','location__location_id',
                'indicator__indicator_id','categoryoption__categoryoption_id',
                'datasource__datasource_id','measuremethod__measuremethod_id',
                'priority','string_value','indicator__afrocode','min_value',
                'numerator_value','denominator_value','max_value',
                'target_value','start_period','end_period',).filter(
                    indicator__translations__language_code=language,
                    location__translations__language_code=language,
                    categoryoption__translations__language_code=language,
                    datasource__translations__language_code=language,   
                    measuremethod__translations__language_code=language,            
                )
        
        if request.user.is_superuser:
            qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1 and user_level:
            qs=qs.filter(location__gte=user_location) # return data for all locations
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1 and user_level:
            qs=qs.filter(location=user_location)
        else: # return own data if not member of a group
            qs=qs.filter(user=request.user).distinct()
        return qs

    """
    Serge requested that the form for data input be restricted to user's country.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.=== modified 02/02/2021
    """
    
    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        email = request.user.email
        user_location = request.user.location.location_id
        language = request.LANGUAGE_CODE # get the en, fr or pt from the request
        
        if db_field.name == "location":
            if request.user.is_superuser:
                kwargs["queryset"] = StgLocation.objects.select_related(
                    'parent','locationlevel','wb_income','special').prefetch_related(
                    'translations__master',
                    # Multi-level location lookup to address N+1 query problem
                    'locationlevel__locationlevel_id__master').order_by('location_id')
                # Looks up for the location level upto the country level
            elif user in groups and user_location==1:
                kwargs["queryset"] = StgLocation.objects.select_related(
                    'parent','locationlevel','wb_income','special').prefetch_related(
                    'translations__master',
                    # Multi-level location lookup to address N+1 query problem
                    'locationlevel__locationlevel_id__master').filter(
                    locationlevel__locationlevel_id__gte=1,
                    locationlevel__locationlevel_id__lte=2).order_by(
                'location_id')
            else:
                kwargs["queryset"] = StgLocation.objects.select_related(
                    'parent','locationlevel','wb_income','special').prefetch_related(
                    'translations__master',
                    # Multi-level location lookup to address N+1 query problem
                    'locationlevel__locationlevel_id__master').filter(
                    location_id=request.user.location_id).translated(
                    language_code=language)

        if db_field.name == "indicator":
            kwargs["queryset"] = StgIndicator.objects.select_related(
                'reference',).prefetch_related(
                'translations__master',).filter(
                translations__language_code=language)

        if db_field.name == "categoryoption":
            kwargs["queryset"] = StgCategoryoption.objects.select_related(
                'category').prefetch_related('translations__master').filter(
                translations__language_code=language)

        if db_field.name == "datasource":
            kwargs["queryset"] = StgDatasource.objects.prefetch_related(
                'translations__master').filter(
                    translations__language_code=language)

        if db_field.name == "measuremethod":
            kwargs["queryset"] = StgMeasuremethod.objects.prefetch_related(
                'translations__master').filter(
                    translations__language_code=language)

        if db_field.name == "user":
            kwargs["queryset"] = CustomUser.objects.select_related(
                'location').prefetch_related('role',
                'location__translations__master').get(id=user)
        return super().formfield_for_foreignkey(db_field, request,**kwargs)



    # #This method gets afrocode from  indicator model for use in list_display
    def get_afrocode(obj):
        return obj.indicator.afrocode
    get_afrocode.admin_order_field  = 'indicator__afrocode'#Sort by AFROCODE
    get_afrocode.short_description = 'Indicator Code'  #Renames the column header

    def get_actions(self, request):
        actions = super(IndicatorFactAdmin, self).get_actions(request)
        if not request.user.has_perm('indicators.approve_factdataindicator'):
           actions.pop('transition_to_approved', None)
        if not request.user.has_perm('indicators.reject_factdataindicator'):
            actions.pop('transition_to_rejected', None)
        if not request.user.has_perm('indicators.delete_factdataindicator'):
            actions.pop('delete_selected', None)
        return actions

    def get_export_resource_class(self):
        return IndicatorFactsResourceExport

    def get_import_resource_class(self):
        return IndicatorFactsResourceImport

    #Format date created to disply only the day, month and year
    def date_created (obj):
        return obj.date_created.strftime("%d-%b-%Y")
    date_created.admin_order_field = 'date_created'
    date_created.short_description = 'Date Created'

    # Show the last update date so users can audit recent changes from the table.
    def date_modified(obj):
        if not obj.date_lastupdated:
            return ''
        return obj.date_lastupdated.strftime("%d-%b-%Y")
    date_modified.admin_order_field = 'date_lastupdated'
    date_modified.short_description = 'Date Modified'

    # use a more descriptive approval status column name
    def get_status(self, obj):
        return obj.get_comment_display()
    get_status.short_description = 'Status'


    """
    Overrride model_save method to grab id of the logged in user. The save_model
    method is given HttpRequest (request), model instance (obj), ModelForm
    instance (form), and boolean value (change) based on add or changes to object.
    """
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # only set user during the first save.
        super().save_model(request, obj, form, change)

    readonly_fields = ('indicator', 'location', 'start_period',)
    fieldsets = ( # used to create frameset sections on the data entry form
        ('Indicator Details', {
                'fields': ('indicator','location', 'categoryoption',
                'datasource','measuremethod','priority',)
            }),
            ('Reporting Period & Data Values', {
                'fields': ('start_period','end_period','value_received',
                'numerator_value','denominator_value','min_value',
                'max_value','target_value','string_value'),
            }),
        )
    # The list display includes a callable get_afrocode that returns indicator code
    list_display=('indicator','location', get_afrocode,'period',
                  'categoryoption','value_received','string_value',
                  'datasource','get_status','priority',date_created,date_modified,)

    search_fields = ('indicator__translations__name','location__translations__name',
        'period','indicator__afrocode','comment','priority') #display search field
   
    list_filter = [('comment', ChoiceDropdownFilter), LocationFilter,IndicatorsFilter, # optimal filter refactored 01/02/2023
        DatasourceFilter,CategoryOptionFilter]

    list_select_related = ('indicator','location','categoryoption','datasource',
        'measuremethod','user',)

    list_display_links = ('location',get_afrocode, 'indicator',)

    list_per_page = 50 #limit records displayed on admin site to 30

    def get_list_per_page(self, request):
        """Allow the Laravel-style page-size selector to control the list length."""
        try:
            requested_size = int(request.GET.get('per_page') or self.list_per_page)
        except (TypeError, ValueError):
            requested_size = self.list_per_page
        return requested_size if requested_size in (10, 25, 50, 100, 250) else self.list_per_page

    #This field needed for controlled approval of resource before ETL process
    readonly_fields=('comment',)

    actions = list(ExportActionModelAdmin.actions) + [transition_to_pending,
        transition_to_approved,transition_to_rejected,]



class LimitModelFormset(BaseInlineFormSet):
    ''' Base Inline formset to limit inline Model records'''
    def __init__(self, *args, **kwargs):
        super(LimitModelFormset, self).__init__(*args, **kwargs)
        instance = kwargs["instance"]
        self.queryset = FactDataIndicator.objects.filter(
            indicator_id=instance).order_by('-date_created')[:5]

# Define the fact table as a tubular form for ease of data entry
class FactIndicatorInline(admin.TabularInline):
    form = IndicatorProxyForm #overrides the default django form
    model = FactDataIndicator
    formset = LimitModelFormset
    extra = 2 # Used to control  number of empty rows displayed.

    """
    Davy and Serge requested that the form be restricted to user's country.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.=== modified 02/02/2021
    """
    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        email = request.user.email
        user_location = request.user.location.location_id
        language = request.LANGUAGE_CODE # get the en, fr or pt from the request
        if db_field.name == "location":
            if request.user.is_superuser:
                kwargs["queryset"] = StgLocation.objects.only(
                    'locationlevel').order_by('location_id')
                # Looks up for the location level upto the country level
            elif user in groups and user_location==1:
                kwargs["queryset"] = StgLocation.objects.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2).order_by(
                'location_id')
            else:
                kwargs["queryset"] = StgLocation.objects.filter(
                location_id=request.user.location_id).translated(
                language_code=language)

        if db_field.name == "user":
                kwargs["queryset"] = CustomUser.objects.filter(
                    email=email)

        # Restricted permission to data source implememnted on 20/03/2020
        if db_field.name == "datasource":
            kwargs["queryset"] = StgDatasource.objects.filter(
            translations__language_code=language).distinct()
        return super().formfield_for_foreignkey(db_field, request,**kwargs)



@admin.register(IndicatorProxy)
class IndicatorProxyAdmin(TranslatableAdmin):
    """
    Serge requested that a user does not see other users or groups data. This
    method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        # language_code = settings.LANGUAGE_CODE
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.username
        language = request.LANGUAGE_CODE # get the en, fr or pt from the request
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
        db_user=list(CustomUser.objects.values_list('username', flat=True))
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        if request.user.is_superuser:
            qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1:
            qs_admin=db_locations.filter(
				locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2)
        return qs

    #This method removes the add button on the admin interface
    def has_add_permission(self, request, obj=None):
        return False
    # This function limits the export format to CSV, XML and XLSX
    def get_import_formats(self):
        """
        This function returns available export formats.
        """
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_import()]

    def get_export_formats(self):
        """
        This function returns available export formats.
        """
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_export()]

    """
    To autofill the user column in a TabularInline formset, you have to override
    the save_formset method inside the Proxy ModelAdmin that contains the inlines
    """
    def save_formset(self, request, form, formset, change):
        for form in formset.forms:
            form.instance.user = request.user
        formset.save()

    fieldsets = (
        ('Indicator Details', {
                'fields':('name','afrocode','reference',)
            }),
        )

    inlines = [FactIndicatorInline]
    readonly_fields = ('afrocode', 'name','reference',)
    list_display=['name','afrocode','reference',]
    list_display_links=['afrocode', 'name']
    search_fields = ('afrocode','translations__name','translations__shortname',)
    list_filter = (
        ('translations__name',DropdownFilter),
    )


@admin.register(aho_factsindicator_archive)
class IndicatorFactArchiveAdmin(OverideExport):
    # This method removes the add button because no data entry is needed
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, extra_context=None):
        ''' Customize add/edit form '''
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False
        return super(IndicatorFactArchiveAdmin, self).change_view(
            request,object_id,extra_context=extra_context)

    def get_afrocode(obj):
        return obj.indicator.afrocode
    get_afrocode.admin_order_field  = 'indicator__afrocode'
    get_afrocode.short_description = 'Indicator Code'

    #Format date created to disply only the day, month and year
    def date_created (obj):
        return obj.date_created.strftime("%d-%b-%Y")
    date_created.admin_order_field = 'date_created'
    date_created.short_description = 'Date Created'

    """
    Serge requested that the form for data input be restricted to user's location.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.===modified 02/02/2021
    """

    def get_queryset(self, request):
        show_full_result_count = False # added 28-01-2023
        language = request.LANGUAGE_CODE # get the en, fr or pt from the request

        qs = super().get_queryset(request).filter( # filter using session language
            location__translations__language_code=language,
                indicator__translations__language_code=language,
                categoryoption__translations__language_code=language,
                datasource__translations__language_code=language,
                measuremethod__translations__language_code=language,
            )

        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        language = request.LANGUAGE_CODE # get the en, fr or pt from the request
        user_location = request.user.location.location_id
        user_uuid = request.user.location.locationlevel.uuid
        user_level= StgLocationLevel.objects.get(uuid=user_uuid)
                   
        qs = qs.select_related('location','indicator','categoryoption', 
                'datasource','measuremethod','user').prefetch_related(
                'location__translations','indicator__translations',
                'categoryoption__translations','datasource__translations',
                'measuremethod__translations').only(
                'location','indicator','categoryoption','datasource',
                'measuremethod','user','value_received','period','comment',
                'date_created','user__id','location__location_id',
                'indicator__indicator_id','categoryoption__categoryoption_id',
                'datasource__datasource_id','measuremethod__measuremethod_id',
                )

        if request.user.is_superuser:
            qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1 and user_level:
            qs=qs.filter(location__gte=user_location) # return data for all locations
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1 and user_level:
            qs=qs.filter(location=user_location)
        else: # return own data if not member of a group
            qs=qs.filter(user=request.user).distinct()
        return qs

 
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('location_search/', self.admin_site.admin_view(
                LocationSearchView.as_view(model_admin=self)),name='location_search'),
            path('indicator_search/', self.admin_site.admin_view(
                IndicatorSearchView.as_view(model_admin=self)),name='indicator_search'),
            path('categories_search/', self.admin_site.admin_view(
                CategoryOptionSearchView.as_view(model_admin=self)),name='categories_search'),
            path('source_search/', self.admin_site.admin_view(
                DataourceSearchView.as_view(model_admin=self)), name='source_search'),
        ]
        return custom_urls + urls

    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        email = request.user.email
        user_location = request.user.location.location_id
        language = request.LANGUAGE_CODE # get the en, fr or pt from the request
        
        if db_field.name == "location":
            if request.user.is_superuser:
                kwargs["queryset"] = StgLocation.objects.select_related(
                    'parent','locationlevel','wb_income','special').prefetch_related(
                    'translations__master').order_by(
                    'locationlevel','translations__name').filter(
                        translations__language_code=language)
                # Looks up for the location level upto the country level
            elif user in groups and user_location==1:
                kwargs["queryset"] = StgLocation.objects.select_related(
                    'parent','locationlevel','wb_income','special').prefetch_related(
                    'translations__master',
                     # Multi-level location lookup to address N+1 query problem
                    'locationlevel__locationlevel_id__master').filter(
                    locationlevel__locationlevel_id__gte=1,
                    locationlevel__locationlevel_id__lte=2).order_by(
                    'locationlevel','translations__name').filter(
                        translations__language_code=language)
            else:
                kwargs["queryset"] = StgLocation.objects.select_related(
                    'parent','locationlevel','wb_income','special').prefetch_related(
                    'translations__master').filter(
                    location_id=request.user.location_id).filter(
                        translations__language_code=language).order_by(
                    'locationlevel','translations__name')

        if db_field.name == "indicator":
            kwargs["queryset"] = StgIndicator.objects.select_related(
                'reference',).prefetch_related(
                'translations__master',).filter(
                translations__language_code=language).order_by(
                'translations__name')

        if db_field.name == "categoryoption":
            kwargs["queryset"] = StgCategoryoption.objects.select_related(
                'category').prefetch_related('translations__master').filter(
                translations__language_code=language).order_by(
                'category__translation__name','translations__name')

        if db_field.name == "datasource":
            kwargs["queryset"] = StgDatasource.objects.prefetch_related(
                'translations__master').filter(
                translations__language_code=language).order_by(
                'translations__name')

        if db_field.name == "measuremethod":
            kwargs["queryset"] = StgMeasuremethod.objects.prefetch_related(
                'translations__master').filter(
                translations__language_code=language).order_by(
                'translations__name')

        if db_field.name == "user":
            kwargs["queryset"] = CustomUser.objects.select_related(
                'location').prefetch_related('role',
                'location__translations__master').get(id=user)
        return super().formfield_for_foreignkey(db_field, request,**kwargs)


    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set user from request during the first save.
            obj.location = request.user.location # set location during first save.
        super().save_model(request, obj, form, change)

    exclude = ('user',)
    # resource_class = AchivedIndicatorResourceExport
    actions = ExportActionModelAdmin.actions
    list_display=('indicator','location','categoryoption','datasource',
        'value_received','period','comment',date_created,)
    list_select_related = True

    
    search_fields = ('indicator__translations__name','location__translations__name',
        'period','comment',) #display search field
    list_per_page = 100 #limit records displayed on admin site to 50
      
    list_filter = [LocationFilter,IndicatorsFilter, DatasourceFilter,# this is the optimal solution to filter
            CategoryOptionFilter]
 
 

@admin.register(StgNarrative_Type)
class NarrativeTypeAdmin(TranslatableAdmin,OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        return qs

    resource_class = NarrativeTypeResourceExport
    list_display=['name','code','shortname','description',]
    list_display_links =('code','name',)
    search_fields = ('code','translations__name','translations__shortname')
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_lastupdated','code',)


@admin.register(StgAnalyticsNarrative)
class AnalyticsNarrativeAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        language = request.LANGUAGE_CODE
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
        user_uuid = request.user.location.locationlevel.uuid
        user_level= StgLocationLevel.objects.get(uuid=user_uuid)

        qs = super().get_queryset(request).filter(
            domain__translations__language_code=language).order_by(
            'domain__translations__name').filter(
            location__translations__language_code=language).order_by(
            'location__translations__name').filter(
                narrative_type__translations__language_code=language).distinct()
        
        if request.user.is_superuser:
            qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1 and user_level:
            qs=qs.filter(location__gte=user_location) # return data for all locations
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1 and user_level:
            qs=qs.filter(location=user_location)
        else: # return own data if not member of a group
            qs=qs.filter(user=request.user).distinct()
        return qs        

    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        language = request.LANGUAGE_CODE
        if db_field.name == "location":
            if request.user.is_superuser:
                kwargs["queryset"] = StgLocation.objects.all().order_by(
                'location_id')
                # Looks up for the location level upto the country level
            elif user in groups and user_location==1:
                kwargs["queryset"] = StgLocation.objects.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2).order_by(
                'location_id')
            else:
                kwargs["queryset"] = StgLocation.objects.filter(
                location_id=request.user.location_id).translated(
                language_code=language)

        if db_field.name == "domain":
                kwargs["queryset"] = StgIndicatorDomain.objects.filter(
                translations__language_code=language).filter(
                level=4).distinct()
        return super().formfield_for_foreignkey(db_field, request,**kwargs)
    resource_class = ThematicNarrativeResourceExport
    list_display=['narrative_type','location','domain','narrative_text']
    list_select_related = ('location','domain',)
    list_display_links =('narrative_type','domain')
    search_fields = ('code','location__translations__name',
        'domain__translations__name') #display search field
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_lastupdated','code',)
    list_filter = (
      ('location',RelatedOnlyDropdownFilter),
    )
    exclude = ('date_lastupdated','code',)


@admin.register(StgIndicatorNarrative)
class IndicatorNarrativeAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        language = request.LANGUAGE_CODE
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
        user_uuid = request.user.location.locationlevel.uuid
        user_level= StgLocationLevel.objects.get(uuid=user_uuid)
        
        qs = super().get_queryset(request).filter(
            indicator__translations__language_code=language).order_by(
            'indicator__translations__name').filter(
            location__translations__language_code=language).order_by(
            'location__translations__name').distinct()
        
        if request.user.is_superuser:
            qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1 and user_level:
            qs=qs.filter(location__gte=user_location) # return data for all locations
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1 and user_level:
            qs=qs.filter(location=user_location)
        else: # return own data if not member of a group
            qs=qs.filter(user=request.user).distinct()
        return qs        


    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        language = request.LANGUAGE_CODE
        if db_field.name == "location":
            if request.user.is_superuser:
                kwargs["queryset"] = StgLocation.objects.all().order_by(
                'location_id')
                # Looks up for the location level upto the country level
            elif user in groups and user_location==1:
                kwargs["queryset"] = StgLocation.objects.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2).order_by(
                'location_id')
            else:
                kwargs["queryset"] = StgLocation.objects.filter(
                location_id=request.user.location_id).translated(
                language_code=language)

        if db_field.name == "indicator":
                kwargs["queryset"] = StgIndicator.objects.filter(
                translations__language_code=language).distinct()
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    resource_class = IndicatorNarrativeResourceExport
    list_display=['narrative_type','code','location','indicator','narrative_text',]
    list_select_related = ('location','indicator',)
    list_display_links =('code',)
    search_fields = ('code','location__translations__name',
        'indicator__translations__name') #display search field
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_lastupdated','code',)
    list_filter = (
      ('location',RelatedOnlyDropdownFilter),
    )


@admin.register(AhoDoamain_Lookup)
class AhoDoamain_LookupAdmin(OverideExport,ExportActionModelAdmin):
    # This method removes the add button on the admin interface
    def has_delete_permission(self, request, obj=None):
        return False
    # This method removes the add button on the admin interface
    def has_add_permission(self, request, obj=None):
        return False
    #This method removes the save buttons from the model form added on 6th Dec 2020
    def changeform_view(self,request,object_id=None,form_url='',extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False
        return super(AhoDoamain_LookupAdmin, self).changeform_view(
            request, object_id, extra_context=extra_context)

    def get_queryset(self, request):
        groups = list(request.user.groups.values_list('user', flat=True))
        db_locations = StgLocation.objects.all().order_by('location_id')
        qs = super().get_queryset(request).distinct()
        return qs
    resource_class = DomainLookupResourceExport
    actions = ExportActionModelAdmin.actions
    list_display=('indicator_name','code','domain_name', 'domain_level',)
    list_display_links = None # make the link for change object non-clickable
    readonly_fields = ('indicator_name','code','domain_name', 'domain_level',)
    search_fields = ('indicator_name','code','domain_name', 'domain_level',)
    ordering = ('indicator_name',)
    list_filter = (
        ('domain_name', DropdownFilter,),
    )
    ordering = ('indicator_name',)


@admin.register(NHOCustomizationIcons)
class NHOIndicatorIconsAdmin(TranslatableAdmin):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        return qs


    fieldsets = (
        ('Font-Awesome Icon Attributes', {
                'fields': ('unicode','code','name','shortname',)
            }),
            ('Description', {
                'fields': ('version','description',),
            }),
        )
    list_display=['name','code','unicode','description','version']
    list_display_links = ('name','code','unicode',)
    search_fields = ('code','unicode','translations__name','version')
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated',)


@admin.register(NHOCustomFactsindicator)
class NHOCustomizationAdmin(OverideExport,ExportActionModelAdmin):
    def get_queryset(self, request):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        language = request.LANGUAGE_CODE # get the en, fr or pt from the request
        db_locations = StgLocation.objects.only('locationlevel',).select_related(
            'parent','locationlevel','wb_income','special').order_by(
            'location_id')
        qs = super().get_queryset(request).select_related(
            'indicator','location','categoryoption','datasource',
            'measuremethod','user',).filter(
            indicator__translations__language_code=language).filter(
            location__translations__language_code=language).filter(
            categoryoption__translations__language_code=language).filter(
            datasource__translations__language_code=language).filter(
            measuremethod__translations__language_code=language).distinct()
        qs = qs.order_by('indicator', 'location').distinct()
        if request.user.is_superuser:
            qs
        # returns data for AFRO and member countries
        elif user in groups and user_location==1:
            qs_admin=db_locations.filter(
				locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2)
        # return data based on the location of the user logged/request location
        elif user in groups and user_location>1:
            qs=qs.filter(location=user_location)
        else: # return own data if not member of a group
            qs=qs.filter(user=request.user)
        return qs

    #Format date created to disply only the day, month and year
    def date_created (obj):
        if obj.date_created is not None:
            return obj.date_created.strftime("%d-%b-%Y")
        pass
    date_created.admin_order_field = 'date_created'
    date_created.short_description = 'Date Created'

    # This method removes the add button because no data entry is needed
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def change_view(self, request, object_id, extra_context=None):
        ''' Customize add/edit form '''
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = True
        return super(NHOCustomizationAdmin, self).change_view(
            request,object_id,extra_context=extra_context)

    def save(self, *args, **kwargs):
        if NHOCustomizationAdmin.objects.count() >=10:
            objects[0].delete()
        super(NHOCustomizationAdmin, self).save(*args, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set user from request during the first save.
        super().save_model(request, obj, form, change)

    exclude = ('user',)

    list_display=('indicator','location','categoryoption','datasource',
    'value_received','period','priority',date_created)
    list_select_related = ('indicator','location','categoryoption','datasource',
        'measuremethod','user','icon',)
    search_fields = ('indicator__translations__name','location__translations__name',
        'period') #display search field
    list_per_page = 100 #limit records displayed on admin site to 50
    list_filter = (
        ('location', TranslatedFieldFilter,),
        ('indicator', TranslatedFieldFilter,),
        ('datasource', TranslatedFieldFilter,),
        ('categoryoption', TranslatedFieldFilter,),
    )
