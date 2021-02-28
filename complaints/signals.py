from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Notification
from .models import Complaint


@receiver(post_save, sender=Complaint)
def notify_on_status_change(sender, instance, created, **kwargs):
    if created or not instance.reporter:
        return
    Notification.objects.create(
        user=instance.reporter,
        title=f"Complaint {instance.reference_id} updated",
        body=f"Status changed to {instance.get_status_display()}.",
        link=f"/track/{instance.reference_id}/",
    )
