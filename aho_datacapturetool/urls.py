"""
Global DCT App URL route Configurations points the URL patterns to views
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import path,include,re_path
from home import admin_views, views
from django.conf.urls.i18n import i18n_patterns #added
from django.views.static import serve # hack to support display of uploaded files
from django.conf import settings # Facilitate viewing on browser pdf reader
from django.conf.urls.static import static # Facilitate display of static assets
from django.conf.urls import handler404,handler500 # display custom 404 error page
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView,)
try:
    from rest_framework.documentation import (
        include_docs_urls, get_schemajs_view)
except ImportError:
    include_docs_urls = None
    get_schemajs_view = None
try:
    from rest_framework_swagger.views import get_swagger_view
except ImportError:
    get_swagger_view = None

from rest_framework.authtoken.views import obtain_auth_token


# admin.autodiscover() # Autoloads the custom login page instead of auth.admin view
admin.site.login = login_required(admin.site.login)

admin.site.site_header="DCT Admin"
admin.site.site_title="DCT Admin"
admin.site.index_title="DCT Admin"

schema_view = (
    get_swagger_view(title='Data Capture Tool API Endpoints')
    if get_swagger_view else None
)

api_patterns = []
if schema_view:
    api_patterns.append(
        path('', schema_view, name='swagger_docs') # Load swagger docs page 3/5/21
    )

api_patterns += [
    # path('', include('router.urls',namespace='api')),
    path('', include(('regions.urls','regions'),namespace='regions')),
    path('', include(('indicators.urls','indicators'),namespace='indicators')),
    path('', include(('publications.urls','publications'),namespace='publications')),
    path('', include(('elements.urls', 'elements'), namespace='elements')),
    path('', include(('home.urls', 'home'), namespace='home')),
    path('', include(('facilities.urls', 'facilities'), namespace='facilities')),
    path('', include(('health_workforce.urls','health_workforce'),
        namespace='health_workforce')),
    path('', include(('health_services.urls', 'health_services'),
        namespace='health_services')),
]

"""
This pattern was added on 25/10/2020 to allow setting of the base/root URL to
 include language selected from the login form once the used selects en, fror pt
 """
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')), #Important for language selection
]

urlpatterns += i18n_patterns ( # must be python immutable list () and not []
    path('', views.login, name="login"),
    path('logout/', views.logout, name='logout'),
    # This pattern is used to redirect native auth to custom view and template
    path('admin/logout/', lambda request: redirect(
        '/microsoft_authentication/logout', permanent=False)),
    path('admin/indicators/imports/', admin_views.indicator_imports, name='aho_indicator_imports'),
    path('admin/indicators/exports/', admin_views.indicator_exports, name='aho_indicator_exports'),
    path('admin/data-integration/connections/', admin_views.data_integration_connections, name='aho_data_integration_connections'),
    path('admin/data-integration/failed-rows/', admin_views.data_integration_failed_rows, name='aho_data_integration_failed_rows'),
    path('admin/data-quality/indicator-checks/', admin_views.data_quality_indicator_checks, name='aho_data_quality_indicator_checks'),
    path('admin/data-quality/facts-dataset/', admin_views.data_quality_facts_dataset, name='aho_data_quality_facts_dataset'),
    path('admin/api-tokens/token-status/', admin_views.api_token_status, name='aho_api_token_status'),
    path('admin/global-search/', admin_views.global_search, name='aho_global_search'),
    path('admin/row-action/', admin_views.row_action, name='aho_row_action'),
    path('admin/quality/',include('data_quality.urls',namespace='data_quality')),
    path('admin/', admin.site.urls,name='dashboard'),
    path('microsoft_authentication/', include('authentication.urls')),
    path('datawizard/', include('data_wizard.urls')), #for data import wizard
    #Daniel support to validate A->B->C pupolated selection in facility services
    path('chaining/', include('smart_selects.urls')),
   #Reset and Changepassword urls
    path('password-reset/', auth_views.PasswordResetView.as_view(),
        name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(),
        name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'),
    path('password-change/', auth_views.PasswordChangeView.as_view(),
        name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(),
        name='password_change_done'),

   # API-based URL patterns for hitting KHRO endpoints for consuming data in JSON
    path('api/', include((api_patterns, 'api'), namespace='api')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api-auth/', include('rest_framework.urls')), # For browsable REST API
    path('api/auth-token/', obtain_auth_token),# added 23/08/2023 to generate tokens

    # Route that allows display of uploaded files when Debug=False in settings.py
    re_path(r'^media/(?P<path>.*)$',serve,{'document_root':settings.MEDIA_ROOT}),
    prefix_default_language=False # Hide default language code (en) on all urls

)

if include_docs_urls and get_schemajs_view:
    urlpatterns += i18n_patterns(
        path('api/docs/', include_docs_urls(title='iAHO-DCT',public=False)),
        path('api/schema/', get_schemajs_view(title='iAHO-DCT', public=False)),
        prefix_default_language=False
    )

# Routes for error handlers served by home view and templates/home/errors
handler404 = 'home.views.handler404'
handler500 = 'home.views.handler500'
