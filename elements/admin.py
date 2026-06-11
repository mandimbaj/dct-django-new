from django.contrib import admin
from django.contrib.admin import AdminSite #customize adminsite
from django import forms
from django.utils.translation import gettext_lazy as _

import data_wizard #this may be the solution to data import madness that has refused to go
from itertools import groupby #additional import for grouped desaggregation options
from parler.admin import TranslatableAdmin
from django.forms import TextInput,Textarea
from import_export.formats import base_formats
from django.forms import BaseInlineFormSet
from django.forms.models import ModelChoiceField, ModelChoiceIterator
from import_export.admin import (ExportActionModelAdmin,ExportMixin,
    ImportExportModelAdmin,ImportExportActionModelAdmin,)
#This are additional imports to override the default Django forms
from django.core.exceptions import NON_FIELD_ERRORS
from django.core.exceptions import ValidationError
from django.forms.models import ModelChoiceField, ModelChoiceIterator
from django.contrib.auth.decorators import permission_required #for approval actions
from .models import (StgDataElement,DataElementProxy,StgDataElementGroup,
    FactDataElement,)
from .resources import (
    FactDataResourceExport, FactDataResourceImport, DataElementExport)
from regions.models import StgLocation
from commoninfo.admin import OverideImportExport, OverideExport
from commoninfo.fields import RoundingDecimalFormField # For fixing rounded decimal
from django_admin_listfilter_dropdown.filters import (
    DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter,
    RelatedOnlyDropdownFilter)
from authentication.models import CustomUser, CustomGroup
from home.models import ( StgDatasource,StgCategoryoption)
from .filters import TranslatedFieldFilter #Danile solution to duplicate filters

from commoninfo.wizard import DataWizardElementSerializer

# The following 3 functions are used to register admin actions
# performed on the data elements. See actions listbox
def transition_to_pending (modeladmin, request, queryset):
    queryset.update(comment = 'pending')
transition_to_pending.short_description = "Mark selected as Pending"

def transition_to_approved (modeladmin, request, queryset):
    queryset.update (comment = 'approved')
transition_to_approved.short_description = "Mark selected as Approved"

def transition_to_rejected (modeladmin, request, queryset):
    queryset.update (comment = 'rejected')
transition_to_rejected.short_description = "Mark selected as Rejected"

'''----------------------------------------------------------------------------
These are ModelAdmins that facilitate viewing of raw data elements from other
systems like DHIS2
------------------------------------------------------------------------------'''
class GroupedModelChoiceIterator(ModelChoiceIterator):
    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)
        if self.field.cache_choices:
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    (self.field.group_label(group), [self.choice(ch) for ch in choices])
                        for group,choices in groupby(self.queryset.all(),
                            key=lambda row: getattr(row, self.field.group_by_field))
                ]
            for choice in self.field.choice_cache:
                yield choice
        else:
            for group, choices in groupby(self.queryset.all(),
	        key=lambda row: getattr(row, self.field.group_by_field)):
                    yield (self.field.group_label(group), [self.choice(ch) for ch in choices])


class GroupedModelChoiceField(ModelChoiceField):
    def __init__(self, group_by_field, group_label=None,
        cache_choices=False, *args, **kwargs):
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


@admin.register(StgDataElement)
class DataElementAdmin(TranslatableAdmin,OverideExport):
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
        ('Primary Attributes', {
                'fields': ('name','shortname', 'description')
            }),
            ('Secondary Attributes', {
                'fields': ('aggregation_type',),
            }),
        )

    resource_class = DataElementExport
    list_display=['name','code','shortname','description',]
    list_display_links = ('code', 'name',)

    search_fields = ('translations__name', 'translations__shortname','code',) #display search field
    list_per_page = 30 #limit records displayed on admin site to 30
    exclude = ('date_created','date_lastupdated',)


class DataElementProxyForm(forms.ModelForm):
    categoryoption = GroupedModelChoiceField(group_by_field='category',
        queryset=StgCategoryoption.objects.all().order_by(
            'category__category_id'),
    )
    # Overrride decimal place restriction that rejects number with >3 d.places
    value = RoundingDecimalFormField(label=_('Numeric Value'),max_digits=20,
                decimal_places=2,)
    target_value = RoundingDecimalFormField(label=_('Target Value'),
        max_digits=20,decimal_places=2,required=False)

    class Meta:
        model = FactDataElement
        fields = ('dataelement','location','period', 'categoryoption',
            'datasource','start_year', 'end_year','value', 'comment',)

    def clean(self):
        cleaned_data = super().clean()
        dataelement_field = 'dataelement'
        dataelement = cleaned_data.get(dataelement_field)
        location_field = 'location'
        location = cleaned_data.get(location_field)
        categoryoption_field = 'categoryoption'
        categoryoption = cleaned_data.get(categoryoption_field)
        datasource_field = 'datasource' #
        datasource = cleaned_data.get(datasource_field)
        start_year_field = 'start_year'
        start_year = cleaned_data.get(start_year_field)
        end_year_field = 'end_year'
        end_year = cleaned_data.get(end_year_field)

        if dataelement and location and categoryoption and categoryoption \
            and start_year and end_year:
            if FactDataElement.objects.filter(
                dataelement=dataelement,datasource=datasource,location=location,
                categoryoption=categoryoption,start_year=start_year,
                end_year=end_year).exists():

                """ pop(key) method removes the specified key and returns the \
                corresponding value. Returns error If key does not exist"""
                cleaned_data.pop(dataelement_field)  # is also done by add_error
                cleaned_data.pop(location_field)
                cleaned_data.pop(categoryoption_field)
                cleaned_data.pop(datasource_field) # added line on 21/02/2020
                cleaned_data.pop(start_year_field)
                cleaned_data.pop(end_year_field)

                if end_year < start_year:
                    raise ValidationError({'start_year':_(
                        'Sorry! Ending year cannot be lower than the start year. \
                        Please make corrections')})
        return cleaned_data


data_wizard.register(
    "Elements Data Import", DataWizardElementSerializer)

@admin.register(FactDataElement)
class DataElementFactAdmin(ExportActionModelAdmin,OverideExport):
    form = DataElementProxyForm #overrides the default django form

    """
    Davy requested that a user does not see other countries data. This function
    does exactly that by filtering location based on logged in user. For this
    reason only the country of the loggied in user is displayed whereas the
    superuser has access to all the countries. Thanks to
    https://docs.djangoproject.com/en/2.2/ref/contrib/admin/
    because it gave the exact logic of achiving this non-functional requirement
    """
    def get_queryset(self, request):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        language = request.LANGUAGE_CODE
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
        qs = super().get_queryset(request).filter(
            dataelement__translations__language_code=language).filter(
            location__translations__language_code=language).filter(
            categoryoption__translations__language_code=language).filter(
            datasource__translations__language_code=language).filter(
            valuetype__translations__language_code=language).order_by(
            'dataelement__translations__name').filter(
            location__translations__language_code=language).order_by(
            'location__translations__name').distinct()

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
        elif user_location>1:
            qs=qs.filter(location=user_location)
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

        if db_field.name == "dataelement":
                kwargs["queryset"] = StgDataElement.objects.filter(
                translations__language_code=language).distinct()

        if db_field.name == "user":
                kwargs["queryset"] = CustomUser.objects.filter(
                email=email)
        return super().formfield_for_foreignkey(db_field, request,**kwargs)


    #This function is used to get the afrocode from related indicator model for use in list_display
    def get_afrocode(obj):
        return obj.dataelement.code
    get_afrocode.admin_order_field  = 'dataelement__code'  #Lookup to allow column sorting by AFROCODE
    get_afrocode.short_description = 'Data Element Code'  #Renames column head

    #The following function returns available export formats.
    def get_export_formats(self):
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_export()]

    def get_import_formats(self):
        """
        Returns available export formats.
        """
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_import()]

    def get_actions(self, request):
        actions = super(DataElementFactAdmin, self).get_actions(request)
        if not request.user.has_perm('elements.approve_factdataelements'):
           actions.pop('transition_to_approved', None)
        if not request.user.has_perm('elements.reject_factdataelements'):
            actions.pop('transition_to_rejected', None)
        if not request.user.has_perm('elements.delete_factdataelements'):
            actions.pop('delete_selected', None)
        return actions

    def get_export_resource_class(self):
        return FactDataResourceExport

    def get_import_resource_class(self):
        return FactDataResourceImport

    #Format date created to disply only the day, month and year
    def date_created (obj):
        return obj.date_created.strftime("%d-%b-%Y")
    date_created.admin_order_field = 'date_created'
    date_created.short_description = 'Date Created'

    # use a more descriptive approval status column name
    def get_status(self, obj):
        return obj.get_comment_display()
    get_status.short_description = 'Status'
    
    actions = list(ExportActionModelAdmin.actions) + [transition_to_pending,
        transition_to_approved, transition_to_rejected]

    """
    Overrride model_save method to grab id of the logged in user. The save_model
    method is given HttpRequest (request), model instance (obj), ModelForm
    instance (form), and boolean value (change) based on add or changes to object.
    """
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # only set user during the first save.
        super().save_model(request, obj, form, change)

    fieldsets = ( # used to create frameset sections on the data entry form
        ('Data Element Details', {
                'fields': ('dataelement', 'location', 'categoryoption',
                    'datasource','start_year', 'end_year',)
            }),
            ('Reporting Period & Value', {
                'fields': ('valuetype','value','target_value',),
            }),
        )
    # Display includes a callable get_afrocode that returns data element code
    list_display=['dataelement','location',get_afrocode,'categoryoption','period',
        'value','datasource','get_status',date_created,]
    list_select_related = ('dataelement','location','categoryoption','datasource',
        'valuetype',)
    list_display_links = ('dataelement','location', get_afrocode,) #For making the code and name clickable
    search_fields = ('dataelement__translations__name','location__translations__name',
        'period','dataelement__code') #display search field
    list_per_page = 30 #limit records displayed on admin site to 30
    #this field need to be controlled for data entry. should only be active for the approving authority

    list_filter = (
        ('location', TranslatedFieldFilter,),
        ('dataelement', TranslatedFieldFilter,),
        ('period',DropdownFilter),
        ('categoryoption', TranslatedFieldFilter,),
        ('comment',DropdownFilter),
    )
    readonly_fields=('comment', 'period', )


class LimitModelFormset(BaseInlineFormSet):
    ''' Base Inline formset to limit inline Model records'''
    def __init__(self, *args, **kwargs):
        super(LimitModelFormset, self).__init__(*args, **kwargs)
        instance = kwargs["instance"]
        self.queryset = FactDataElement.objects.filter(
            dataelement_id=instance).order_by('-date_created')[:5]

# Fact table as a tubular (not columnar) form for ease of entry as requested by Davy Liboko
class FactElementInline(admin.TabularInline):
    form = DataElementProxyForm #overrides the default django form
    model = FactDataElement
    formset = LimitModelFormset
    # Very useful in controlling the number of empty rows displayed.In this case zero is Ok for insertion or changes
    extra = 2

    """
    This function is for filtering location to display country level. the database
    field must be parentid for the dropdown list    Note the use of
    locationlevel__name__in as helper for the name lookup while(__in)suffix is
    a special case that works with tuples in Python.
    """
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

        if db_field.name == "dataelement":
                kwargs["queryset"] = StgDataElement.objects.filter(
                translations__language_code=language).distinct()
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    list_select_related = ('dataelement','location','categoryoption','datasource',
        'valuetype',)
    fields = ('dataelement','location','datasource', 'valuetype','categoryoption',
            'start_year', 'end_year','value',)


@admin.register(DataElementProxy)
#This function removes the add button on the admin interface
class DataElementProxyAdmin(TranslatableAdmin):
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

    def has_add_permission(self, request, obj=None):
        return False
    #This function limits the export format to only 3 types -CSV, XML and XLSX
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

    inlines = [FactElementInline]
    fields = ('code', 'name')
    list_display_links = ('code', 'name',)
    # Added to customize fields displayed on the import window
    resource_class = FactDataResourceExport #added to customize fields displayed on the import window
    list_display_links = ('code', 'name',)
    # Use tabular form within the data element modelform
    list_display=['name','code','description',]
    list_display_links = ('code', 'name',)
    search_fields = ('code','translations__name',) #display search field
    readonly_fields = ('code','name','description',)


@admin.register(StgDataElementGroup)
class DataElementGoupAdmin(TranslatableAdmin,OverideExport):
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
        (' Data Elements Group Attributes',{
                'fields': (
                    'name', 'shortname','description',)
            }),
            ('Data Elements Allocation', {
                'fields':('dataelement',)
            }),
    )
    # Used to create frameset sections on the data entry form
    field = ('name','code','shortname', 'description',)
    list_display=['name','code','shortname', 'description',]
    search_fields = ('code','translations__name',) #display search field
    filter_horizontal = ('dataelement',) # Display an inline with multiselect
    exclude = ('code',)
