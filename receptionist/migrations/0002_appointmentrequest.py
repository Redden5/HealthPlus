import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctor', '0002_teamscall'),
        ('patients', '0008_moodentry'),
        ('receptionist', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppointmentRequest',
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
                ('preferred_date', models.DateField(blank=True, null=True)),
                ('preferred_time', models.TimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('booked', 'Booked'),
                        ('declined', 'Declined'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('booked_appointment', models.OneToOneField(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='from_request',
                    to='receptionist.appointment',
                )),
                ('patient', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='appointment_requests',
                    to='patients.patientprofile',
                )),
                ('preferred_doctor', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='appointment_requests',
                    to='doctor.doctorprofile',
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
