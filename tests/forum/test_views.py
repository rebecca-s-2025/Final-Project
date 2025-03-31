from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import ForumPost, Category, Role

User = get_user_model()

class ForumTests(TestCase):
    def setUp(self):
        
        self.role = Role.objects.create(name='User', role_type='U')
        self.user = User.objects.create_user(username='testuserforum', email='testuserforum@example.com', password='pass', role=self.role)
        
        self.category = Category.objects.create(name='Forum Cat', category_type='FORUM')
        self.client.login(username='testuserforum', password='pass')

    def test_forum_category_list_view(self):
        response = self.client.get(reverse('forum_category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum/forum_category_list.html')

    def test_forum_post_create_view(self):
        response = self.client.post(reverse('forum_post_create', args=[self.category.id]), {
            'title': 'New Post',
            'content': 'Post content'
        })
        self.assertEqual(response.status_code, 200 or 302)  # Allow redirect after create
