from django import forms
from django.utils.translation import gettext_lazy as _

from regions.models import StgLocation

from .models import DataIntegrationConnection


class DataIntegrationConnectionForm(forms.ModelForm):
    SECRET_FIELDS = ('password', 'api_token', 'api_key_value', 'client_secret')

    class Meta:
        model = DataIntegrationConnection
        fields = (
            'name',
            'location',
            'provider',
            'integration_method',
            'status',
            'sync_frequency',
            'server_name',
            'port',
            'database_driver',
            'database_name',
            'source_table',
            'connection_timeout',
            'ssl_mode',
            'ssl_ca_path',
            'ssl_certificate_path',
            'ssl_key_path',
            'ssl_cipher',
            'api_url',
            'auth_type',
            'api_token',
            'api_key_name',
            'api_key_value',
            'client_id',
            'client_secret',
            'username',
            'password',
            'notes',
        )
        widgets = {
            'password': forms.PasswordInput(render_value=False),
            'api_token': forms.PasswordInput(render_value=False),
            'api_key_value': forms.PasswordInput(render_value=False),
            'client_secret': forms.PasswordInput(render_value=False),
            'notes': forms.Textarea(attrs={'rows': 4}),
            'ssl_ca_path': forms.TextInput(),
            'ssl_certificate_path': forms.TextInput(),
            'ssl_key_path': forms.TextInput(),
        }

    field_groups = (
        {
            'title': _('Identity'),
            'fields': ('name', 'location', 'provider', 'integration_method', 'status', 'sync_frequency'),
            'section': 'identity',
        },
        {
            'title': _('Direct database'),
            'fields': ('server_name', 'port', 'database_driver', 'database_name', 'source_table', 'connection_timeout'),
            'section': 'direct',
        },
        {
            'title': _('SSL'),
            'fields': ('ssl_mode', 'ssl_ca_path', 'ssl_certificate_path', 'ssl_key_path', 'ssl_cipher'),
            'section': 'ssl',
        },
        {
            'title': _('API'),
            'fields': ('api_url', 'auth_type', 'api_token', 'api_key_name', 'api_key_value', 'client_id', 'client_secret'),
            'section': 'api',
        },
        {
            'title': _('Credentials'),
            'fields': ('username', 'password'),
            'section': 'credentials',
        },
        {
            'title': _('Mapping'),
            'fields': ('notes',),
            'section': 'mapping',
        },
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['location'].queryset = StgLocation.objects.filter(locationlevel_id=2)
        self.fields['location'].required = False

        if user is not None and not getattr(user, 'is_superuser', False):
            self.fields['location'].queryset = StgLocation.objects.filter(pk=getattr(user, 'location_id', None))
            self.fields['location'].disabled = True
            self.initial.setdefault('location', getattr(user, 'location_id', None))

        for field_name in self.SECRET_FIELDS:
            field = self.fields[field_name]
            field.required = False
            field.help_text = _('Leave blank to keep the existing value.') if self.instance.pk else ''

        self.fields['connection_timeout'].min_value = 1
        self.fields['connection_timeout'].max_value = 120

    def grouped_fields(self):
        for group in self.field_groups:
            yield {
                'title': group['title'],
                'section': group['section'],
                'fields': [self[field_name] for field_name in group['fields']],
            }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.pk and self.user is not None:
            instance.user = self.user
        if self.user is not None and not getattr(self.user, 'is_superuser', False):
            instance.location_id = getattr(self.user, 'location_id', None)

        if self.instance.pk:
            existing = DataIntegrationConnection.objects.get(pk=self.instance.pk)
            for field_name in self.SECRET_FIELDS:
                if not self.cleaned_data.get(field_name):
                    setattr(instance, field_name, getattr(existing, field_name))

        if commit:
            instance.save()
            self.save_m2m()
        return instance
