from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.admin import UserAdmin
from regions.models import StgLocation
from django.contrib.admin.models import LogEntry
from .models import CustomUser, CustomGroup,AhodctUserLogs
from . import models
from django.forms import TextInput,Textarea # customize textarea row and column
from django_admin_listfilter_dropdown.filters import (
    DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter,
    RelatedOnlyDropdownFilter) #custom


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'content_type', 'codename')
    list_filter = ('content_type__app_label', 'content_type')
    search_fields = (
        'name',
        'codename',
        'content_type__app_label',
        'content_type__model',
    )
    ordering = ('content_type__app_label', 'content_type__model', 'codename')

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(models.CustomUser)
class UserAdmin (UserAdmin):
    from django.db import models
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size':'100'})},
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':100})},
    }

    """
    We don't need to show list of permissions for non superuser admins. They
    just need to assign the groups which already are linked to the permissions
    """
    def get_fieldsets(self, request, obj=None):
          fieldsets = super(UserAdmin, self).get_fieldsets(request, obj)
         # This method hides permsions and super use attributes on the model form
          remove_fields = ['user_permissions','is_superuser']
          if not request.user.is_superuser:
              if len(fieldsets) > 0:
                  for f in fieldsets:
                      if f[0] == 'Account Permissions':
                          fieldsets[2][1]['fields'] = tuple(
                              x for x in fieldsets[2][1]['fields']
                              if not x in remove_fields)
                          break
          return fieldsets

    """
    For non-superusers, eg. Country admins, if they need to assign groups to
    other users, we only need to show groups in the Country admins location
    """
    def get_form(self, request, obj=None, **kwargs):
          form = super(UserAdmin, self).get_form(request, obj, **kwargs)
          if not request.user.is_superuser:
              filtered_groups = CustomGroup.objects.filter(
                  location=request.user.location)
              if form.base_fields.get('groups'):
                  form.base_fields['groups'].queryset=CustomGroup.objects.filter(
                      location=request.user.location)
          return form

    """
    The purpose of this method is to delegate limited role of creating users
    and groups to a non-superuser. This is achieved by assigning logged in user
    location to the user being created.
    """
    def save_model(self, request, obj, form, change):
        req_user = request.user
        if not req_user.is_superuser:
            obj.location = req_user.location
        super().save_model(request, obj, form, change)

    """
    The purpose of this method is to filter displayed list of users to location
    of logged in user
    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location
        if request.user.is_superuser:
            qs # return all instances of the request instances
        elif user in groups: # Fetch all instances of group membership
            qs=qs.filter(location=user_location)
        else:
            qs=qs.filter(username=user)
        return qs

    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location.location_id
        db_locations = StgLocation.objects.all().order_by('location_id')
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
                location_id=request.user.location_id).filter(
                translations__language_code=language).distinct()
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    readonly_fields = ('last_login','date_joined',)
    fieldsets = (
        ('Personal info', {'fields': ('title','first_name', 'last_name',
            'gender','location')}),
        ('Login Credentials', {'fields': ('email', 'username',)}),
        ('Account Permissions', {'fields': ('is_active', 'is_staff',
            'is_superuser', 'groups', 'user_permissions')}),
        ('Login Details', {'fields': ('last_login',)}),
    )
    limited_fieldsets = (
        ('Persional Details', {'fields': ('email',)}),
        ('Personal info', {'fields': ('first_name', 'last_name','location')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        ('Contacts and Password', {
            'classes': ('wide',),
            'fields': ('email','location', 'password1', 'password2')}
        ),
    )
    list_select_related = ('location',)
    list_display = ['first_name','last_name','gender','email','username',
        'location','last_login']
    list_display_links = ['first_name','last_name','username','email']


admin.site.unregister(Group)# Unregister the group in order to use custom group
@admin.register(models.CustomGroup)
class GroupAdmin(BaseGroupAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Get a query of groups the user belongs and flatten it to list object
        groups = list(request.user.groups.values_list('user', flat=True))
        user = request.user.id
        user_location = request.user.location
        if request.user.is_superuser:
            qs # return all instances of the request instances
        elif user in groups: # Fetch all instances of group membership
            qs=qs.filter(location=user_location)
        else:
            qs=qs.filter(username=user)
        return qs

    """
    The purpose of this method is to restrict display of permission selections
    in the listbox. Only permissions asigned to logged in user group are loaded.
    """
    def get_form(self, request, obj=None, **kwargs):
        form = super(GroupAdmin, self).get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            filtered_groups = CustomGroup.objects.filter(
                location=request.user.location)
            user_permissions = [f.permissions.all() for f in filtered_groups][0]
            if form.base_fields.get('permissions'):
                form.base_fields['permissions'].queryset = user_permissions
        return form

    def formfield_for_foreignkey(self, db_field, request =None, **kwargs):
        groups = list(request.user.groups.values_list('user', flat=True))
        language = request.LANGUAGE_CODE # get anguage code e.g. fr from request
        user = request.user.id
        user_location = request.user.location.location_id
        email = request.user.email

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

        if db_field.name == "roles_manager":
                kwargs["queryset"] = CustomUser.objects.filter(
                email=email)
        return super().formfield_for_foreignkey(db_field, request,**kwargs)

    # Override get_changeform_initial_data to autofill user field with logged user
    def get_changeform_initial_data(self, request):
        get_data = super(
        GroupAdmin,self).get_changeform_initial_data(request)
        get_data['roles_manager'] = request.user
        get_data['location'] = request.user.location
        return get_data

    """
    Overrride model_save method to grab id of the logged in user. The save_model
    method is given HttpRequest (request), model instance (obj), ModelForm
    instance (form), and boolean value (change) based on add or changes to object.
    """
    def save_model(self, request, obj, form, change):
        # import pdb; pdb.set_trace()
        if not obj.pk:
            obj.roles_manager = request.user # set user during the first save.
            obj.location = request.user.location # set location during first save.
        super().save_model(request, obj, form, change)

    exclude = ['roles_manager','location',]
    list_display = ['name','location','roles_manager']
    list_select_related = ('role','location',)


# This query unmanaged class allows the super admin to track user activities!
@admin.register(AhodctUserLogs)
class AhoDCT_LogsAdmin(admin.ModelAdmin):

    # This function removes the add button on the admin interface
    def has_delete_permission(self, request, obj=None):
        return False
        # This function removes the add button on the admin interface
    def has_add_permission(self, request, obj=None):
        return False
    #This method removes the save buttons from the model form
    def changeform_view(self,request,object_id=None,form_url='',
        extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False
        return super(AhoDCT_LogsAdmin, self).changeform_view(
            request, object_id, extra_context=extra_context)
 
    list_display=['first_name', 'last_name','email',
        'location_name','record_name','action','action_time',
        'last_login',]
    
    list_display_links = None # disable link to chage view form
    
    readonly_fields = ('first_name', 'last_name','email',
        'location_name','record_name','action','action_time',
        'last_login',)
    search_fields = ('first_name', 'last_name','email',
        'location_name','record_name','action',)
    list_filter = (
        ('record_name', DropdownFilter,),
        ('location_name', DropdownFilter,),
        ('action', DropdownFilter),
    )
    ordering = ('-action_time',)
