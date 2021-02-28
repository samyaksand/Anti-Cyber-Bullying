from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('api/me/', views.MeView.as_view(), name='api_me'),
    path('api/me/settings/', views.ProfileSettingsView.as_view(), name='api_profile_settings'),
    path('api/notifications/', views.NotificationListView.as_view(), name='api_notifications'),
    path('api/notifications/<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='api_notification_read'),
]
