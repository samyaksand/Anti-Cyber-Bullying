from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('admin-console', views.admin_console, name="admin_console"),
    path('complaint/<int:pk>/', views.complaint_detail, name='complaint_detail'),
]