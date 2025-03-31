from django.core.management.base import BaseCommand
from core.models import Library

class Command(BaseCommand):
    help = 'Seed library data'

    def handle(self, *args, **kwargs):
        libraries = [
            {
                "name": "Library 1",
                "address": "Address 1",
                "latitude": 1.29027,
                "longitude": 103.851959,
            },
            {
                "name": "Library 2",
                "address": "Address 2",
                "latitude": 1.3521,
                "longitude": 103.8198,
            },
        ]

        for lib in libraries:
            Library.objects.get_or_create(
                name=lib["name"],
                address=lib["address"],
                latitude=lib["latitude"],
                longitude=lib["longitude"],
            )

        self.stdout.write(self.style.SUCCESS("Libraries seeded successfully."))