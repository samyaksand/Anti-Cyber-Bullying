from django.test import TestCase

from .models import ContactMessage


class ContactFormTests(TestCase):
    def test_valid_submission_is_persisted(self):
        response = self.client.post('/contact/', {
            'name': 'Jordan',
            'email': 'jordan@example.com',
            'message': 'I need help with a cyberbullying case.',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)
        saved = ContactMessage.objects.first()
        self.assertEqual(saved.name, 'Jordan')
        self.assertEqual(saved.message, 'I need help with a cyberbullying case.')

    def test_empty_message_is_not_persisted(self):
        response = self.client.post('/contact/', {'name': 'Jordan', 'email': 'jordan@example.com', 'message': ''})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 0)
