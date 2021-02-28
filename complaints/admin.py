from django.contrib import admin

from .models import CaseMessage, Complaint, Evidence, EvidenceVerification


class EvidenceVerificationInline(admin.TabularInline):
    model = EvidenceVerification
    extra = 0
    readonly_fields = ['computed_hash', 'result', 'verified_by', 'verified_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class EvidenceInline(admin.TabularInline):
    model = Evidence
    extra = 0
    readonly_fields = ['sha256_hash', 'original_filename', 'content_type', 'file_size', 'uploaded_at']


class CaseMessageInline(admin.TabularInline):
    model = CaseMessage
    extra = 0


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['reference_id', 'category', 'status', 'is_anonymous', 'created_at']
    list_filter = ['category', 'status', 'is_anonymous']
    search_fields = ['reference_id', 'tracking_code', 'contact_email', 'reporter_name']
    inlines = [EvidenceInline, CaseMessageInline]


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ['id', 'complaint', 'original_filename', 'sha256_hash', 'uploaded_at']
    readonly_fields = ['sha256_hash', 'original_filename', 'content_type', 'file_size', 'uploaded_at']
    search_fields = ['sha256_hash', 'original_filename']
    inlines = [EvidenceVerificationInline]
