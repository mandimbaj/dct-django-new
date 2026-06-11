from django.contrib import admin
from django.db.models import Case, IntegerField, Value, When
from parler.admin import TranslatableAdmin
from django.utils.html import format_html
import data_wizard # Solution to data import madness that had refused to go
from django.forms import TextInput,Textarea #customize textarea row and column size
from import_export.formats import base_formats
from .models import (StgProductDomain,StgKnowledgeProduct,StgResourceType,
    StgResourceCategory,StgKnowledgeResourceTagging)
from commoninfo.admin import OverideImportExport,OverideExport

from commoninfo.admin_filters import (LocationFilter,KnowledgeResourceFilter)
from django_admin_listfilter_dropdown.filters import ChoiceDropdownFilter
from aho_datacapturetool.settings import *
from regions.models import StgLocation,StgLocationLevel
from regions.views import LocationSearchView
from .views import KnowledgeResourceSearchView
from django.urls import path

from .resources import (StgKnowledgeProductResourceExport,
    StgKnowledgeProductResourceImport,ProductDomainResourceExport,
    ProductTypeResourceExport,ProductCategoryResourceExport,)
from import_export.admin import (ImportExportModelAdmin, ExportMixin,
    ExportActionModelAdmin)

from authentication.models import CustomUser, CustomGroup
from .filters import TranslatedFieldFilter #Danile solution to duplicate filters
from .serializers import StgKnowledgeProductSerializer


#Methods used to register global actions performed on data. See actions listbox
def transition_to_pending (modeladmin, request, queryset):
    queryset.update(comment = 'pending')
transition_to_pending.short_description = "Mark selected as Pending"

def transition_to_approved (modeladmin, request, queryset):
    queryset.update (comment = 'approved')
transition_to_approved.short_description = "Mark selected as Approved"

def transition_to_rejected (modeladmin, request, queryset):
    queryset.update (comment = 'rejected')
transition_to_rejected.short_description = "Mark selected as Rejected"


@admin.register(StgResourceType)
class ResourceTypeAdmin(TranslatableAdmin,OverideExport):
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

    def get_export_resource_class(self):
        return ProductTypeResourceExport

    list_display=['name','code','shortname','description']
    list_display_links =('code', 'name',)
    search_fields = ('translations__name','translations__shortname','code',) #display search field
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)


@admin.register(StgResourceCategory)
class ResourceCategoryAdmin(TranslatableAdmin,OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).select_related(
                    'type').prefetch_related(
            'translations__master','type__translations').filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()
        return qs

    def get_export_resource_class(self):
        return ProductCategoryResourceExport

    fieldsets = (
        ('Resource Categorization', {
                'fields':('name','shortname','type','category',)
        }),
        ('Detailed Description', {
            'fields': ('description',),
        }),
    )
    list_display=['name','code','shortname','type','description']
    list_display_links =('code', 'name',)
    search_fields = ('translations__name','translations__shortname','code')
    list_per_page = 30 #limit records displayed on admin site to 15
    exclude = ('date_created','date_lastupdated','code',)


# data_wizard.register(
#     "Knowledge Resource Import", StgKnowledgeProductSerializer)
@admin.register(StgKnowledgeProduct)
class ProductAdmin(TranslatableAdmin,OverideExport,ExportActionModelAdmin):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('location_search/', self.admin_site.admin_view(
                LocationSearchView.as_view(model_admin=self)),
                    name='location_search'),
            path('products_search/', self.admin_site.admin_view(
                KnowledgeResourceSearchView.as_view(model_admin=self)),
                    name='products_search'),
            
        ]
        return custom_urls + urls
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
        qs = super().get_queryset(request).select_related(
            'user','type','location','categorization').prefetch_related(
            'translations','type__translations','location__translations').filter(
                translations__language_code=language).filter(
                type__translations__language_code=language).filter(
                location__translations__language_code=language).filter(
                location__translations__language_code=language).annotate(
                approval_priority=Case(
                    When(comment__iexact='pending', then=Value(0)),
                    When(comment__iexact='rejected', then=Value(1)),
                    When(comment__iexact='approved', then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            ).order_by(
                    'approval_priority',
                    'location__translations__name',
                    'translations__title',
                ).distinct()


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
        email = request.user.email
        language = request.LANGUAGE_CODE
        user_location = request.user.location.location_id

        if db_field.name == "location":
            if request.user.is_superuser:
                kwargs["queryset"] = StgLocation.objects.select_related(
                    'parent','locationlevel','wb_income','special').prefetch_related(
                    'translations__master',
                     # was throwing error due to locationlevel__master bad lookup
                     # the error was corrected on 19/07/2023 at 22:25 UTC+3
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

        if db_field.name == "type":
                kwargs["queryset"] = StgResourceType.objects.prefetch_related(
                'translations__master').filter(
                translations__language_code=language)

        if db_field.name == "categorization":
                kwargs["queryset"] = StgResourceCategory.objects.select_related(
                    'type').prefetch_related('translations__master').filter(
                translations__language_code=language).distinct()

        if db_field.name == "user":
            kwargs["queryset"] = CustomUser.objects.select_related(
                'location').prefetch_related('role',
                'location__translations__master').filter(email=email)
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    # display clickable URL for the external resource link
    def show_external_url(self, resource):
        if resource.external_url:
            return format_html(
                "<a href='{url}'>{url}</a>",url=resource.external_url
            )
        else:
            return "No link"
    show_external_url.allow_tags = True
    show_external_url.short_description= 'External Link'

    # display clickable URL for the nternal (azure blob) resource link
    def file_url(self, resource):
        if resource.internal_url:
            base_url = f'https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER}/'           
            filename = resource.internal_url.name
            link=base_url+filename         
            return format_html(
                "<a href='{url}'>{link}</a>",url=resource.internal_url.url,link=link
            )
        else:
            return "No file"
    file_url.allow_tags = True
    file_url.short_description = 'File Link'

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

    def get_export_resource_class(self):
        return StgKnowledgeProductResourceExport

    def get_import_resource_class(self):
        return StgKnowledgeProductResourceImport

     #This function is used to register permissions for approvals. See signals,py
    def get_actions(self, request):
        actions = super(ProductAdmin, self).get_actions(request)
        if not request.user.has_perm('publications.approve_stgknowledgeproduct'):
           actions.pop('transition_to_approved', None)
        if not request.user.has_perm('publications.reject_stgknowledgeproduct'):
            actions.pop('transition_to_rejected', None)
        if not request.user.has_perm('publications.delete_stgknowledgeproduct'):
            actions.pop('delete_selected', None)
        return actions

    def get_export_resource_class(self):
        return StgKnowledgeProductResourceExport

    def get_import_resource_class(self):
        return StgKnowledgeProductResourceImport


    """
    Overrride model_save method to grab id of the logged in user. The save_model
    method is given HttpRequest (request), model instance (obj), ModelForm
    instance (form), and boolean value (change) based on add or changes to object.
    """
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user # only set user during the first save.
        super().save_model(request, obj, form, change)


    exclude = ['user',]
    fieldsets = (
        ('Publication Attributes', {
                'fields':('title','type','categorization','location',)
            }),
            ('Description & Abstract', {
                'fields': ('description', 'abstract',),
            }),
            ('Attribution, Access and Approval Details', {
                'fields': ('author','year_published','internal_url',
                    'external_url','cover_image','comment'),
            }),
        )

    def get_location(obj):
           return obj.location.name
    get_location.short_description = 'Publication Place'

    def get_type(obj):
           return obj.type.name
    get_type.short_description = 'Type'

    # Format date created to disply only the day, month and year
    def date_created (obj):
        return obj.date_created.strftime("%d-%b-%Y")
    date_created.admin_order_field = 'date_created'
    date_created.short_description = 'Date Created'

    # use a more descriptive approval status column name
    def get_status(self, obj):
        return obj.get_comment_display()
    get_status.short_description = 'Status'


    # To display the choice field values use the helper method get_foo_display
    list_display=['title','code',get_type,'author','year_published',get_location,
        'file_url','show_external_url','get_status',date_created]
    list_select_related = ('user','type','categorization','location',)
    list_display_links = ['code','title',]
    readonly_fields = ('comment',)
    search_fields = ('translations__title','type__translations__name',
        'location__translations__name',) #display search field
    list_per_page = 50 #limit records displayed on admin site to 30
    actions = list(ExportActionModelAdmin.actions) + [transition_to_pending,
        transition_to_approved,transition_to_rejected]
    exclude = ('date_created','date_lastupdated','code','comment')
   
    list_filter = [('comment', ChoiceDropdownFilter), LocationFilter,KnowledgeResourceFilter,] # optimal solution to admin filter refactored 01/02/2023  



@admin.register(StgProductDomain)
class ProductDomainAdmin(TranslatableAdmin,OverideExport):
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

    def get_export_resource_class(self):
        return ProductDomainResourceExport

    fieldsets = (
        ('Resource Attributes', {
                'fields':('name','shortname','description','parent','level')
            }),
        ('Resource Publications', {
                'fields':('publications',) #afrocode may be null
            }),
        )

    list_select_related = ('parent',)
    list_display=['name','code','shortname','parent','level']
    list_display_links =('name','shortname','code',)
    search_fields = ('translations__name','translations__shortname','code',)

    filter_horizontal = ('publications',) # should display multiselect records
    exclude = ('date_created','date_lastupdated','code',)
    list_per_page = 50 #limit records displayed on admin site to 15
    list_filter = (
        ('parent',TranslatedFieldFilter),
        ('publications',TranslatedFieldFilter,),#Added 16/12/2019 for lookup
    )


@admin.register(StgKnowledgeResourceTagging)
class ResourceTaggingAdmin(OverideExport):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    def get_type(obj):
           return obj.publications.type.name
    get_type.short_description = 'Resource Type'

    def get_code(obj):
           return obj.publications.code
    get_code.short_description = 'Resource Code'

    def get_queryset(self, request):
        language = request.LANGUAGE_CODE
        qs = super().get_queryset(request).filter(
            publications__translations__language_code=language,
            location__translations__language_code=language,).order_by(
            'publications__translations__title').distinct()

        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user',flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        # db_locations = StgLocation.objects.all().order_by('location_id')

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

    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        language = request.LANGUAGE_CODE # get the en, fr or pt from the request
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

        if db_field.name == "publications":
                kwargs["queryset"] = StgKnowledgeProduct.objects.filter(
                translations__language_code=language).distinct()
        return super().formfield_for_foreignkey(db_field, request,**kwargs)
    list_display=['publications',get_code,get_type,'location',]
