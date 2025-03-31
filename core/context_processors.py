from .models import Notification

def notification_context(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, read=False).count()
        recent = Notification.objects.filter(user=request.user).order_by('-created_on')[:20]
        return {
            'unread_notifications_count': unread_count,
            'recent_notifications': recent
        }
    return {}