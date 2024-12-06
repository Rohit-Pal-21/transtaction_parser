from django.urls import path
from .views import XMLToExcelAPIView

urlpatterns = [
    path('convert/', XMLToExcelAPIView.as_view(), name='xml-to-excel'),
]
