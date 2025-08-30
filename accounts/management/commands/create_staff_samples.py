# management/commands/create_sample_staff_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from faker import Faker
import random

class Command(BaseCommand):
    help = "Create 50 sample staff users with different roles"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all non-superuser staff before creating new ones",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=50,
            help="Number of staff users to create (default: 50)",
        )

    def handle(self, *args, **options):
        fake = Faker()
        user_count = options["count"]

        if options["clear"]:
            self.stdout.write("Deleting all non-superuser staff users...")
            User.objects.filter(is_staff=True, is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS("All staff users deleted successfully"))

        # Get or create role groups in bulk
        role_names = ["admin", "staff", "accountant"]
        groups = {}
        
        for name in role_names:
            group, created = Group.objects.get_or_create(name=name)
            groups[name] = group
            if created:
                self.stdout.write(f"Created group: {name}")

        # Pre-generate unique usernames and emails
        existing_usernames = set(User.objects.values_list('username', flat=True))
        existing_emails = set(User.objects.values_list('email', flat=True))
        
        users_data = []
        for i in range(user_count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            # Generate unique username
            base_username = f"{first_name.lower()}.{last_name.lower()}"
            username = base_username
            counter = 1
            while username in existing_usernames:
                username = f"{base_username}{counter}"
                counter += 1
            existing_usernames.add(username)
            
            # Generate unique email
            base_email = f"{first_name.lower()}.{last_name.lower()}@company.com"
            email = base_email
            counter = 1
            while email in existing_emails:
                email = f"{first_name.lower()}.{last_name.lower()}{counter}@company.com"
                counter += 1
            existing_emails.add(email)
            
            users_data.append({
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'password': "staff123"  # Will be hashed later
            })

        # Create users in bulk without saving passwords yet
        users_to_create = []
        for user_data in users_data:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_staff=True,
                is_active=True,
                is_superuser=False,
                date_joined=timezone.now()
            )
            # Store plain password temporarily for bulk password setting
            user._plain_password = user_data['password']
            users_to_create.append(user)

        # Bulk create users (without passwords)
        created_users = User.objects.bulk_create(users_to_create)
        
        # Set passwords in bulk using update() for better performance
        for user in created_users:
            user.set_password(user._plain_password)
            # Clear temporary attribute
            delattr(user, '_plain_password')
        
        # Update passwords in bulk (this is more efficient than individual saves)
        User.objects.bulk_update(created_users, ['password'])

        # Prepare role assignments using bulk operations
        role_assignments = []
        role_stats = {
            'no_roles': 0,
            'one_role': 0,
            'two_roles': 0,
            'all_roles': 0
        }

        # Define role probabilities and combinations
        role_probabilities = [
            (0.1, []),                    # 10% no roles
            (0.4, [random.choice(role_names)]),  # 40% one random role
            (0.3, random.sample(role_names, 2)), # 30% two random roles
            (0.2, role_names)              # 20% all roles
        ]

        for user in created_users:
            # Choose role combination based on weights
            choice = random.choices(
                role_probabilities,
                weights=[prob for prob, _ in role_probabilities],
                k=1
            )[0]
            
            roles_to_assign = choice[1]
            
            # Update statistics
            if not roles_to_assign:
                role_stats['no_roles'] += 1
            elif len(roles_to_assign) == 1:
                role_stats['one_role'] += 1
            elif len(roles_to_assign) == 2:
                role_stats['two_roles'] += 1
            else:
                role_stats['all_roles'] += 1
            
            # Add role assignments
            for role_name in roles_to_assign:
                role_assignments.append(user.groups.through(user_id=user.id, group_id=groups[role_name].id))

        # Bulk create role assignments
        if role_assignments:
            user.groups.through.objects.bulk_create(role_assignments)

        # Print statistics
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(created_users)} staff users"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Role distribution: "
                f"{role_stats['no_roles']} with no roles, "
                f"{role_stats['one_role']} with one role, "
                f"{role_stats['two_roles']} with two roles, "
                f"{role_stats['all_roles']} with all three roles"
            )
        )
        
        # Print some example users and their roles
        self.stdout.write("\nExample users created:")
        
       