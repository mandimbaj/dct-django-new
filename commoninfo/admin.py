
from django.contrib import admin
from django.contrib.admin import AdminSite #customize adminsite
#these libraries are imported to support monkey of admin_menu package
from django.urls import resolve, reverse, NoReverseMatch
from django.utils.text import capfirst
#import custom menu for customization to change apps order
from admin_menu.templatetags import custom_admin_menu
from import_export.admin import (ImportExportModelAdmin, ExportActionModelAdmin,
    ExportMixin,ImportMixin,ExportActionModelAdmin,ImportExportActionModelAdmin) #added exportaction mixin only
from import_export.formats import base_formats
from django.utils.translation import gettext_lazy as _
# Customize the site admin header for login, title bar, and data admin form section.
class AdminSite(AdminSite):
    site_header = 'African Health Observatory' #also shown on login form
    site_title = 'AHO Data Capture and Admin Tool' #shown on the title bar
    index_title = 'African Health Observatory Data Management' #shown in the content section

# #Import this method and do nothing to it. It is required by get_app_list()!!
def get_admin_site(context):
    pass

get_admin_site = custom_admin_menu.get_admin_site #assign as is!

# This is the method that does the menu tweaks using the ordering dict!!!
def get_app_list(context, order=True):
    admin_site = get_admin_site(context)
    request = context['request']
    language = request.LANGUAGE_CODE
    # import pdb; pdb.set_trace()


    app_dict = {}
    for model, model_admin in admin_site._registry.items():
        app_label = model._meta.app_label
        try:
            has_module_perms = model_admin.has_module_permission(request)
        except AttributeError:
            has_module_perms = request.user.has_module_perms(app_label)

        if has_module_perms:
            perms = model_admin.get_model_perms(request)

            # Check whether user has any perm for this model.
            # If so, add the model to the model_dict.
            if True in perms.values():
                info = (app_label, model._meta.model_name)
                model_dict = {
                    'name': capfirst(model._meta.verbose_name_plural),
                    'object_name': model._meta.object_name,
                    'perms': perms,
                    'model_admin': model_admin,
                }
                if perms.get('change', False):
                    try:
                        model_dict['admin_url'] = reverse(
                        'admin:%s_%s_changelist'%info,current_app=admin_site.name)
                    except NoReverseMatch:
                        pass
                if perms.get('add', False):
                    try:
                        model_dict['add_url'] = reverse(
                        'admin:%s_%s_add' % info, current_app=admin_site.name)
                    except NoReverseMatch:
                        pass
                if app_label in app_dict:
                    app_dict[app_label]['models'].append(model_dict)
                else:
                    try:
                        name = apps.get_app_config(app_label).verbose_name
                    except NameError:
                        # Workround to rename main horizontal menu for translation; added on 02/01/2024
                        if app_label.title().upper() == 'HOME':
                            name =_("HOME") # rename home menu for translation
                        elif app_label.title().upper() == 'INDICATORS':
                            name =_("INDICATORS") # rename indicators menu for translation
                        elif app_label.title().upper() == 'PUBLICATIONS':
                            name =_("PUBLICATIONS") # rename publications menu for translation
                        elif app_label.title().upper() == 'FACILITIES':
                            name =_("FACILITIES") # rename health facilities menu for translation
                        elif app_label.title().upper() == 'REGIONS':
                            name =_("REGIONS") # rename regions menu for translation
                        elif app_label.title().upper() == 'AUTHENTICATION':
                            name =_("AUTHENTICATION") # rename regions menu for translation

                        elif app_label.title().upper() == 'UHC_CLOCK':
                            name =_("UHC CLOCK") # rename UHC_Clock menu
                        elif app_label.title().upper() == 'AUTHTOKEN':
                            name =_("API TOKENS") # rename authtoken menu
                        elif app_label.title().upper() == 'HEALTH_WORKFORCE':
                            name =_("HEALTH WORKFORCE") # rename health_workforce menu
                        elif app_label.title().upper() == 'HEALTH_SERVICES':
                            name =_("HEALTH SERVICES") # rename health_services menu
                        elif app_label.title().upper() == 'ELEMENTS':
                            name =_("DATA ELEMENTS") # rename data elements menu
                        elif app_label.title().upper() == 'DATA_WIZARD':
                            name =_("DATA WIZARD") # rename data import wizard menu
                        elif app_label.title().upper() == 'DATA_QUALITY':
                            name =_("DATA QUALITY") # rename data quality menu
                            
                        else:
                             name = app_label.title().upper() # use default app name but convert to uppercase
                    
                    app_dict[app_label] = {
                        'name': name,
                        'app_label': app_label,
                        'app_url': reverse(
                            'admin:app_list',
                            kwargs={'app_label': app_label},
                            current_app=admin_site.name,
                        ),
                        'has_module_perms': has_module_perms,
                        'models': [model_dict],
                    }

    # This dict orders app names based on English (en) translations
    if language == 'en':
        ordering = {
            'Home':1,
            'Indicators':2,
            'Publications':3,
            'Facilities':4,
            'Health Workforce':5, # Health_Workforce
            'Health Services':6, # Health_Services
            'Data Elements':7, # Elements
            'Regions':8,
            'Data Wizard':9, # Data_Wizard
            'Data Quality':10, # Data_Quality
            'api tokens':11, # Authtoken
            'Authentication':12,
            'UHC Clock':13,
        }

    # This dict orders app names based on French (fr) translations
    elif language == 'fr':
        ordering = {
            'ACCUEIL':1,
            'INDICATEURS':2,
            'PUBLICATIONS':3,
            'ÉTABLISSEMENTS':4,
            'PERSONNEL DE SANTÉ':5, # Health_Workforce
            'SERVICES DE SANTÉ':6, # Health_Services
            'ÉLÉMENTS DE DONNÉES':7, # Elements
            'Régions':8,
            'IMPORT DE DONNÉES':9, # Data_Wizard
            'QUALITÉ DES DONNÉES':10, # Data_Quality
            "TOKENS D'API":11, # Authtoken
            'AUTHENTIFICATION':12,
            "HORLOGE DE L'UHC":13,
        }

    # This dict orders app names based on portuguese (pt) translations
    elif language == 'pt':
        ordering = {
            'CASA':1,
            'INDICADORES':2,
            'PUBLICAÇÕES':3,
            'INSTALAÇÕES DE SAÚDE':4,
            'PESSOAL DA SAÚDE':5, # Health_Workforce
            'SERVIÇOS DE SAÚDE':6, # Health_Services
            'ELEMENTOS DE DADOS':7, # Elements
            'REGIÕES':8,
            'ASSISTENTE DE DADOS':9, # Data_Wizard
            'QUALIDADE DOS DADOS':10, # Data_Quality
            'TOQUES API':11, # Authtoken
            'AUTENTICAÇÃO':12,
            'RELÓGIO DE UHC':13,
        }
    
    # This dict orders app names based on default app name (app_label)
    else:
        ordering = {
            'Home':1,
            'Indicators':2,
            'Publications':3,
            'Facilities':4,
            'Health_Workforce':5,
            'Health_Services':6,
            'Elements':7,
            'Regions':8,
            'Data_Wizard':9,
            'Data_Quality':10,
            'Authtoken':11,
            'Authentication':12,
            'UHC_Clock':13,
        }

    ordering =  {k.upper(): v for k, v in ordering.items()}   
    # Create the list to be sorted using the ordering dict.
    app_list = list(app_dict.values())
    
    if order:
        app_list.sort(key=lambda x: ordering.get(x['name'], 999))
        # Sort the models alphabetically within each app.
        for app in app_list:
            app['models'].sort(key=lambda x: x['name'])
    
    return app_list
  
# Apply language translated navigation menu in uppercase
custom_admin_menu.get_app_list = get_app_list


class OverideImportExport(ImportExportModelAdmin):
    def get_import_formats(self):
        # Returns available import/export formats.
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_import()]

    def get_export_formats(self):
        # Returns available import/export formats.
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_export()]

# Used to override export base format types to limit to only CSV,XLS and XLSx
class OverideExport(ExportMixin, admin.ModelAdmin):
    def get_export_formats(self):
        # Returns available export formats.
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_export()]


# Used override export base format types to limit to only CSV,XLS and XLSx
class OverideExportAdmin(ExportActionModelAdmin, ExportMixin, admin.ModelAdmin):
    def get_export_formats(self):
        # Returns available export formats.
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_export()]

# Used to override import base format types to limit to only CSV,XLS and XLSx
class OverideImport(ImportMixin, admin.ModelAdmin):
    def get_import_formats(self):
        # Returns available import formats.
        formats = (
              base_formats.CSV,
              base_formats.XLS,
              base_formats.XLSX,
        )
        return [f for f in formats if f().can_import()]
