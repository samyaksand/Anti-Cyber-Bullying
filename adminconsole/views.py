from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from chatapp.models import Conversation
from complaints.models import Complaint, STATUS_RESOLVED, STATUS_CLOSED
from complaints.permissions import IsAdmin, user_is_admin
from django.contrib.auth.models import User


def _is_admin(user):
    return user_is_admin(user)


@login_required(login_url='/login/google-oauth2/')
def admin_console_view(request):
    if not _is_admin(request.user):
        messages.error(
            request,
            "This Google account does not have administrator access. You're signed in as a regular user.",
        )
        return redirect('dashboard')
    return render(request, 'adminconsole/dashboard.html')


class AdminStatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        total = Complaint.objects.count()
        resolved = Complaint.objects.filter(status__in=[STATUS_RESOLVED, STATUS_CLOSED]).count()
        pending = total - resolved
        critical = Complaint.objects.filter(
            category__in=['threats', 'blackmail', 'stalking']
        ).exclude(status__in=[STATUS_RESOLVED, STATUS_CLOSED]).count()
        registered_users = User.objects.count()
        unread_messages = sum(c.unread_count_for_admin for c in Conversation.objects.all())

        by_category = list(
            Complaint.objects.values('category').order_by('category').annotate(count=Count('id'))
        )

        return Response({
            'total_complaints': total,
            'pending_complaints': pending,
            'resolved_complaints': resolved,
            'critical_complaints': critical,
            'registered_users': registered_users,
            'unread_messages': unread_messages,
            'by_category': by_category,
            'generated_at': timezone.now().isoformat(),
        })
