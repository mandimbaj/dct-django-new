"""
Local development URL configuration — removes Swagger/DRF docs (incompatible with DRF 3.15+).
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import path, include, re_path
from home import admin_views, views
from django.conf.urls.i18n import i18n_patterns
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.authtoken.views import obtain_auth_token
from django.shortcuts import redirect as _redirect

admin.site.site_header = "DCT Admin"
admin.site.site_title = "DCT Admin"
admin.site.index_title = "DCT Admin"

api_patterns = [
    path('', include(('regions.urls', 'regions'), namespace='regions')),
    path('', include(('indicators.urls', 'indicators'), namespace='indicators')),
    path('', include(('publications.urls', 'publications'), namespace='publications')),
    path('', include(('elements.urls', 'elements'), namespace='elements')),
    path('', include(('home.urls', 'home'), namespace='home')),
    path('', include(('facilities.urls', 'facilities'), namespace='facilities')),
    path('', include(('health_workforce.urls', 'health_workforce'), namespace='health_workforce')),
    path('', include(('health_services.urls', 'health_services'), namespace='health_services')),
]

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('', views.login, name="login"),
    path('logout/', views.logout, name='logout'),
    path('admin/logout/', lambda request: redirect('/microsoft_authentication/logout', permanent=False)),
    path('admin/indicators/imports/', admin_views.indicator_imports, name='aho_indicator_imports'),
    path('admin/indicators/exports/', admin_views.indicator_exports, name='aho_indicator_exports'),
    path('admin/data-integration/connections/', admin_views.data_integration_connections, name='aho_data_integration_connections'),
    path('admin/data-integration/failed-rows/', admin_views.data_integration_failed_rows, name='aho_data_integration_failed_rows'),
    path('admin/data-quality/indicator-checks/', admin_views.data_quality_indicator_checks, name='aho_data_quality_indicator_checks'),
    path('admin/data-quality/facts-dataset/', admin_views.data_quality_facts_dataset, name='aho_data_quality_facts_dataset'),
    path('admin/api-tokens/token-status/', admin_views.api_token_status, name='aho_api_token_status'),
    path('admin/global-search/', admin_views.global_search, name='aho_global_search'),
    path('admin/row-action/', admin_views.row_action, name='aho_row_action'),
    path('admin/quality/', include('data_quality.urls', namespace='data_quality')),
    path('admin/', admin.site.urls, name='dashboard'),
    path('microsoft_authentication/login', lambda req: _redirect('/en/admin/login/?next=/en/admin/'), name='ms_login_local'),
    path('microsoft_authentication/', include('authentication.urls')),
    path('datawizard/', include('data_wizard.urls')),
    path('chaining/', include('smart_selects.urls')),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password-change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('api/', include((api_patterns, 'api'), namespace='api')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api-auth/', include('rest_framework.urls')),
    path('api/auth-token/', obtain_auth_token),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    prefix_default_language=False
)

handler404 = 'home.views.handler404'
handler500 = 'home.views.handler500'
