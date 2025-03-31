from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import ForumPost, PostLike, Comment, CommentLike, StudentNote, NoteLike, Role, Category

User = get_user_model()

class GamificationTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='User', role_type='U')
        self.user = User.objects.create_user(username='user', email='user@example.com', password='pass', role=self.role)
        self.other = User.objects.create_user(username='other', email='other@example.com', password='pass', role=self.role)

        # 🔥 Create a Category to avoid ForeignKey errors
        self.forum_category = Category.objects.create(name='Forum', category_type='FORUM')
        self.note_category = Category.objects.create(name='Notes', category_type='NOTE')

    def test_post_like_adds_point(self):
        post = ForumPost.objects.create(
            title="Test", content="Post content", author=self.user, category=self.forum_category
        )
        self.client.force_login(self.other)
        PostLike.objects.create(user=self.other, post=post)
        self.user.refresh_from_db()
        self.assertEqual(self.user.points, 2)

    def test_comment_like_adds_point(self):
        post = ForumPost.objects.create(
            title="Test", content="Post content", author=self.user, category=self.forum_category
        )
        comment = Comment.objects.create(content="Nice post", author=self.user, content_object=post)
        self.client.force_login(self.other)
        CommentLike.objects.create(user=self.other, comment=comment)
        self.user.refresh_from_db()
        self.assertEqual(self.user.points, 2)

    def test_note_like_adds_point(self):
        note = StudentNote.objects.create(
            title="Note", content="Some text", author=self.user, category=self.note_category
        )
        self.client.force_login(self.other)
        NoteLike.objects.create(user=self.other, note=note)
        self.user.refresh_from_db()
        self.assertEqual(self.user.points, 2)