from django.http import HttpResponse
from rest_framework import generics, permissions

from complaints.models import Complaint
from complaints.permissions import user_is_admin
from complaints.views import get_complaint_with_access_check
from .models import IncidentEntry
from .serializers import IncidentEntrySerializer


class IncidentListCreateView(generics.ListCreateAPIView):
    """Access follows the same rule as complaint evidence/messages: the
    registered owner, an admin, or anyone presenting the complaint's
    tracking_code, so anonymous reporters can add incidents too."""
    serializer_class = IncidentEntrySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        complaint = self._get_complaint()
        return complaint.incidents.all()

    def perform_create(self, serializer):
        complaint = self._get_complaint()
        serializer.save(complaint=complaint)

    def _get_complaint(self):
        return get_complaint_with_access_check(self.request, self.kwargs['complaint_id'])


def incident_report_download(request, complaint_id):
    complaint = Complaint.objects.filter(pk=complaint_id).first()
    if complaint is None:
        return HttpResponse('Not found', status=404)

    tracking_code = request.GET.get('tracking_code', '')
    is_owner = request.user.is_authenticated and complaint.reporter_id == request.user.id
    has_tracking_code = bool(tracking_code) and complaint.tracking_code == tracking_code
    if not (user_is_admin(request.user) or is_owner or has_tracking_code):
        return HttpResponse('Forbidden', status=403)

    lines = [
        f"Incident Report for Complaint {complaint.reference_id}",
        f"Category: {complaint.get_category_display()}",
        f"Status: {complaint.get_status_display()}",
        f"Submitted: {complaint.created_at}",
        "",
        "Description:",
        complaint.description,
        "",
        "Timeline:",
    ]
    for incident in complaint.incidents.all():
        lines.append(f"- {incident.occurred_at} [{incident.platform}] {incident.description}")
        if incident.url:
            lines.append(f"  URL: {incident.url}")

    content = "\n".join(lines)
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{complaint.reference_id}_report.txt"'
    return response
