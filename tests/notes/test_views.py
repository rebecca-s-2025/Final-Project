from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Category, StudentNote, Role

User = get_user_model()

class NotesTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='User', role_type='U')
        self.user = User.objects.create_user(username='testusernote', email='testusernote@example.com', password='pass', role=self.role)
        self.category = Category.objects.create(name='Note Cat', category_type='NOTE')
        self.client.login(username='testusernote', password='pass')

    def test_notes_category_list_view(self):
        response = self.client.get(reverse('notes_category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/notes_category_list.html')

    def test_notes_list_view(self):
        response = self.client.get(reverse('notes_list', args=[self.category.id]))
        self.assertEqual(response.status_code, 200)
