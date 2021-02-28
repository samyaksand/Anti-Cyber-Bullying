import os

from complaints.models import Complaint, evidence_upload_path, validate_evidence_file
from django.db import models


def incident_attachment_path(instance, filename):
    return os.path.join('incidents', str(instance.complaint.reference_id), filename)


class IncidentEntry(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='incidents')
    occurred_at = models.DateTimeField()
    platform = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    url = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['occurred_at']

    def __str__(self):
        return f"Incident on {self.complaint.reference_id} at {self.occurred_at}"


class IncidentAttachment(models.Model):
    incident = models.ForeignKey(IncidentEntry, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=incident_attachment_path, validators=[validate_evidence_file])
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for incident {self.incident_id}"
