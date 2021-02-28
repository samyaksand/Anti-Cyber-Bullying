from rest_framework import serializers

from .models import IncidentAttachment, IncidentEntry


class IncidentAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentAttachment
        fields = ['id', 'file', 'uploaded_at']


class IncidentEntrySerializer(serializers.ModelSerializer):
    attachments = IncidentAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = IncidentEntry
        fields = ['id', 'complaint', 'occurred_at', 'platform', 'description', 'url', 'created_at', 'attachments']
        read_only_fields = ['created_at', 'complaint']
