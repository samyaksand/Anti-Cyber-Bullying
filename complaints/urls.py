from django.urls import path

from . import views

urlpatterns = [
    path('complaint/<int:pk>/', views.complaint_detail_page, name='complaint_detail'),
    path('api/complaints/', views.ComplaintCreateView.as_view(), name='api_complaint_create'),
    path('api/complaints/mine/', views.MyComplaintListView.as_view(), name='api_my_complaints'),
    path('api/complaints/<int:pk>/', views.ComplaintDetailView.as_view(), name='api_complaint_detail'),
    path('api/complaints/<int:pk>/evidence/', views.EvidenceUploadView.as_view(), name='api_evidence_upload'),
    path('api/complaints/<int:pk>/messages/', views.CaseMessageListCreateView.as_view(), name='api_case_messages'),
    path('api/track/', views.TrackComplaintView.as_view(), name='api_track_complaint'),
    path('api/admin/complaints/', views.AdminComplaintListView.as_view(), name='api_admin_complaint_list'),
    path('api/admin/complaints/<int:pk>/', views.AdminComplaintUpdateView.as_view(), name='api_admin_complaint_update'),
    path('api/admin/evidence/<int:pk>/verify/', views.EvidenceVerifyView.as_view(), name='api_evidence_verify'),
    path(
        'api/admin/evidence/<int:pk>/verifications/',
        views.EvidenceVerificationHistoryView.as_view(),
        name='api_evidence_verification_history',
    ),
]
