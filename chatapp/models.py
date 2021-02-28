import os

from complaints.models import Complaint, validate_evidence_file
from django.conf import settings
from django.db import models

STATUS_OPEN = 'open'
STATUS_RESOLVED = 'resolved'

CONVERSATION_STATUS_CHOICES = [
    (STATUS_OPEN, 'Open'),
    (STATUS_RESOLVED, 'Resolved'),
]


class Conversation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversation')
    complaint = models.ForeignKey(Complaint, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    status = models.CharField(max_length=10, choices=CONVERSATION_STATUS_CHOICES, default=STATUS_OPEN)
    admin_internal_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation with {self.user.username}"

    @property
    def unread_count_for_admin(self):
        return self.messages.filter(is_from_admin=False, read_at__isnull=True).count()


def message_attachment_path(instance, filename):
    return os.path.join('chat_attachments', str(instance.conversation_id), filename)


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    is_from_admin = models.BooleanField(default=False)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    body = models.TextField(blank=True)
    attachment = models.FileField(upload_to=message_attachment_path, blank=True, null=True, validators=[validate_evidence_file])
    is_typing_event = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message in conversation {self.conversation_id}"
