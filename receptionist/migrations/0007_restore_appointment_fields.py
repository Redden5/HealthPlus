import uuid
from django.db import migrations, models


def populate_room_names(apps, schema_editor):
    # Use raw SQL to avoid ORM fetching columns that don't exist yet
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT id FROM receptionist_appointment WHERE room_name = ''")
        rows = cursor.fetchall()
        for (appt_id,) in rows:
            cursor.execute(
                "UPDATE receptionist_appointment SET room_name = %s WHERE id = %s",
                [str(uuid.uuid4()), appt_id],
            )


class Migration(migrations.Migration):

    dependencies = [
        ('receptionist', '0006_merge_20260427_1825'),
    ]

    operations = [
        # Add room_name without unique first
        migrations.AddField(
            model_name='appointment',
            name='room_name',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
        # Populate unique UUIDs for all existing rows via raw SQL
        migrations.RunPython(populate_room_names, migrations.RunPython.noop),
        # Now enforce uniqueness
        migrations.AlterField(
            model_name='appointment',
            name='room_name',
            field=models.CharField(default=uuid.uuid4, max_length=100, unique=True),
        ),
        migrations.AddField(
            model_name='appointment',
            name='cancellation_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='appointment',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
    ]
