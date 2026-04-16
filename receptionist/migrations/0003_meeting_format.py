from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('receptionist', '0002_appointmentrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='meeting_format',
            field=models.CharField(
                choices=[('in_person', 'In Person'), ('video', 'Video')],
                default='in_person',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='appointmentrequest',
            name='meeting_format',
            field=models.CharField(
                choices=[('in_person', 'In Person'), ('video', 'Video')],
                default='in_person',
                max_length=10,
            ),
        ),
    ]
