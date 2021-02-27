from django.db import models
from django.utils import timezone
from django.conf import settings

# Create your models here.

class Complaint(models.Model):
    name = models.CharField(max_length=200)
    issue_description = models.TextField()
    links = models.URLField(max_length=200, blank=True, null=True)
    resolution_status = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name