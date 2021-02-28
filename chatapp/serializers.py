from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'is_from_admin', 'body', 'attachment', 'created_at', 'read_at']


class ConversationSerializer(serializers.ModelSerializer):
    user_display = serializers.SerializerMethodField()
    unread_count = serializers.IntegerField(source='unread_count_for_admin', read_only=True)

    def get_user_display(self, obj):
        full_name = obj.user.get_full_name()
        return full_name or obj.user.get_username()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'user', 'user_display', 'complaint', 'status',
            'admin_internal_notes', 'unread_count', 'last_message', 'updated_at',
        ]

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        return MessageSerializer(last).data if last else None
