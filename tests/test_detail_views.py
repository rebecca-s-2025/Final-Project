from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import ForumPost, Comment, StudentNote, Category, Role

User = get_user_model()

class DetailViewsTests(TestCase):
    def setUp(self):
        
        self.role = Role.objects.create(name='User', role_type='U')
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='pass', role=self.role)

        self.category = Category.objects.create(name="General", category_type="FORUM")
        self.post = ForumPost.objects.create(title="Post", content="Test", author=self.user, category=self.category)
        self.note = StudentNote.objects.create(title="Note", content="Some note", author=self.user, category=self.category)

    def test_forum_post_detail_view(self):
        url = reverse("forum_post_detail", args=[self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)

    def test_note_detail_view(self):
        url = reverse("note_detail", args=[self.note.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.note.title)