from django.urls import path

from . import views

urlpatterns = [
    path('api/complaints/<int:complaint_id>/incidents/', views.IncidentListCreateView.as_view(), name='api_incidents'),
    path('api/complaints/<int:complaint_id>/report/', views.incident_report_download, name='incident_report_download'),
]
