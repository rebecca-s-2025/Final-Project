from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import DropLocation, TextbookRequest, Textbook, Role

User = get_user_model()

class TextbookTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='User', role_type='U')
        self.user = User.objects.create_user(username='testuserbook', email='testuserbook@example.com', password='pass', role=self.role)
        self.client.login(username='testuserbook', password='pass')

    def test_textbook_request_form_view(self):
        response = self.client.get(reverse('create_textbook_request'))
        self.assertEqual(response.status_code, 200)

    def test_list_dropped_textbooks_redirect_for_anonymous(self):
        self.client.logout()
        response = self.client.get(reverse('list_dropped_textbooks'))
        self.assertEqual(response.status_code, 302)
