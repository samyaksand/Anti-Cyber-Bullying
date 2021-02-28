from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from accounts.models import Profile
from .models import Conversation, Message


class ConversationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.alice = User.objects.create_user(username='alice', email='alice@example.com')
        self.admin = User.objects.create_user(username='admin', email='admin@example.com')
        Profile.objects.create(user=self.admin, role='admin')

    def test_user_conversation_is_created_on_first_access(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get('/api/chat/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Conversation.objects.filter(user=self.alice).count(), 1)

    def test_messages_persist_across_requests(self):
        conversation = Conversation.objects.create(user=self.alice)
        Message.objects.create(conversation=conversation, is_from_admin=False, sender=self.alice, body='hello')
        self.client.force_authenticate(user=self.alice)
        response = self.client.get('/api/chat/me/')
        self.assertEqual(len(response.data['messages']), 1)
        self.assertEqual(response.data['messages'][0]['body'], 'hello')

    def test_non_admin_cannot_access_inbox(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.get('/api/admin/chat/inbox/')
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_inbox_and_see_unread_count(self):
        conversation = Conversation.objects.create(user=self.alice)
        Message.objects.create(conversation=conversation, is_from_admin=False, sender=self.alice, body='help')
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/admin/chat/inbox/')
        self.assertEqual(response.status_code, 200)
        results = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(results[0]['unread_count'], 1)

    def test_admin_can_resolve_and_link_complaint(self):
        conversation = Conversation.objects.create(user=self.alice)
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f'/api/admin/chat/{conversation.id}/', {'status': 'resolved'})
        self.assertEqual(response.status_code, 200)
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, 'resolved')


class ChatWebsocketTests(TransactionTestCase):
    """Exercises the real Django Channels consumer with two separate
    authenticated connections."""

    def setUp(self):
        self.alice = User.objects.create_user(username='alice', email='alice@example.com', password='x')
        self.bob = User.objects.create_user(username='bob', email='bob@example.com', password='x')
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password='x')
        Profile.objects.create(user=self.admin, role='admin')

    def _communicator_for(self, user):
        from channels.testing import WebsocketCommunicator
        from website.asgi import application
        communicator = WebsocketCommunicator(application, '/ws/chat/')
        communicator.scope['user'] = user
        return communicator

    def test_user_message_reaches_admin_and_persists(self):
        import asyncio

        async def scenario():
            user_comm = self._communicator_for(self.alice)
            admin_comm = self._communicator_for(self.admin)

            connected, _ = await user_comm.connect()
            self.assertTrue(connected)
            connected, _ = await admin_comm.connect()
            self.assertTrue(connected)

            await user_comm.send_json_to({'type': 'message', 'body': 'I need help'})

            user_echo = await user_comm.receive_json_from(timeout=5)
            self.assertEqual(user_echo['type'], 'chat.message')
            self.assertEqual(user_echo['body'], 'I need help')
            self.assertFalse(user_echo['is_from_admin'])

            admin_echo = await admin_comm.receive_json_from(timeout=5)
            self.assertEqual(admin_echo['body'], 'I need help')
            conversation_id = admin_echo['conversation_id']

            await admin_comm.send_json_to({
                'type': 'message', 'body': 'How can I help?', 'conversation_id': conversation_id,
            })

            admin_reply_echo = await admin_comm.receive_json_from(timeout=5)
            self.assertEqual(admin_reply_echo['body'], 'How can I help?')

            user_reply_echo = await user_comm.receive_json_from(timeout=5)
            self.assertEqual(user_reply_echo['body'], 'How can I help?')
            self.assertTrue(user_reply_echo['is_from_admin'])

            await user_comm.disconnect()
            await admin_comm.disconnect()

        asyncio.run(scenario())

        conversation = Conversation.objects.get(user=self.alice)
        self.assertEqual(conversation.messages.count(), 2)
        self.assertEqual(conversation.messages.filter(is_from_admin=True).count(), 1)
        self.assertEqual(conversation.messages.filter(is_from_admin=False).count(), 1)

    def test_user_cannot_see_another_users_conversation_messages(self):
        import asyncio

        async def scenario():
            alice_comm = self._communicator_for(self.alice)
            bob_comm = self._communicator_for(self.bob)

            await alice_comm.connect()
            await bob_comm.connect()

            await alice_comm.send_json_to({'type': 'message', 'body': 'this is alice only'})
            await alice_comm.receive_json_from(timeout=5)

            received_by_bob = await bob_comm.receive_nothing(timeout=1)
            self.assertTrue(received_by_bob)

            await alice_comm.disconnect()
            await bob_comm.disconnect()

        asyncio.run(scenario())

        alice_conversation = Conversation.objects.get(user=self.alice)
        self.assertEqual(alice_conversation.messages.count(), 1)
        bob_conversation = Conversation.objects.get(user=self.bob)
        self.assertEqual(bob_conversation.messages.count(), 0)

    def test_read_receipt_only_updates_own_conversation_as_non_admin(self):
        import asyncio

        alice_conversation = Conversation.objects.create(user=self.alice)
        bob_conversation = Conversation.objects.create(user=self.bob)
        Message.objects.create(conversation=bob_conversation, is_from_admin=True, sender=self.admin, body='hi bob')

        async def scenario():
            alice_comm = self._communicator_for(self.alice)
            await alice_comm.connect()
            await alice_comm.send_json_to({'type': 'read', 'conversation_id': bob_conversation.id})
            echo = await alice_comm.receive_json_from(timeout=5)
            self.assertEqual(echo['conversation_id'], alice_conversation.id)
            await alice_comm.disconnect()

        asyncio.run(scenario())

        bob_conversation.refresh_from_db()
        unread = bob_conversation.messages.filter(is_from_admin=True, read_at__isnull=True).count()
        self.assertEqual(unread, 1)
