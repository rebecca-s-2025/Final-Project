from django.core.management.base import BaseCommand
from core.models import ForumCategory

class Command(BaseCommand):
    help = "Seed default forum categories"

    def handle(self, *args, **kwargs):
        categories = [
            {"name": "English", "description": "Discuss topics related to English."},
            {"name": "Math", "description": "Discuss topics related to Mathematics."},
            {"name": "Science", "description": "Discuss topics related to Science."},
            {"name": "Business", "description": "Discuss topics related to Business."},
            {"name": "Social Science", "description": "Discuss topics related to Social Science."},
            {"name": "Computer Science", "description": "Discuss topics related to Computer Science."},
        ]

        for category_data in categories:
            category, created = ForumCategory.objects.get_or_create(
                name=category_data["name"],
                defaults={"description": category_data["description"]},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Category "{category_data["name"]}" created.'))
            else:
                self.stdout.write(self.style.WARNING(f'Category "{category_data["name"]}" already exists.'))