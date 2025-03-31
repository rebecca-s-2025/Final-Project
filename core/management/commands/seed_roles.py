from django.core.management.base import BaseCommand
from core.models import Role

class Command(BaseCommand):
    help = 'Creates default system roles if they don\'t exist'

    def handle(self, *args, **kwargs):
        default_roles = [
            {
                'name': 'Owner',
                'role_type': 'O',
                'description': 'System owner with full privileges'
            },
            {
                'name': 'Admin',
                'role_type': 'A',
                'description': 'Administrator with elevated privileges'
            },
            {
                'name': 'User',
                'role_type': 'U',
                'description': 'Regular system user'
            }
        ]

        created_count = 0
        for role_data in default_roles:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'role_type': role_data['role_type'],
                    'description': role_data['description'],
                    'mode': 'Active'
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created {role_data['name']} role")

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {created_count} roles. '
                f'Total roles in system: {Role.objects.count()}'
            )
        )
