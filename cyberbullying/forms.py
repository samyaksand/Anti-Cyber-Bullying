from django import forms

from complaints.models import Complaint
from .models import ContactMessage


class ComplaintForm(forms.ModelForm):

    class Meta:
        model = Complaint
        fields = (
            'reporter_name', 'category', 'platform', 'incident_date',
            'description', 'urls', 'is_anonymous', 'contact_email',
        )
        widgets = {
            'incident_date': forms.DateTimeInput(attrs={'id': 'datepicker'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'urls': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'reporter_name': 'Your name (optional if reporting anonymously)',
            'category': 'What type of issue is this?',
            'platform': 'Where did this happen? (platform / app / website)',
            'incident_date': 'When did this occur?',
            'description': 'Describe the issue',
            'urls': 'Any links you would like to provide? (one per line)',
            'is_anonymous': 'Report anonymously',
            'contact_email': 'Contact email (required if reporting anonymously, used to track your case)',
        }


class ContactMessageForm(forms.ModelForm):

    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'message')
