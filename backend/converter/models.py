import uuid

from django.db import models


class ConversionTask(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    class SourceFormat(models.TextChoices):
        TEXT = "text", "Text"
        EPUB = "epub", "EPUB"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    input_name = models.CharField(max_length=255, blank=True)
    source_format = models.CharField(
        max_length=16,
        choices=SourceFormat.choices,
        default=SourceFormat.TEXT,
    )
    source_text = models.TextField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    progress = models.PositiveSmallIntegerField(default=0)
    chapters_done = models.PositiveIntegerField(default=0)
    total_chapters = models.PositiveIntegerField(default=0)
    characters = models.JSONField(default=list, blank=True)
    chapters = models.JSONField(default=list, blank=True)
    script_yaml = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        label = self.input_name or str(self.id)
        return f"{label} ({self.status})"

