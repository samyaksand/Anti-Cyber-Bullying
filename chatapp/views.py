from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from complaints.permissions import IsAdmin, user_is_admin
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


class MyConversationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversation, _ = Conversation.objects.get_or_create(user=request.user)
        messages = conversation.messages.all()
        return Response({
            'conversation': ConversationSerializer(conversation).data,
            'messages': MessageSerializer(messages, many=True).data,
        })


class MessageAttachmentUploadView(APIView):
    """Uploads a file attachment onto a chat message. Kept as a REST endpoint
    rather than part of the WebSocket protocol, since binary file upload over
    a JSON text WebSocket is impractical. The created Message is broadcast to
    the same conversation and admin-inbox groups the live chat consumer uses,
    so it appears in both sides' chat logs without a page reload."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file_obj = request.data.get('file')
        if not file_obj:
            return Response({'detail': 'A file is required.'}, status=status.HTTP_400_BAD_REQUEST)

        is_admin = user_is_admin(request.user)
        if is_admin:
            conversation_id = request.data.get('conversation_id')
            if not conversation_id:
                return Response({'detail': 'conversation_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
            conversation = get_object_or_404(Conversation, pk=conversation_id)
        else:
            conversation, _ = Conversation.objects.get_or_create(user=request.user)

        message = Message.objects.create(
            conversation=conversation,
            is_from_admin=is_admin,
            sender=request.user,
            attachment=file_obj,
        )

        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        payload = {
            'type': 'chat.message',
            'id': message.id,
            'conversation_id': conversation.id,
            'is_from_admin': is_admin,
            'body': message.body,
            'attachment': request.build_absolute_uri(message.attachment.url),
            'created_at': message.created_at.isoformat(),
        }
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(f'conversation_{conversation.id}', payload)
        async_to_sync(channel_layer.group_send)('chat_admin_inbox', payload)

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class AdminInboxView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = Conversation.objects.all()
        search = self.request.query_params.get('search')
        status_filter = self.request.query_params.get('status')
        if search:
            qs = qs.filter(user__username__icontains=search)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class AdminConversationMessagesView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        conversation = get_object_or_404(Conversation, pk=self.kwargs['pk'])
        return conversation.messages.all()


class AdminConversationUpdateView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        if 'status' in request.data:
            conversation.status = request.data['status']
        if 'complaint' in request.data:
            conversation.complaint_id = request.data['complaint']
        if 'admin_internal_notes' in request.data:
            conversation.admin_internal_notes = request.data['admin_internal_notes']
        conversation.save()
        return Response(ConversationSerializer(conversation).data)
