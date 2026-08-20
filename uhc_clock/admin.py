from django.contrib import admin
# register models here
import data_wizard # Solution for flexible data import from Excel and CSV
from django import forms
from django.conf import settings # allow import of projects settings at the root
from django.forms import BaseInlineFormSet
from parler.admin import (TranslatableAdmin,TranslatableStackedInline,
    TranslatableInlineModelAdmin)

from django_admin_listfilter_dropdown.filters import (
    DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter,
    RelatedOnlyDropdownFilter) #custom

from .models import (StgUHClockIndicatorsGroup,StgUHClockIndicators,
        StgUHCIndicatorTheme,Facts_UHC_DatabaseView,
        CountrySelectionUHCIndicators)

from django.forms import TextInput,Textarea # customize textarea row and column size
from commoninfo.admin import (OverideImportExport,OverideExport,OverideImport,)
from regions.models import StgLocation,StgLocationLevel
from indicators.models import StgIndicator

@admin.register(StgUHClockIndicatorsGroup)
class UHCClockIndicatorGroupAdmin(TranslatableAdmin):
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

data_wizard.register(StgUHClockIndicators)
@admin.register(StgUHClockIndicators)
class UHCClockIndicatorGroupAdmin(OverideExport):
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            indicator_id__translations__language_code=language,
            group__translations__language_code=language).distinct()
        return qs

    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        language = request.LANGUAGE_CODE

        if db_field.name == "indicator":
            kwargs["queryset"] = StgIndicator.objects.filter(
                translations__language_code=language).distinct()
        
        if db_field.name == "group":
            kwargs["queryset"] = StgUHClockIndicatorsGroup.objects.filter(
                translations__language_code=language).distinct()
                # Looks up for the location level upto the country level
        return super().formfield_for_foreignkey(db_field, request,**kwargs)
    
    list_display=['indicator','group','Indicator_type','description',]


@admin.register(StgUHCIndicatorTheme)
class UHClockIndicatorThemeAdmin(TranslatableAdmin,OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'120'})},
        models.TextField: {'widget': Textarea(attrs={'rows':2, 'cols':120})},
    }

    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
                'translations__name').distinct()
        return qs

    fieldsets = (
        ('Domain Attributes', {
                'fields': ('name', 'shortname','parent','group',
                        'level')
            }),
            ('Domain Description', {
                'fields': ('description','indicators'),
            }),
        )
    # resource_class = DomainResourceExport
    # actions = ExportActionModelAdmin.actions
    list_display=('name','shortname','parent','group','level')
    list_select_related = ('parent','group',)
    list_display_links = ('name','parent','group','level')
    search_fields = ('translations__name','translations__shortname','code')
    list_per_page = 50 #limit records displayed on admin site to 40
    # filter_horizontal = ('indicators',) # this should display  inline with multiselect
    exclude = ('date_created','date_lastupdated',)
 


@admin.register(Facts_UHC_DatabaseView)
class Facts_DataViewAdmin(OverideExport):
    change_list_template = 'admin/data_quality/change_list.html' # add buttons for validations
    import_export_change_list_template = 'admin/data_quality/change_list_export.html'
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'105'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request).distinct()
        groups = list(request.user.groups.values_list(
            'user', flat=True))
        user = request.user.id  
        location = request.user.location_id
        language = request.LANGUAGE_CODE 
        db_locations = StgLocation.objects.get(
            location_id=location) #filter by logged user loaction
        
        if request.user.is_superuser:
            qs=qs # show all records if logged in as super user
        elif user in groups: # return records on if the user belongs to the group
            qs=qs.filter(location=db_locations) # return records for logged in country
        else: # return records belonging to logged user only
            qs=qs.filter(user=user)      
        return qs # must return filter queryset to be displayed on admin interface

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, extra_context=None):
        ''' Customize add/edit form '''
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context["show_save"] = False
        extra_context['show_close'] = True
        return super(Facts_DataViewAdmin, self).change_view(
            request,object_id,extra_context=extra_context)
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set logged user during first save.
        super().save_model(request, obj, form, change)

    # exclude = ('user',)
    list_display=('fact_id','afrocode','indicator',
            'location','categoryoption','datasource','measure_type',
            'value_received','period','uhclock_theme','comment',)

    list_display_links = ('fact_id','indicator','datasource',)
    search_fields = ('afrocode','indicator','location',
        'measure_type','period','indicator') 
    list_per_page = 50 #limit records displayed on admin site to 30

    list_filter = (
        ('location',DropdownFilter,),
        ('datasource', DropdownFilter,),
        ('period',DropdownFilter),
        ('categoryoption', DropdownFilter,),
    )


@admin.register(CountrySelectionUHCIndicators)
class Country_IndicatorSelectionAdmin(OverideExport):
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            location__translations__language_code=language)
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
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    def get_domains(self, obj):
        return ", ".join([d.name for d in obj.domain.all()])
    get_domains.short_description = 'Selected UHC Clock Themes'
    
    list_display=['location','get_domains',]
    list_display_links = ['location','get_domains',]
