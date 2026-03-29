import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("doctor", "0001_initial"),
        ("patients", "0008_moodentry"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeamsCall",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("scheduled_at", models.DateTimeField()),
                ("join_url", models.URLField(blank=True)),
                ("teams_meeting_id", models.CharField(blank=True, max_length=300)),
                ("status", models.CharField(
                    choices=[
                        ("scheduled", "Scheduled"),
                        ("active", "Active"),
                        ("ended", "Ended"),
                        ("cancelled", "Cancelled"),
                    ],
                    default="scheduled",
                    max_length=20,
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "doctor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="calls",
                        to="doctor.doctorprofile",
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="calls",
                        to="patients.patientprofile",
                    ),
                ),
            ],
            options={"ordering": ["scheduled_at"]},
        ),
    ]
