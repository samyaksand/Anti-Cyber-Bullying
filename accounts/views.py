from django.contrib.auth import logout as django_logout
from django.shortcuts import render, redirect
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from complaints.models import Complaint, STATUS_RESOLVED, STATUS_CLOSED
from .models import Notification, Profile
from .serializers import NotificationSerializer, ProfileSerializer, UserSerializer


def logout_view(request):
    django_logout(request)
    return redirect('/')


def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('/login/google-oauth2/')
    complaints = Complaint.objects.filter(reporter=request.user).order_by('-created_at')
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:10]
    resolved_count = complaints.filter(status__in=[STATUS_RESOLVED, STATUS_CLOSED]).count()
    return render(request, 'accounts/dashboard.html', {
        'complaints': complaints,
        'notifications': notifications,
        'total_count': complaints.count(),
        'resolved_count': resolved_count,
        'open_count': complaints.count() - resolved_count,
    })


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ProfileSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        notification.is_read = True
        notification.save()
        return Response(NotificationSerializer(notification).data)
