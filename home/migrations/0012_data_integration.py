# Generated manually to mirror the Laravel Data integration schema.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('regions', '0002_auto_20210916_1203'),
        ('home', '0011_auto_20230124_1036'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataIntegrationConnection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('provider', models.CharField(choices=[('dhis2', 'DHIS2'), ('databank', 'DataBank'), ('who_datahub', 'WHO DataHub'), ('aho_warehouse', 'AHO Warehouse'), ('custom', 'Custom')], default='dhis2', max_length=50, verbose_name='Provider')),
                ('integration_method', models.CharField(choices=[('direct', 'Direct database'), ('api', 'API')], default='api', max_length=50, verbose_name='Integration method')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('active', 'Active'), ('paused', 'Paused'), ('error', 'Error')], default='draft', max_length=50, verbose_name='Status')),
                ('sync_frequency', models.CharField(choices=[('manual', 'Manual'), ('hourly', 'Hourly'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default='manual', max_length=50, verbose_name='Sync frequency')),
                ('server_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Server name')),
                ('port', models.PositiveIntegerField(blank=True, null=True, verbose_name='Port')),
                ('database_driver', models.CharField(blank=True, choices=[('mysql', 'MySQL / MariaDB'), ('pgsql', 'PostgreSQL'), ('sqlsrv', 'SQL Server'), ('oracle', 'Oracle'), ('sqlite', 'SQLite'), ('odbc', 'ODBC'), ('other', 'Other')], max_length=50, null=True, verbose_name='Database driver')),
                ('database_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Database name')),
                ('source_table', models.CharField(blank=True, max_length=255, null=True, verbose_name='Source table')),
                ('username', models.CharField(blank=True, max_length=255, null=True, verbose_name='Username')),
                ('password', models.TextField(blank=True, null=True, verbose_name='Password')),
                ('api_url', models.URLField(blank=True, max_length=255, null=True, verbose_name='API URL')),
                ('auth_type', models.CharField(choices=[('none', 'None'), ('bearer', 'Bearer token'), ('api_key', 'API key'), ('basic', 'Basic authentication'), ('oauth2', 'OAuth2')], default='none', max_length=50, verbose_name='Authentication type')),
                ('api_token', models.TextField(blank=True, null=True, verbose_name='API token')),
                ('api_key_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='API key name')),
                ('api_key_value', models.TextField(blank=True, null=True, verbose_name='API key value')),
                ('client_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='Client ID')),
                ('client_secret', models.TextField(blank=True, null=True, verbose_name='Client secret')),
                ('data_scope', models.JSONField(blank=True, null=True, verbose_name='Data scope')),
                ('field_mapping', models.JSONField(blank=True, null=True, verbose_name='Field mapping')),
                ('ssl_mode', models.CharField(choices=[('disabled', 'Disabled'), ('required', 'Required'), ('verify_identity', 'Verify identity')], default='disabled', max_length=50, verbose_name='SSL mode')),
                ('ssl_ca_path', models.TextField(blank=True, null=True, verbose_name='SSL CA path')),
                ('ssl_certificate_path', models.TextField(blank=True, null=True, verbose_name='SSL certificate path')),
                ('ssl_key_path', models.TextField(blank=True, null=True, verbose_name='SSL key path')),
                ('ssl_cipher', models.CharField(blank=True, max_length=255, null=True, verbose_name='SSL cipher')),
                ('connection_timeout', models.PositiveSmallIntegerField(default=15, verbose_name='Connection timeout')),
                ('last_synced_at', models.DateTimeField(blank=True, null=True, verbose_name='Last synced at')),
                ('last_tested_at', models.DateTimeField(blank=True, null=True, verbose_name='Last tested at')),
                ('last_test_status', models.CharField(blank=True, max_length=50, null=True, verbose_name='Last test status')),
                ('last_test_message', models.TextField(blank=True, null=True, verbose_name='Last test message')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notes')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date Modified')),
                ('location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='regions.stglocation')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Data integration connection',
                'verbose_name_plural': 'Data integration connections',
                'db_table': 'data_integration_connections',
                'ordering': ('-updated_at', '-created_at'),
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='DataIntegrationFieldMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('local_field', models.CharField(choices=[('location_id', 'Location'), ('indicator_id', 'Indicator'), ('start_period', 'Start period'), ('end_period', 'End period'), ('period', 'Period'), ('categoryoption_id', 'Category option'), ('datasource_id', 'Data source'), ('measuremethod_id', 'Measure method'), ('value_received', 'Value received'), ('numerator_value', 'Numerator'), ('denominator_value', 'Denominator'), ('min_value', 'Min'), ('max_value', 'Max'), ('target_value', 'Target'), ('string_value', 'Text value'), ('comment', 'Approval status'), ('priority', 'Priority')], max_length=255, verbose_name='Local field')),
                ('external_field', models.CharField(max_length=255, verbose_name='External field')),
                ('field_type', models.CharField(choices=[('direct', 'Direct'), ('lookup', 'Lookup'), ('computed', 'Computed'), ('conditional', 'Conditional'), ('skip', 'Skip')], default='direct', max_length=50, verbose_name='Field type')),
                ('transformation_config', models.JSONField(blank=True, null=True, verbose_name='Transformation config')),
                ('is_required', models.BooleanField(default=False, verbose_name='Required')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notes')),
                ('sort_order', models.IntegerField(default=0, verbose_name='Sort order')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date Modified')),
                ('connection', models.ForeignKey(db_column='data_integration_connection_id', on_delete=django.db.models.deletion.CASCADE, related_name='field_mappings', to='home.dataintegrationconnection')),
            ],
            options={
                'verbose_name': 'Data integration field mapping',
                'verbose_name_plural': 'Data integration field mappings',
                'db_table': 'data_integration_field_mappings',
                'ordering': ('sort_order', 'id'),
                'managed': True,
            },
        ),
        migrations.AddIndex(
            model_name='dataintegrationconnection',
            index=models.Index(fields=['provider', 'integration_method'], name='dic_provider_method_idx'),
        ),
        migrations.AddIndex(
            model_name='dataintegrationconnection',
            index=models.Index(fields=['status', 'sync_frequency'], name='dic_status_sync_idx'),
        ),
        migrations.AddConstraint(
            model_name='dataintegrationfieldmapping',
            constraint=models.UniqueConstraint(fields=('connection', 'local_field'), name='difm_connection_local_unique'),
        ),
        migrations.AddIndex(
            model_name='dataintegrationfieldmapping',
            index=models.Index(fields=['connection', 'field_type'], name='difm_connection_type_idx'),
        ),
    ]
