from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('sources', '0002_source_user'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterModelTable(
                    name='filesource',
                    table=None,
                ),
                migrations.AlterModelTable(
                    name='urlsource',
                    table=None,
                ),
            ],
        ),
    ]
