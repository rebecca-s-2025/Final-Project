from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Role

User = get_user_model()

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.role = Role.objects.create(name='User', role_type='U')
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='pass', role=self.role)

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')

    def test_login_required_profile_view(self):
        response = self.client.get(reverse('view_profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.client.login(username='testuser', password='pass')
        response = self.client.get(reverse('view_profile'))
        self.assertEqual(response.status_code, 200)