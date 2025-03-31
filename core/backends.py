from django.db import models  # Add missing import
from django.contrib.auth import get_user_model

class UsernameOrEmailBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(
                models.Q(username__iexact=username) |
                models.Q(email__iexact=username)
            )
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            return None
        except UserModel.MultipleObjectsReturned:
            return UserModel.objects.filter(
                models.Q(username__iexact=username) |
                models.Q(email__iexact=username)
            ).first()

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None