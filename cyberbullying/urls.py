from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('complaint/new', views.complaint_new, name='complaint_new'),
    path('track/', views.track_complaint, name='track_complaint'),
    path('live-support/', views.live_support, name='live_support'),
    path('cyber-safety/', views.cyber_safety, name='cyber_safety'),
    path('emergency/', views.emergency, name='emergency'),
    path('contact/', views.contact, name='contact'),
]
