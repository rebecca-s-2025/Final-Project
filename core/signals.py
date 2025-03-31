# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PostLike, CommentLike, NoteLike, Notification, ForumPost, Comment, StudentNote
from django.contrib.contenttypes.models import ContentType

@receiver(post_save, sender=PostLike)
def notify_post_like(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.post.author,
            message=f"Your post '{instance.post.title}' received a new like!",
            notification_type='REPLY',  # or create a new one: 'LIKE'
            content_type=ContentType.objects.get_for_model(ForumPost),
            object_id=instance.post.id,
            content_object=instance.post
        )

@receiver(post_save, sender=CommentLike)
def notify_comment_like(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.comment.author,
            message=f"Your comment received a new like!",
            notification_type='REPLY',
            content_type=ContentType.objects.get_for_model(Comment),
            object_id=instance.comment.id,
            content_object=instance.comment
        )

@receiver(post_save, sender=NoteLike)
def notify_note_like(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.note.author,
            message=f"Your note '{instance.note.title}' received a new like!",
            notification_type='REPLY',
            content_type=ContentType.objects.get_for_model(StudentNote),
            object_id=instance.note.id,
            content_object=instance.note
        )

# Gamification: Notify on level up
@receiver(post_save, sender=PostLike)
@receiver(post_save, sender=CommentLike)
@receiver(post_save, sender=NoteLike)
def handle_like_actions(sender, instance, created, **kwargs):
    if not created:
        return

    # Identify the user
    if hasattr(instance, 'post'):
        user = instance.post.author
    elif hasattr(instance, 'comment'):
        user = instance.comment.author
    elif hasattr(instance, 'note'):
        user = instance.note.author
    else:
        return

    # Capture old level
    old_level = user.level

    # Increase points
    user.points += 1
    user.update_level()  # This will also save the user

    # Notify level-up
    if user.level > old_level:
        Notification.objects.create(
            user=user,
            message=f"Congrats! You've reached Level {user.level} 🎉",
            notification_type='LEVEL_UP',
            content_type=None,
            object_id=None
        )
