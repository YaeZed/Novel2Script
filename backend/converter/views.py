from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ConversionTask
from .serializers import (
    ConversionCreateSerializer,
    ConversionResultSerializer,
    ConversionStatusSerializer,
)
from .services.epub_parser import extract_epub_text
from .services.task_runner import start_conversion_task


class ConvertView(APIView):
    def post(self, request):
        serializer = ConversionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data.get("file")
        source_format = serializer.validated_data.get("source_format") or ConversionTask.SourceFormat.TEXT
        input_name = ""

        if uploaded_file:
            input_name = uploaded_file.name
            if uploaded_file.name.lower().endswith(".epub"):
                source_format = ConversionTask.SourceFormat.EPUB
                source_text = extract_epub_text(uploaded_file.read())
            else:
                source_text = uploaded_file.read().decode("utf-8", errors="ignore")
        else:
            source_text = serializer.validated_data["text"]
            input_name = "pasted-text.txt"

        task = ConversionTask.objects.create(
            input_name=input_name,
            source_format=source_format,
            source_text=source_text,
            status=ConversionTask.Status.PENDING,
        )

        start_conversion_task(task)

        return Response({"task_id": task.id}, status=status.HTTP_201_CREATED)


class ConversionStatusView(APIView):
    def get(self, request, task_id):
        task = get_object_or_404(ConversionTask, id=task_id)
        serializer = ConversionStatusSerializer(task)
        return Response(serializer.data)


class ConversionResultView(APIView):
    def get(self, request, task_id):
        task = get_object_or_404(ConversionTask, id=task_id)
        serializer = ConversionResultSerializer(task)
        return Response(serializer.data)
