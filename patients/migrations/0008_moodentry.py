import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("patients", "0007_conversation_message"),
    ]

    operations = [
        migrations.CreateModel(
            name="MoodEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score", models.PositiveSmallIntegerField()),
                ("note", models.TextField(blank=True)),
                ("logged_at", models.DateTimeField(auto_now_add=True)),
                ("date", models.DateField()),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mood_entries",
                        to="patients.patientprofile",
                    ),
                ),
            ],
            options={
                "ordering": ["date"],
                "unique_together": {("patient", "date")},
            },
        ),
    ]
