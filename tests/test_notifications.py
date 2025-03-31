from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Notification, Role

User = get_user_model()

class NotificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.role = Role.objects.create(name='User', role_type='U')
        self.user = User.objects.create_user(username='notifier', email='notify@example.com', password='notify123', role=self.role)
        self.client.login(username='notifier', password='notify123')
        Notification.objects.create(user=self.user, message='New message', notification_type='REPLY')

    def test_notification_appears_in_context(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('recent_notifications', response.context)
        self.assertGreaterEqual(len(response.context['recent_notifications']), 1)

    def test_mark_all_as_read(self):
        response = self.client.post(reverse('mark_all_notifications_read'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.filter(user=self.user, read=False).count(), 0)