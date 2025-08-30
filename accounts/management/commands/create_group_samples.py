from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group


class Command(BaseCommand):
    help = "Create predefined roles (Admin, staff)"

    def handle(self, *args, **kwargs):
        predefined_roles = [
            {"name": "admin"},
            {"name": "staff"},
            {"name": "accountant"},
        ]
        for role_data in predefined_roles:
            group, created = Group.objects.get_or_create(
                name=role_data["name"].lower(),
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Created role: {group.name}"))
