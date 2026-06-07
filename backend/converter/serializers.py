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
    chapters = serializers.SerializerMethodField()
    can_view_result = serializers.SerializerMethodField()

    class Meta:
        model = ConversionTask
        fields = [
            "id",
            "input_name",
            "source_format",
            "status",
            "progress",
            "chapters_done",
            "total_chapters",
            "chapters",
            "can_view_result",
            "error_message",
            "llm_provider",
        ]

    def get_llm_provider(self, obj):  # noqa: ARG002
        try:
            return resolve_llm_provider()
        except ValueError:
            return "misconfigured"

    def get_chapters(self, obj):
        return [
            {
                "index": chapter.get("index"),
                "title": chapter.get("title", ""),
                "excerpt": chapter.get("excerpt", ""),
            }
            for chapter in obj.chapters
        ]

    def get_can_view_result(self, obj):
        return bool(obj.script_yaml.strip())


class ConversionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversionTask
        fields = ["id", "script_yaml", "characters", "chapters", "status", "error_message"]
