from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Profile
from .models import (
    Complaint, Evidence, EvidenceVerification, STATUS_SUBMITTED,
    VERIFICATION_RESULT_FAILED, VERIFICATION_RESULT_VERIFIED,
)


class ComplaintModelTests(TestCase):
    def test_reference_and_tracking_codes_are_generated(self):
        complaint = Complaint.objects.create(category='harassment', description='test')
        self.assertTrue(complaint.reference_id.startswith('ACB-'))
        self.assertEqual(len(complaint.tracking_code), 16)

    def test_resolution_status_alias(self):
        complaint = Complaint.objects.create(category='harassment', description='test')
        self.assertFalse(complaint.resolution_status)
        complaint.status = 'resolved'
        complaint.save()
        self.assertTrue(complaint.resolution_status)
        self.assertIsNotNone(complaint.resolved_at)


class ComplaintSubmissionAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_anonymous_submission_requires_email(self):
        response = self.client.post('/api/complaints/', {
            'category': 'stalking',
            'description': 'someone is following my posts',
            'is_anonymous': True,
        })
        self.assertEqual(response.status_code, 400)

    def test_anonymous_submission_with_email_succeeds(self):
        response = self.client.post('/api/complaints/', {
            'category': 'stalking',
            'description': 'someone is following my posts',
            'is_anonymous': True,
            'contact_email': 'reporter@example.com',
        })
        self.assertEqual(response.status_code, 201)
        complaint = Complaint.objects.get(reference_id=response.data['reference_id'])
        self.assertIsNone(complaint.reporter)
        self.assertTrue(complaint.is_anonymous)

    def test_registered_user_submission_links_reporter(self):
        user = User.objects.create_user(username='alice', email='alice@example.com')
        self.client.force_authenticate(user=user)
        response = self.client.post('/api/complaints/', {
            'category': 'doxxing',
            'description': 'my address was posted online',
        })
        self.assertEqual(response.status_code, 201)
        complaint = Complaint.objects.get(reference_id=response.data['reference_id'])
        self.assertEqual(complaint.reporter, user)
        self.assertFalse(complaint.is_anonymous)


class ComplaintAccessControlTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.alice = User.objects.create_user(username='alice', email='alice@example.com')
        self.bob = User.objects.create_user(username='bob', email='bob@example.com')
        self.complaint = Complaint.objects.create(
            reporter=self.alice, category='harassment', description='test', status=STATUS_SUBMITTED
        )

    def test_owner_can_view_own_complaint(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get(f'/api/complaints/{self.complaint.id}/')
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_view_complaint(self):
        self.client.force_authenticate(user=self.bob)
        response = self.client.get(f'/api/complaints/{self.complaint.id}/')
        self.assertEqual(response.status_code, 403)

    def test_non_admin_cannot_access_admin_list(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get('/api/admin/complaints/')
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_admin_list(self):
        Profile.objects.create(user=self.bob, role='admin')
        self.client.force_authenticate(user=self.bob)
        response = self.client.get('/api/admin/complaints/')
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_upload_evidence_to_someone_elses_complaint(self):
        self.client.force_authenticate(user=self.bob)
        upload = SimpleUploadedFile('proof.txt', b'bobs attempt', content_type='text/plain')
        response = self.client.post(f'/api/complaints/{self.complaint.id}/evidence/', {'file': upload})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.complaint.evidence.count(), 0)

    def test_anonymous_cannot_upload_evidence_without_tracking_code(self):
        upload = SimpleUploadedFile('proof.txt', b'anon attempt', content_type='text/plain')
        response = self.client.post(f'/api/complaints/{self.complaint.id}/evidence/', {'file': upload})
        self.assertEqual(response.status_code, 403)

    def test_owner_can_upload_evidence_to_own_complaint(self):
        self.client.force_authenticate(user=self.alice)
        upload = SimpleUploadedFile('proof.txt', b'alices evidence', content_type='text/plain')
        response = self.client.post(f'/api/complaints/{self.complaint.id}/evidence/', {'file': upload})
        self.assertEqual(response.status_code, 201)

    def test_anonymous_with_correct_tracking_code_can_upload_evidence(self):
        anon_complaint = Complaint.objects.create(
            category='stalking', description='anon case', is_anonymous=True,
            contact_email='victim@example.com',
        )
        upload = SimpleUploadedFile('proof.txt', b'anon evidence', content_type='text/plain')
        response = self.client.post(
            f'/api/complaints/{anon_complaint.id}/evidence/?tracking_code={anon_complaint.tracking_code}',
            {'file': upload},
        )
        self.assertEqual(response.status_code, 201)

    def test_other_user_cannot_read_or_post_case_messages_on_someone_elses_complaint(self):
        self.client.force_authenticate(user=self.bob)
        response = self.client.get(f'/api/complaints/{self.complaint.id}/messages/')
        self.assertEqual(response.status_code, 403)
        response = self.client.post(f'/api/complaints/{self.complaint.id}/messages/', {'body': 'snooping'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.complaint.case_messages.count(), 0)

    def test_anonymous_cannot_read_or_post_case_messages_without_tracking_code(self):
        response = self.client.get(f'/api/complaints/{self.complaint.id}/messages/')
        self.assertEqual(response.status_code, 403)
        response = self.client.post(f'/api/complaints/{self.complaint.id}/messages/', {'body': 'snooping'})
        self.assertEqual(response.status_code, 403)

    def test_owner_can_post_case_message_on_own_complaint(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(f'/api/complaints/{self.complaint.id}/messages/', {'body': 'hello admin'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.complaint.case_messages.count(), 1)

    def test_anonymous_with_correct_tracking_code_can_post_case_message(self):
        anon_complaint = Complaint.objects.create(
            category='stalking', description='anon case', is_anonymous=True,
            contact_email='victim@example.com',
        )
        response = self.client.post(
            f'/api/complaints/{anon_complaint.id}/messages/?tracking_code={anon_complaint.tracking_code}',
            {'body': 'follow-up from anon reporter'},
        )
        self.assertEqual(response.status_code, 201)

    def test_complaint_detail_page_rejects_non_owner(self):
        self.client.force_login(self.bob)
        response = self.client.get(f'/complaint/{self.complaint.id}/')
        self.assertEqual(response.status_code, 403)

    def test_complaint_detail_page_allows_owner(self):
        self.client.force_login(self.alice)
        response = self.client.get(f'/complaint/{self.complaint.id}/')
        self.assertEqual(response.status_code, 200)

    def test_complaint_detail_page_allows_correct_tracking_code(self):
        anon_complaint = Complaint.objects.create(
            category='stalking', description='anon case', is_anonymous=True,
            contact_email='victim@example.com',
        )
        response = self.client.get(f'/complaint/{anon_complaint.id}/?tracking_code={anon_complaint.tracking_code}')
        self.assertEqual(response.status_code, 200)

    def test_complaint_detail_page_rejects_wrong_tracking_code(self):
        anon_complaint = Complaint.objects.create(
            category='stalking', description='anon case', is_anonymous=True,
            contact_email='victim@example.com',
        )
        response = self.client.get(f'/complaint/{anon_complaint.id}/?tracking_code=WRONGCODE0000000')
        self.assertEqual(response.status_code, 403)


class TrackComplaintTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.complaint = Complaint.objects.create(
            category='threats', description='test', is_anonymous=True, contact_email='victim@example.com',
        )

    def test_track_with_correct_email_succeeds(self):
        response = self.client.post('/api/track/', {
            'reference_id': self.complaint.reference_id,
            'email': 'victim@example.com',
        })
        self.assertEqual(response.status_code, 200)

    def test_track_with_wrong_email_fails(self):
        response = self.client.post('/api/track/', {
            'reference_id': self.complaint.reference_id,
            'email': 'someoneelse@example.com',
        })
        self.assertEqual(response.status_code, 404)


class EvidenceIntegrityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.complaint = Complaint.objects.create(category='harassment', description='test')
        self.admin_user = User.objects.create_user(username='admin', email='admin@example.com')
        Profile.objects.create(user=self.admin_user, role='admin')
        self.other_user = User.objects.create_user(username='reporter', email='reporter@example.com')

    def _upload(self, content=b'original evidence bytes'):
        upload = SimpleUploadedFile('proof.txt', content, content_type='text/plain')
        return Evidence.objects.create(complaint=self.complaint, file=upload)

    def test_hash_is_computed_on_upload(self):
        import hashlib
        content = b'original evidence bytes'
        evidence = self._upload(content)
        self.assertEqual(evidence.sha256_hash, hashlib.sha256(content).hexdigest())
        self.assertEqual(evidence.original_filename, 'proof.txt')
        self.assertEqual(evidence.file_size, len(content))

    def test_verify_unmodified_file_is_verified(self):
        evidence = self._upload()
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/admin/evidence/{evidence.id}/verify/')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['result'], VERIFICATION_RESULT_VERIFIED)

    def test_verify_tampered_file_fails_integrity_check(self):
        evidence = self._upload()
        evidence.file.open('wb')
        evidence.file.write(b'tampered bytes, different content entirely')
        evidence.file.close()

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/admin/evidence/{evidence.id}/verify/')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['result'], VERIFICATION_RESULT_FAILED)

    def test_verification_history_accumulates(self):
        evidence = self._upload()
        self.client.force_authenticate(user=self.admin_user)
        self.client.post(f'/api/admin/evidence/{evidence.id}/verify/')
        self.client.post(f'/api/admin/evidence/{evidence.id}/verify/')
        self.assertEqual(EvidenceVerification.objects.filter(evidence=evidence).count(), 2)

        history = self.client.get(f'/api/admin/evidence/{evidence.id}/verifications/')
        self.assertEqual(history.status_code, 200)
        results = history.data['results'] if isinstance(history.data, dict) else history.data
        self.assertEqual(len(results), 2)

    def test_non_admin_cannot_trigger_verification(self):
        evidence = self._upload()
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(f'/api/admin/evidence/{evidence.id}/verify/')
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_trigger_verification(self):
        evidence = self._upload()
        response = self.client.post(f'/api/admin/evidence/{evidence.id}/verify/')
        self.assertEqual(response.status_code, 403)

    def test_original_evidence_file_cannot_be_replaced_in_place(self):
        evidence = self._upload()
        replacement = SimpleUploadedFile('other.txt', b'a completely different file', content_type='text/plain')
        evidence.file = replacement
        with self.assertRaises(ValidationError):
            evidence.save()

    def test_replacement_evidence_is_a_new_separate_record(self):
        first = self._upload(b'first version of the evidence')
        second = self._upload(b'second, corrected version of the evidence')
        self.assertNotEqual(first.id, second.id)
        self.assertEqual(Evidence.objects.filter(complaint=self.complaint).count(), 2)
        self.assertNotEqual(first.sha256_hash, second.sha256_hash)
