from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Notification, Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['role', 'profile_pic_url', 'phone', 'notify_on_message', 'notify_on_status_change']
        read_only_fields = ['role']


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'profile']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'body', 'link', 'is_read', 'created_at']
