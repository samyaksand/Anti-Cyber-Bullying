from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('adminconsole', views.admin_console, name="admin_console"),
    path('adminconsole/resolved', views.admin_console_resolved, name="admin_console_resolved"),
    path('adminconsole/unresolved', views.admin_console_unresolved, name="admin_console_unresolved"),
    path('complaint/<int:pk>/', views.complaint_detail, name='complaint_detail'),
    path('complaint/new', views.complaint_new, name="complaint_new"),
]