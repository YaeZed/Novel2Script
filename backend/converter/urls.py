from django.urls import path

from .views import ConversionResultView, ConversionStatusView, ConvertView


urlpatterns = [
    path("convert", ConvertView.as_view(), name="convert"),
    path("status/<uuid:task_id>", ConversionStatusView.as_view(), name="conversion-status"),
    path("result/<uuid:task_id>", ConversionResultView.as_view(), name="conversion-result"),
]

