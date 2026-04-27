from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('receptionist', '0004_add_cancellation_reason'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
    ]
