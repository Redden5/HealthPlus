import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('doctor', '0002_teamscall'),
        ('patients', '0008_moodentry'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReceptionistProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointment_type', models.CharField(
                    choices=[
                        ('therapy', 'Therapy Session'),
                        ('medication', 'Medication Check-in'),
                        ('consultation', 'General Consultation'),
                        ('followup', 'Follow-up'),
                        ('assessment', 'Assessment'),
                    ],
                    default='consultation',
                    max_length=20,
                )),
                ('title', models.CharField(max_length=200)),
                ('scheduled_at', models.DateTimeField()),
                ('duration_minutes', models.PositiveSmallIntegerField(default=60)),
                ('location', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('status', models.CharField(
                    choices=[
                        ('scheduled', 'Scheduled'),
                        ('confirmed', 'Confirmed'),
                        ('completed', 'Completed'),
                        ('cancelled', 'Cancelled'),
                        ('no_show', 'No Show'),
                    ],
                    default='scheduled',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='doctor.doctorprofile')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='patients.patientprofile')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_appointments', to='receptionist.receptionistprofile')),
            ],
            options={'ordering': ['scheduled_at']},
        ),
    ]
