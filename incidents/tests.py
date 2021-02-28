from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from complaints.models import Complaint
from .models import IncidentEntry


class IncidentTimelineTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.alice = User.objects.create_user(username='alice', email='alice@example.com')
        self.bob = User.objects.create_user(username='bob', email='bob@example.com')
        self.complaint = Complaint.objects.create(
            reporter=self.alice, category='harassment', description='test',
        )

    def test_owner_can_add_incident_entry(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(f'/api/complaints/{self.complaint.id}/incidents/', {
            'occurred_at': timezone.now().isoformat(),
            'platform': 'Instagram',
            'description': 'repeated abusive comments',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.complaint.incidents.count(), 1)

    def test_other_user_cannot_add_incident_entry(self):
        self.client.force_authenticate(user=self.bob)
        response = self.client.post(f'/api/complaints/{self.complaint.id}/incidents/', {
            'occurred_at': timezone.now().isoformat(),
            'platform': 'Instagram',
            'description': 'repeated abusive comments',
        })
        self.assertEqual(response.status_code, 403)

    def test_report_download_requires_access(self):
        IncidentEntry.objects.create(
            complaint=self.complaint, occurred_at=timezone.now(), description='test entry',
        )
        self.client.force_login(self.bob)
        response = self.client.get(f'/api/complaints/{self.complaint.id}/report/')
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.alice)
        response = self.client.get(f'/api/complaints/{self.complaint.id}/report/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test entry', response.content)

    def test_anonymous_reporter_can_add_incident_with_tracking_code(self):
        anon_complaint = Complaint.objects.create(
            category='stalking', description='anon case', is_anonymous=True,
            contact_email='victim@example.com',
        )
        response = self.client.post(
            f'/api/complaints/{anon_complaint.id}/incidents/?tracking_code={anon_complaint.tracking_code}', {
                'occurred_at': timezone.now().isoformat(),
                'platform': 'Twitter',
                'description': 'threatening message',
            })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(anon_complaint.incidents.count(), 1)

    def test_anonymous_without_tracking_code_cannot_add_incident(self):
        anon_complaint = Complaint.objects.create(
            category='stalking', description='anon case', is_anonymous=True,
            contact_email='victim@example.com',
        )
        response = self.client.post(f'/api/complaints/{anon_complaint.id}/incidents/', {
            'occurred_at': timezone.now().isoformat(),
            'platform': 'Twitter',
            'description': 'threatening message',
        })
        self.assertEqual(response.status_code, 403)

    def test_wrong_tracking_code_cannot_add_incident(self):
        anon_complaint = Complaint.objects.create(
            category='stalking', description='anon case', is_anonymous=True,
            contact_email='victim@example.com',
        )
        response = self.client.post(
            f'/api/complaints/{anon_complaint.id}/incidents/?tracking_code=WRONGCODE0000000', {
                'occurred_at': timezone.now().isoformat(),
                'platform': 'Twitter',
                'description': 'threatening message',
            })
        self.assertEqual(response.status_code, 403)

    def test_report_download_with_correct_tracking_code_succeeds(self):
        anon_complaint = Complaint.objects.create(
            category='stalking', description='anon case', is_anonymous=True,
            contact_email='victim@example.com',
        )
        IncidentEntry.objects.create(
            complaint=anon_complaint, occurred_at=timezone.now(), description='anon entry',
        )
        response = self.client.get(
            f'/api/complaints/{anon_complaint.id}/report/?tracking_code={anon_complaint.tracking_code}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'anon entry', response.content)
