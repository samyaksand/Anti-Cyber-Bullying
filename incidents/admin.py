from django.contrib import admin

from .models import IncidentAttachment, IncidentEntry


class IncidentAttachmentInline(admin.TabularInline):
    model = IncidentAttachment
    extra = 0


@admin.register(IncidentEntry)
class IncidentEntryAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'occurred_at', 'platform']
    inlines = [IncidentAttachmentInline]
