from rest_framework import serializers

from .models import ConversionTask
from .services.pipeline import resolve_llm_provider


class ConversionCreateSerializer(serializers.Serializer):
    text = serializers.CharField(required=False, allow_blank=True)
    file = serializers.FileField(required=False)
    source_format = serializers.ChoiceField(
        choices=ConversionTask.SourceFormat.choices,
        required=False,
    )

    def validate(self, attrs):
        if not attrs.get("text") and not attrs.get("file"):
            raise serializers.ValidationError("text or file is required")
        return attrs


class ConversionCreatedSerializer(serializers.Serializer):
    task_id = serializers.UUIDField()


class ConversionStatusSerializer(serializers.ModelSerializer):
    llm_provider = serializers.SerializerMethodField()

    class Meta:
        model = ConversionTask
        fields = [
            "id",
            "status",
            "progress",
            "chapters_done",
            "total_chapters",
            "error_message",
            "llm_provider",
        ]

    def get_llm_provider(self, obj):  # noqa: ARG002
        try:
            return resolve_llm_provider()
        except ValueError:
            return "misconfigured"


class ConversionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversionTask
        fields = ["id", "script_yaml", "characters", "chapters", "status", "error_message"]
