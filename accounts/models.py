from django.conf import settings
from django.db import models

USER_IMG_DEFAULT = "https://image.shutterstock.com/image-vector/default-avatar-profile-icon-vector-260nw-1745180411.jpg"

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_CHOICES = [
    (ROLE_USER, 'User'),
    (ROLE_ADMIN, 'Administrator'),
]


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_USER)
    profile_pic_url = models.URLField(max_length=400, blank=True, default=USER_IMG_DEFAULT)
    phone = models.CharField(max_length=20, blank=True)
    notify_on_message = models.BooleanField(default=True)
    notify_on_status_change = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == ROLE_ADMIN


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    body = models.CharField(max_length=500, blank=True)
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    path = models.CharField(max_length=300)
    method = models.CharField(max_length=10)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.method} {self.path} ({self.status_code})"
