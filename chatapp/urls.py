from django.urls import path

from . import views

urlpatterns = [
    path('api/chat/me/', views.MyConversationView.as_view(), name='api_chat_me'),
    path('api/chat/attachments/', views.MessageAttachmentUploadView.as_view(), name='api_chat_attachment_upload'),
    path('api/admin/chat/inbox/', views.AdminInboxView.as_view(), name='api_admin_chat_inbox'),
    path('api/admin/chat/<int:pk>/messages/', views.AdminConversationMessagesView.as_view(), name='api_admin_chat_messages'),
    path('api/admin/chat/<int:pk>/', views.AdminConversationUpdateView.as_view(), name='api_admin_chat_update'),
]
