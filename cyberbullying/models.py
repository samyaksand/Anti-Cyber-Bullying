from django.db import models
from django.utils import timezone
from django.conf import settings

# Create your models here.

class Complaint(models.Model):
    name = models.CharField(max_length=200, blank=True)
    issue_date_time = models.DateTimeField(null=True, default=timezone.now)
    issue_location = models.CharField(max_length=200, null=True)
    issue_description = models.TextField(null=True)
    issue_reported = models.TextField(null=True)
    links = models.URLField(max_length=200, blank=True, null=True)
    resolution_status = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.issue_location