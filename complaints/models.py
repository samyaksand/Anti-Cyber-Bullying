import hashlib
import os
import secrets
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.conf import settings as django_settings
from django.db import models

CATEGORY_HARASSMENT = 'harassment'
CATEGORY_CYBERBULLYING = 'cyberbullying'
CATEGORY_STALKING = 'stalking'
CATEGORY_THREATS = 'threats'
CATEGORY_IMPERSONATION = 'impersonation'
CATEGORY_DOXXING = 'doxxing'
CATEGORY_HATE_SPEECH = 'hate_speech'
CATEGORY_BLACKMAIL = 'blackmail'

CATEGORY_CHOICES = [
    (CATEGORY_HARASSMENT, 'Harassment'),
    (CATEGORY_CYBERBULLYING, 'Cyberbullying'),
    (CATEGORY_STALKING, 'Stalking'),
    (CATEGORY_THREATS, 'Threats'),
    (CATEGORY_IMPERSONATION, 'Impersonation'),
    (CATEGORY_DOXXING, 'Doxxing'),
    (CATEGORY_HATE_SPEECH, 'Hate speech'),
    (CATEGORY_BLACKMAIL, 'Blackmail'),
]

STATUS_SUBMITTED = 'submitted'
STATUS_UNDER_REVIEW = 'under_review'
STATUS_INFO_REQUIRED = 'info_required'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_RESOLVED = 'resolved'
STATUS_CLOSED = 'closed'

STATUS_CHOICES = [
    (STATUS_SUBMITTED, 'Submitted'),
    (STATUS_UNDER_REVIEW, 'Under Review'),
    (STATUS_INFO_REQUIRED, 'Additional Information Required'),
    (STATUS_IN_PROGRESS, 'Investigation in Progress'),
    (STATUS_RESOLVED, 'Resolved'),
    (STATUS_CLOSED, 'Closed'),
]


def generate_reference_id():
    while True:
        candidate = 'ACB-' + ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        if not Complaint.objects.filter(reference_id=candidate).exists():
            return candidate


def generate_tracking_code():
    while True:
        candidate = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        if not Complaint.objects.filter(tracking_code=candidate).exists():
            return candidate


class Complaint(models.Model):
    reference_id = models.CharField(max_length=20, unique=True, editable=False)
    tracking_code = models.CharField(max_length=20, unique=True, editable=False, db_index=True)

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints'
    )
    is_anonymous = models.BooleanField(default=False)
    contact_email = models.EmailField(blank=True)

    reporter_name = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    platform = models.CharField(max_length=100, blank=True)
    incident_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField()
    urls = models.TextField(blank=True, help_text='One URL per line')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    investigation_notes = models.TextField(blank=True)
    assigned_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference_id} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.reference_id:
            self.reference_id = generate_reference_id()
        if not self.tracking_code:
            self.tracking_code = generate_tracking_code()
        if self.status == STATUS_RESOLVED and not self.resolved_at:
            from django.utils import timezone
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def resolution_status(self):
        return self.status in (STATUS_RESOLVED, STATUS_CLOSED)


def evidence_upload_path(instance, filename):
    return os.path.join('evidence', str(instance.complaint.reference_id), filename)


def validate_evidence_file(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in django_settings.ALLOWED_EVIDENCE_EXTENSIONS:
        raise ValidationError(f"Unsupported file type: {ext}")
    if value.size > django_settings.MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError("File exceeds the maximum allowed size.")


class Evidence(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='evidence')
    file = models.FileField(upload_to=evidence_upload_path, validators=[validate_evidence_file])
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    sha256_hash = models.CharField(max_length=64, editable=False, blank=True)
    original_filename = models.CharField(max_length=255, editable=False, blank=True)
    content_type = models.CharField(max_length=100, editable=False, blank=True)
    file_size = models.PositiveBigIntegerField(editable=False, null=True)

    def __str__(self):
        return f"Evidence for {self.complaint.reference_id}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            original = Evidence.objects.filter(pk=self.pk).first()
            if original and original.file and original.file.name != self.file.name:
                raise ValidationError(
                    "Existing evidence is immutable. Upload a new Evidence record instead of replacing this file."
                )

        is_new = self.pk is None
        if is_new and self.file:
            self.original_filename = os.path.basename(self.file.name)
            self.content_type = getattr(self.file.file, 'content_type', '') or ''
            self.file_size = self.file.size
            hasher = hashlib.sha256()
            for chunk in self.file.chunks():
                hasher.update(chunk)
            self.sha256_hash = hasher.hexdigest()
            self.file.seek(0)

        super().save(*args, **kwargs)

    def recalculate_hash(self):
        """Reads the currently stored file from disk/storage and returns its
        SHA-256 hash, independent of whatever is recorded in sha256_hash."""
        hasher = hashlib.sha256()
        self.file.open('rb')
        try:
            for chunk in self.file.chunks():
                hasher.update(chunk)
        finally:
            self.file.close()
        return hasher.hexdigest()


VERIFICATION_RESULT_VERIFIED = 'verified'
VERIFICATION_RESULT_FAILED = 'failed'

VERIFICATION_RESULT_CHOICES = [
    (VERIFICATION_RESULT_VERIFIED, 'Verified'),
    (VERIFICATION_RESULT_FAILED, 'Integrity Check Failed'),
]


class EvidenceVerification(models.Model):
    """Append-only record of an admin recalculating and comparing an
    Evidence file's hash. Never edited or deleted after creation."""
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name='verifications')
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    computed_hash = models.CharField(max_length=64)
    result = models.CharField(max_length=10, choices=VERIFICATION_RESULT_CHOICES)
    verified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-verified_at']

    def __str__(self):
        return f"{self.get_result_display()} for evidence #{self.evidence_id}"


class CaseMessage(models.Model):
    """Follow-up messaging thread attached to a complaint, used for both
    the registered-user case inbox and anonymous follow-up messaging."""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='case_messages')
    author_is_admin = models.BooleanField(default=False)
    author_name = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    internal_note = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message on {self.complaint.reference_id}"
