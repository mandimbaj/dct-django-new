from django.contrib import admin
import data_wizard # Solution to data import madness that had refused to go
from django.forms import TextInput,Textarea #
from django.utils.html import format_html
from import_export.formats import base_formats
from parler.admin import TranslatableAdmin
from django_admin_listfilter_dropdown.filters import (
    DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter,
    RelatedOnlyDropdownFilter) #custom
from import_export.admin import (ImportExportModelAdmin, ExportMixin,
    ImportExportActionModelAdmin,ExportActionModelAdmin)
from commoninfo.admin import OverideImportExport,OverideExport,OverideImport
from .models import (ResourceTypeProxy,HumanWorkforceResourceProxy,
    StgInstitutionType,StgTrainingInstitution,StgHealthWorkforceFacts,
    ResourceCategoryProxy,StgHealthCadre,StgInstitutionProgrammes,
    StgRecurringEvent,StgAnnouncements)
from .resources import (HealthWorkforceResourceExport,HealthCadreResourceExport,
    TrainingInstitutionResourceExport,HealthWorkforceProductResourceExport,)

from regions.models import StgLocation,StgLocationLevel
from home.models import StgDatasource,StgCategoryoption,StgMeasuremethod
from authentication.models import CustomUser, CustomGroup
from .filters import TranslatedFieldFilter #Danile solution to duplicate filters
from publications.models import StgResourceType, StgResourceCategory
from commoninfo.wizard import DataWizardWorkforceFactsSerializer
from django.urls import path

from commoninfo.admin_filters import  (LocationFilter,DatasourceFilter,
    CategoryOptionFilter,HealthCadreFilter) # added 1/2/2023
from regions.views import LocationSearchView
from . views import HealthCadreSearchView
from home.views import CategoryOptionSearchView,DataourceSearchView


#Methods used to register global actions performed on data. See actions listbox
def transition_to_pending (modeladmin, request, queryset):
    queryset.update(status = 'pending')
transition_to_pending.short_description = "Mark selected as Pending"

def transition_to_approved (modeladmin, request, queryset):
    queryset.update (status = 'approved')
transition_to_approved.short_description = "Mark selected as Approved"

def transition_to_rejected (modeladmin, request, queryset):
    queryset.update (status = 'rejected')
transition_to_rejected.short_description = "Mark selected as Rejected"


@admin.register(ResourceTypeProxy)
class ResourceTypeAdmin(TranslatableAdmin):
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

    list_display=['name','code','description',]
    list_display_links =('code', 'name',)
    search_fields = ('code','translations__name',) #display search field
    list_per_page = 15 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)


@admin.register(ResourceCategoryProxy)
class ResourceCategoryAdmin(TranslatableAdmin):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request): # Filter only categories relating to HWF
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).filter(category=2).order_by(
            'translations__name').distinct()
        return qs

    list_display=['name','code','description',]
    list_display_links =('code', 'name',)
    search_fields = ('code','translations__name',) #display search field
    list_per_page = 15 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)


@admin.register(StgInstitutionType)
class InsitutionTypeAdmin(TranslatableAdmin):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    list_display=['name','code','shortname','description']
    list_display_links =('code', 'name','shortname')
    search_fields = ('code','translations__name','translations__shortname')
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)


@admin.register(StgInstitutionProgrammes)
class ProgrammesAdmin(TranslatableAdmin):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    list_display=['name','code','description']
    list_display_links =('code', 'name',)
    search_fields = ('code','translations__name',) #display search field
    list_per_page = 15 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)


@admin.register(HumanWorkforceResourceProxy)
class ResourceAdmin(TranslatableAdmin,ExportActionModelAdmin):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_export_resource_class(self):
        return HealthWorkforceProductResourceExport
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
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__title').filter(
            location__translations__language_code=language).order_by(
            'location__translations__name').distinct()
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        
        user_uuid = request.user.location.locationlevel.uuid
        user_level= StgLocationLevel.objects.get(uuid=user_uuid)

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
    Serge requested that the form for input be restricted to user's location.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.=== modified 02/02/2021
    """
    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        language = request.LANGUAGE_CODE
        user = request.user.id
        email = request.user.email
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
            
            if db_field.name == "type":
                    kwargs["queryset"] = StgResourceType.objects.prefetch_related(
                    'translations__master').filter(
                    translations__language_code=language)

            if db_field.name == "categorization":
                    kwargs["queryset"] = StgResourceCategory.objects.select_related(
                    'type').prefetch_related('translations__master').filter(
                translations__language_code=language).distinct()


        if db_field.name == "user":
                kwargs["queryset"] = CustomUser.objects.filter(
                    email=email)
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    #to make URl clickable, I changed show_url to just url in the list_display tuple
    def show_external_url(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.external_url)

    def show_url(self, obj):
        return obj.url if obj.url else 'None'

    show_external_url.allow_tags = True
    show_external_url.short_description= 'External File Link'

    """
    Returns available export formats.
    """
    def get_import_formats(self):
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_import()]

    def get_export_formats(self):
        """
        Returns available export formats.
        """
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_export()]

    def get_location(obj):
           return obj.location.name
    get_location.short_description = 'Location'

    def get_type(obj):
           return obj.type.name
    get_type.short_description = 'Type'

    """
    Method added 14/02/2024 due error user_id cannot be null
    First overrride model_save method to get id of the logged in user.
    """
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # only set user during the first save.
        super().save_model(request, obj, form, change)

     #This function is used to register permissions for approvals.See signals,py
    def get_actions(self, request):
        actions = super(ResourceAdmin, self).get_actions(request)
        if not request.user.has_perm('resources.approve_stgknowledgeproduct'):
           actions.pop('transition_to_approved', None)
        if not request.user.has_perm('resources.reject_stgknowledgeproduct'):
            actions.pop('transition_to_rejected', None)
        if not request.user.has_perm('resources.delete_stgknowledgeproduct'):
            actions.pop('delete_selected', None)
        return actions

    actions = list(ExportActionModelAdmin.actions) + [transition_to_pending,
        transition_to_approved,transition_to_rejected]

    fieldsets = (
        ('Publication Attributes', {
                'fields':('title','type','categorization','location',)
            }),
            ('Description & Abstract', {
                'fields': ('description', 'abstract',),
            }),
            ('Attribution & Access Details', {
                'fields': ('author','year_published','internal_url',
                    'external_url','cover_image',),
            }),
        )
    list_display=['title','code','author',get_type,get_location,'year_published',
        'internal_url','show_external_url','cover_image','get_comment_display']
    list_display_links = ['code','title',]
    readonly_fields = ('comment',)
    search_fields = ('translations__title','type__translations__name',
        'location__translations__name',) #display search field
    list_per_page = 30 #limit records displayed on admin site to 30
    exclude = ('date_created','date_lastupdated','code',)
    list_filter = (
        ('location',TranslatedFieldFilter),
        ('type',TranslatedFieldFilter),
        ('categorization',TranslatedFieldFilter),
    )


@admin.register(StgTrainingInstitution)
class TrainingInsitutionAdmin(TranslatableAdmin,OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_export_resource_class(self):
        return TrainingInstitutionResourceExport

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
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        user_uuid = request.user.location.locationlevel.uuid
        user_level= StgLocationLevel.objects.get(uuid=user_uuid)

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
    Serge requested that the form for input be restricted to user's location.
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

        if db_field.name == "user":
                kwargs["queryset"] = CustomUser.objects.filter(
                email=email)
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    """
    Overrride model_save method to grab id of the logged in user. The save_model
    method is given HttpRequest (request), model instance (obj), ModelForm
    instance (form), and boolean value (change) based on add or changes to object.
    """
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set user from request during the first save.
        super().save_model(request, obj, form, change)

    fieldsets = (
        ('Institution Details',{
                'fields': (
                    'name', 'type','accreditation','accreditation_info','regulator')
            }),

            ('Contact Details', {
                'fields': ('location','address','posta','email','phone_number',
                'url', 'latitude','longitude'),
            }),
            ('Academic Details', {
                'fields': ( 'faculty','language','programmes',),
            }),
        )

    filter_horizontal = ('programmes',) # this should display  inline with multiselect
    list_display=['name','type','code','location','url','email']
    list_display_links = ('code', 'name',) #display as clickable link
    search_fields = ('location__translations__name','translations__name',
        'type__translations__name') #display search field
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated',)
    list_filter = (
        ('location',TranslatedFieldFilter),
        ('type',TranslatedFieldFilter),
    )


@admin.register(StgHealthCadre)
class HealthCadreAdmin(TranslatableAdmin,OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request): # Filter only categories relating to HWF
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        return qs

    def get_export_resource_class(self):
        return HealthCadreResourceExport

    fieldsets = (
        ('Occulation/Cadre Details',{
                'fields': (
                    'name', 'shortname','code','description','academic','parent')
            }),
    )
    list_display=['name','code','shortname','description','academic','parent']
    list_display_links = ('code', 'shortname','name',) #display as clickable link
    search_fields = ('code','translations__name', 'translations__shortname',)
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated',)
    list_filter = (
        ('parent',TranslatedFieldFilter),
    )


# Register data import wizard for the custom serializer defined in common.wizard.py
data_wizard.register(
    "HealthWorkforce Import", DataWizardWorkforceFactsSerializer)

@admin.register(StgHealthWorkforceFacts)
class HealthworforceFactsAdmin(ExportActionModelAdmin,OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('location_search/', self.admin_site.admin_view(
                LocationSearchView.as_view(model_admin=self)),name='location_search'),
            path('cadre_search/', self.admin_site.admin_view(
                HealthCadreSearchView.as_view(model_admin=self)),name='cadre_search'),
            path('categories_search/', self.admin_site.admin_view(
                CategoryOptionSearchView.as_view(model_admin=self)),name='categories_search'),
            path('source_search/', self.admin_site.admin_view(
                DataourceSearchView.as_view(model_admin=self)), name='source_search'),
        ]
        return custom_urls + urls

    def get_export_resource_class(self):
        return HealthWorkforceResourceExport

    # Format date created to disply only the day, month and year
    def date_created (obj):
        return obj.date_created.strftime("%d-%b-%Y")
    date_created.admin_order_field = 'date_created'
    date_created.short_description = 'Date Created'

    # Override get_changeform_initial_data to fill user field with logged in user
    def get_changeform_initial_data(self, request):
        get_data = super(
        HealthworforceFactsAdmin,self).get_changeform_initial_data(request)
        get_data['user'] = request.user.pk
        return get_data

    """
    Serge requested that the form for data input be restricted to user's location.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.===modified 02/02/2021
    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            cadre__translations__language_code=language).order_by(
            'cadre__translations__name').filter(
            location__translations__language_code=language).order_by(
            'location__translations__name').distinct()
        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id

        user_uuid = request.user.location.locationlevel.uuid
        user_level= StgLocationLevel.objects.get(uuid=user_uuid)

        
        qs = qs.select_related('location','cadre','categoryoption', 
            'datasource','measuremethod','user').prefetch_related(
            'location__translations','cadre__translations',
            'categoryoption__translations','datasource__translations',
            'measuremethod__translations').only(
            'location','cadre','categoryoption','datasource',
            'measuremethod','user','value','period','status',
            'date_created','user__id','location__location_id',
            'cadre__cadre_id','categoryoption__categoryoption_id',
            'datasource__datasource_id','measuremethod__measuremethod_id',
            'start_year','end_year',).filter(
                cadre__translations__language_code=language).order_by(
            'cadre__translations__name').filter(
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
        user = request.user.id
        email = request.user.email
        language = request.LANGUAGE_CODE
        user_location = request.user.location.location_id
        
        if db_field.name == "location":
            if request.user.is_superuser:
                kwargs["queryset"] = StgLocation.objects.select_related(
                    'parent','locationlevel','wb_income','special').prefetch_related(
                    'translations__master',
                    # Multi-level location lookup to address N+1 query problem
                    'locationlevel__locationlevel_id__master').order_by(
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
                    'translations__master',
                    # Multi-level location lookup to address N+1 query problem
                    'locationlevel__locationlevel_id__master').filter(
                    location_id=request.user.location_id).translated(
                    language_code=language).order_by(
                    'locationlevel','translations__name').filter(
                    translations__language_code=language)

        if db_field.name == "cadre":
            kwargs["queryset"] = StgHealthCadre.objects.select_related(
                'parent',).prefetch_related(
                'translations__master',).filter(
                    translations__language_code=language).order_by(
                'translations__name')

        if db_field.name == "categoryoption":
            kwargs["queryset"] = StgCategoryoption.objects.select_related(
                'category').prefetch_related('translations__master').filter(
                translations__language_code=language).order_by(
                'translations__name')

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

    """
    Returns available export formats.
    """
    def get_import_formats(self):
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_import()]

    def get_export_formats(self):
        """
        Returns available export formats.
        """
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_export()]

    def get_actions(self, request):
        actions = super(HealthworforceFactsAdmin, self).get_actions(request)
        if not request.user.has_perm('health_workforce.approve_stghealthworkforcefacts'):
           actions.pop('transition_to_approved', None)
        if not request.user.has_perm('health_workforce.reject_stghealthworkforcefacts'):
            actions.pop('transition_to_rejected', None)
        if not request.user.has_perm('health_workforce.delete_stghealthworkforcefacts'):
            actions.pop('delete_selected', None)
        return actions

    """
    Overrride model_save method to grab id of the logged in user. The save_model
    method is given HttpRequest (request), model instance (obj), ModelForm
    instance (form), and boolean value (change) based on add or changes to object.
    """
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # set user from request during the first save.
            obj.location = request.user.location # set location during first save.
        super().save_model(request, obj, form, change)

    fieldsets = (
        ('Health Occulation/Cadre Data',{
                'fields': (
                    'cadre','categoryoption','datasource','location',)
        }),
        ('Reporting Period & Values', {
            'fields':('start_year','end_year','measuremethod','value',)
        }),
    )
    list_display=['cadre','location','categoryoption','period','value','status',
        date_created,]
    list_display_links = ('cadre', 'location',) #display as clickable link
    search_fields = ('location__translations__name','cadre__translations__name',
        'period') #display search field
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated',)

    actions = list(ExportActionModelAdmin.actions) + [transition_to_pending,
        transition_to_approved,transition_to_rejected,]


    list_filter = [LocationFilter, DatasourceFilter,HealthCadreFilter,
                   CategoryOptionFilter]


@admin.register(StgRecurringEvent)
class RecurringEventsAdmin(TranslatableAdmin):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    """
    Serge requested that the form for data input be restricted to user location.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.===modified 02/02/2021
    """
    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        user_uuid = request.user.location.locationlevel.uuid
        user_level= StgLocationLevel.objects.get(uuid=user_uuid)

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
    Serge requested that the form for input be restricted to user's location.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.=== modified 02/02/2021
    """
    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        language = request.LANGUAGE_CODE
        user_location = request.user.location.location_id
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
        return super().formfield_for_foreignkey(db_field,request,**kwargs)

    #to make URl clickable, I changed show_url to just url in the list_display tuple
    def show_external_url(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.external_url)

    def show_url(self, obj):
        return obj.url if obj.url else 'None'

    show_external_url.allow_tags = True
    show_external_url.short_description= 'Web Link (URL)'

    """
    Returns available export formats.
    """
    def get_import_formats(self):
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_import()]

    def get_export_formats(self):
        """
        Returns available export formats.
        """
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_export()]

    fieldsets = (
        ('Event Details', {
                'fields':('name','shortname','theme','start_year',
                'end_year','status') #afrocode may be null
            }),
            ('Target Focus and Location', {
                'fields': ('location', 'cadre',),
            }),
            ('Files and Web Resources', {
                'fields': ('internal_url','external_url','cover_image'),
            }),
        )
    filter_horizontal = ['cadre'] # this should display multiselect boxes
    list_display=['name','code','shortname','theme','period','internal_url',
        'show_external_url']
    list_display_links = ['name','code']
    search_fields = ('name','shortname','location__name',) #display search field
    list_per_page = 30 #limit records displayed on admin site to 30
    exclude = ('date_created','date_lastupdated','code',)
    list_filter = (
        ('location',TranslatedFieldFilter),
    )


@admin.register(StgAnnouncements)
class EventsAnnouncementAdmin(TranslatableAdmin):
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
        qs = super().get_queryset(request).filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')

        user_uuid = request.user.location.locationlevel.uuid
        user_level= StgLocationLevel.objects.get(uuid=user_uuid)
        
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
    Serge requested that the form for input be restricted to user's location.
    Thus, this function is for filtering location to display country level.
    The location is used to filter the dropdownlist based on the request
    object's USER, If the user has superuser privileges or is a member of
    AFRO-DataAdmins, he/she can enter data for all the AFRO member countries
    otherwise, can only enter data for his/her country.=== modified 02/02/2021
    """
    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        language = request.LANGUAGE_CODE
        user_location = request.user.location.location_id
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
        return super().formfield_for_foreignkey(db_field,request,**kwargs)

    #to make URl clickable, I changed show_url to just url in the list_display tuple
    def show_external_url(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.external_url)

    def show_url(self, obj):
        return obj.url if obj.url else 'None'

    show_external_url.allow_tags = True
    show_external_url.short_description= 'Web Link (URL)'

    """
    Returns available export formats.
    """
    def get_import_formats(self):
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_import()]

    def get_export_formats(self):
        """
        Returns available export formats.
        """
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_export()]

    fieldsets = (
        ('Event Details', {
                'fields':('name','shortname','message','start_year',
                'end_year','location','status') #afrocode may be null
            }),
            ('Files and Web Resources', {
                'fields': ('internal_url','external_url','cover_image'),
            }),
        )
    list_display=['name','location','message','period','internal_url',
        'show_external_url']
    list_display_links = ['name','location',]
    search_fields = ('name','shortname','location__name',) #display search field
    list_per_page = 50 #limit records displayed on admin site to 30
    exclude = ('date_created','date_lastupdated','code',)
    list_filter = (
        ('location',TranslatedFieldFilter),
    )
