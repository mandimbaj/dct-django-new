from django.contrib import admin
from parler.admin import TranslatableAdmin
from django.forms import TextInput,Textarea #for customizing textarea row and column size
from .models import (StgLocationLevel,StgEconomicZones,StgWorldbankIncomegroups,
    StgSpecialcategorization,StgLocation,StgLocationCodes,)
from django_admin_listfilter_dropdown.filters import (
    DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter,
    RelatedOnlyDropdownFilter) #custom
from commoninfo.admin import OverideExport,OverideImportExport,OverideImport
from .resources import (LocationLevelResourceExport,IncomegroupsResourceExport,
    EconomicZoneResourceExport,SpecialcategorizationResourceExport,
    LocationResourceExport,LocationResourceImport)
from import_export.admin import (ExportMixin, ImportExportModelAdmin,
    ImportExportActionModelAdmin,)
#This is required to limit the import/export fields 26/10/2018
from import_export import resources
from .filters import TranslatedFieldFilter #Danile solution to duplicate filters

#the following 3 functions are used to register global actions performed on data
def pending (modeladmin, request, queryset):
    queryset.update(comment = 'pending')
pending.short_description = "Mark selected as Pending"

def approved (modeladmin, request, queryset):
    queryset.update (comment = 'approved')
approved.short_description = "Mark selected as Approved"

def rejected (modeladmin, request, queryset):
    queryset.update (comment = 'rejected')
rejected.short_description = "Mark selected as Rejected"


@admin.register(StgLocationLevel)
class RegionAdmin(TranslatableAdmin,OverideExport):
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

    resource_class = LocationLevelResourceExport
    list_display=['name','code','type','description',]
    list_display_links = ('code', 'name',)
    search_fields = ('code','translations__name','translations__type')
    list_per_page = 15 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)
    list_filter = (
        ('translations__name',DropdownFilter),
    )

@admin.register(StgEconomicZones)
class EconomicBlocksAdmin(TranslatableAdmin,OverideExport):
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

    resource_class = EconomicZoneResourceExport
    list_display=['name','code','shortname','description',]
    list_display_links = ('code', 'name',)
    search_fields = ('translations__name','translations__shortname','code')
    list_per_page = 15 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code')


@admin.register(StgWorldbankIncomegroups)
class WBGroupsAdmin(TranslatableAdmin,OverideExport):
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

    resource_class = IncomegroupsResourceExport
    list_display=['name','code','shortname','description',]
    list_display_links = ('code', 'name',)
    search_fields = ('code','translations__name','translations__shortname')
    list_per_page = 15 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)


@admin.register(StgSpecialcategorization)
class SpecialStatesAdmin(TranslatableAdmin,OverideExport):
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

    resource_class = SpecialcategorizationResourceExport
    list_display=['name','code','shortname','description',]
    list_display_links = ('code', 'name',)
    search_fields = ('translations__name','translations__shortname','code')
    list_per_page = 15 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code')


@admin.register(StgLocation)
class LocationAdmin(TranslatableAdmin,OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    """
    Serge requested that the form for data input be restricted to user's location.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.===modified 02/02/2021
    """
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        db_locations = StgLocation.objects.all().order_by('location_id')
        user_location = request.user.location.location_id
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct().filter(
            locationlevel__translations__language_code=language).order_by(
            'locationlevel__translations__name').distinct()
        return qs

    """
    Serge requested that the form for input be restricted to user's location.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.=== modified 02/02/2021
    """
    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        language = request.LANGUAGE_CODE # get the en, fr or pt from the request
        user = request.user.id
        user_location = request.user.location.location_id

        if db_field.name == "parent":
            if request.user.is_superuser:
                kwargs["queryset"] = StgLocation.objects.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=3).order_by(
                'location_id')
                # Looks up for the location level upto the country level
            elif user in groups and user_location==1:
                kwargs["queryset"] = StgLocation.objects.filter(
                locationlevel__locationlevel_id__gte=1,
                locationlevel__locationlevel_id__lte=2).order_by(
                'location_id')
            else:
                kwargs["queryset"] = StgLocation.objects.filter(
                location_id=user_location).translated(
                language_code=language)
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    fieldsets = (
        ('Location Details',{
                'fields': (
                    'locationlevel','name','iso_alpha','iso_number',
                    'description','wb_income','special', )
            }),
            ('Geo-map Info', {
                'fields': ('parent','longitude','latitude', 'cordinate',),
            }),
            ('Socioeconomic Status', {
                'fields': ('zone',),
            }),
        )
    resource_class = LocationResourceExport
    filter_horizontal = ('zone',)
    list_display=['name','code','parent','wb_income','locationlevel',]
    list_select_related = ('parent','locationlevel','wb_income','special',)
    list_display_links = ('code', 'name',) #display as clickable link
    search_fields = ('translations__name','code',) #display search field

    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated',)
    list_filter = (
        ('locationlevel',TranslatedFieldFilter),
        ('parent',TranslatedFieldFilter),
    )


@admin.register(StgLocationCodes)
class LocationCodesAdmin(admin.ModelAdmin):
    """
    This method filters logged in users depending on group roles and permissions.
    Only the superuser can see all users and locations data while a users
    can only see data from registered location within his/her group/system role.
    If a user is not assigned to a group, he/she can only own data - 01/02/2021
    """
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            location__translations__language_code=language).order_by(
            'location__translations__name').distinct()
        return qs

    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        language = request.LANGUAGE_CODE
        user = request.user.id
        user_location = request.user.location.location_id

        if db_field.name == "location":
            if request.user.is_superuser:
                kwargs["queryset"] = StgLocation.objects.all().order_by(
                'location_id').filter(translations__language_code=language)
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



    list_display=('location','country_code',)
    list_select_related = ('location',)
    search_fields = ('location','country_code',) #display search field

    list_per_page = 50 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated',)
    list_filter = (
        ('location',TranslatedFieldFilter),
    )
