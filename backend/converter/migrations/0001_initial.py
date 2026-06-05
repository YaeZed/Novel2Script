import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ConversionTask",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("input_name", models.CharField(blank=True, max_length=255)),
                (
                    "source_format",
                    models.CharField(
                        choices=[("text", "Text"), ("epub", "EPUB")],
                        default="text",
                        max_length=16,
                    ),
                ),
                ("source_text", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("progress", models.PositiveSmallIntegerField(default=0)),
                ("chapters_done", models.PositiveIntegerField(default=0)),
                ("total_chapters", models.PositiveIntegerField(default=0)),
                ("characters", models.JSONField(blank=True, default=list)),
                ("chapters", models.JSONField(blank=True, default=list)),
                ("script_yaml", models.TextField(blank=True)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]

