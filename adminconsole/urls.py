from django.urls import path

from . import views

urlpatterns = [
    path('admin-console/', views.admin_console_view, name='admin_console'),
    path('api/admin/stats/', views.AdminStatsView.as_view(), name='api_admin_stats'),
]
