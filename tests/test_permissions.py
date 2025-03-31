from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import ForumPost, Category, Role

User = get_user_model()

class PermissionsTests(TestCase):
    def setUp(self):
        
        self.role = Role.objects.create(name='User', role_type='U')
        self.user = User.objects.create_user(username='u1', email='u1@example.com', password='pass', role=self.role)
        self.other_user = User.objects.create_user(username='u2', email='u2@example.com', password='pass', role=self.role)
        self.category = Category.objects.create(name="General", category_type="FORUM")
        self.post = ForumPost.objects.create(title="Post", content="Test", author=self.user, category=self.category)

    def test_user_cannot_like_own_post(self):
        self.client.force_login(self.user)
        url = reverse("like_post", args=[self.post.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_access_like(self):
        url = reverse("like_post", args=[self.post.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login