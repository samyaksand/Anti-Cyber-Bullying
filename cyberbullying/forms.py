from django import forms
from .models import Complaint

class ComplaintForm(forms.ModelForm):

    class Meta:
        model = Complaint
        fields = ('name', 'issue_date_time', 'issue_location', 'issue_description', 'issue_reported', 'links')
        widgets = {
            'issue_date_time': forms.DateTimeInput(attrs={'id': 'datepicker'}),
        }

        labels = {
            "issue_date_time": "When did this occur?",
            "issue_location": "Where did this occur?",
            "issue_description" : "Describe the issue",
            "issue_reported": "Have you reported this to any authority(eg. police)?",
            "links" : "Any links you would like to provide?"
        }