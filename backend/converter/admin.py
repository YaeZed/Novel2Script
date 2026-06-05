from django.contrib import admin

from .models import ConversionTask


@admin.register(ConversionTask)
class ConversionTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "input_name", "status", "progress", "created_at", "updated_at")
    list_filter = ("status", "source_format")
    search_fields = ("id", "input_name")
    readonly_fields = ("id", "created_at", "updated_at")

