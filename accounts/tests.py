from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Notification, Profile


class AuthAndProfileTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.alice = User.objects.create_user(username='alice', email='alice@example.com')

    def test_unauthenticated_me_is_rejected(self):
        response = self.client.get('/api/me/')
        self.assertEqual(response.status_code, 403)

    def test_authenticated_me_returns_profile(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get('/api/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'alice')

    def test_dashboard_redirects_anonymous_user(self):
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)

    def test_dashboard_loads_for_authenticated_user(self):
        self.client.force_login(self.alice)
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)


class NotificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.alice = User.objects.create_user(username='alice', email='alice@example.com')
        self.bob = User.objects.create_user(username='bob', email='bob@example.com')

    def test_user_only_sees_own_notifications(self):
        Notification.objects.create(user=self.alice, title='for alice')
        Notification.objects.create(user=self.bob, title='for bob')
        self.client.force_authenticate(user=self.alice)
        response = self.client.get('/api/notifications/')
        results = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'for alice')

    def test_cannot_mark_other_users_notification_read(self):
        notification = Notification.objects.create(user=self.bob, title='for bob')
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(f'/api/notifications/{notification.id}/read/')
        self.assertEqual(response.status_code, 404)
