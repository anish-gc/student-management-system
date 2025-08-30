from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from datetime import timedelta
import random

from students.models.metadata_model import MetaData
from students.models.student_model import Student

class Command(BaseCommand):
    help = "Create 100 sample students with realistic data and random metadata"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing students before creating new ones",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Number of students to create (default: 100)",
        )

    def handle(self, *args, **options):
        fake = Faker()
        student_count = options["count"]

        if options["clear"]:
            self.stdout.write("Deleting all existing students...")
            Student.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("All students deleted successfully"))

        # Get all student metadata template objects
        student_metadata_keys = [
            "learning_style", "preferred_contact_method", "scholarship_status",
            "accessibility_needs", "emergency_contact", "advisor",
            "campus_residence", "graduation_track"
        ]
        
        metadata_templates = list(MetaData.objects.filter(key__in=student_metadata_keys))
        
        if not metadata_templates:
            self.stdout.write(self.style.ERROR("❌ No student metadata templates found!"))
            self.stdout.write(self.style.WARNING("Run create_sample_metadata command first"))
            return

        # Create students in bulk
        students_to_create = []
        for i in range(student_count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            student = Student(
                first_name=first_name,
                last_name=last_name,
                email=f"{first_name.lower()}.{last_name.lower()}{i}@example.com",
                date_of_birth=fake.date_between_dates(
                    timezone.now().date() - timedelta(days=25 * 365),
                    timezone.now().date() - timedelta(days=18 * 365)
                ),
                is_active=random.choice([True, True, True, False]),  # 75% active
                created_by_id=1,
            )
            students_to_create.append(student)

        created_students = Student.objects.bulk_create(students_to_create)

        # Assign random metadata templates to students
        metadata_stats = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
        
        for student in created_students:
            # Random number of metadata items (0 to all available)
            num_metadata = random.choices(
                range(len(metadata_templates) + 1),
                weights=[10, 15, 20, 25, 15, 10, 5, 3, 2],  # Weighted probabilities
                k=1
            )[0]
            
            metadata_stats[num_metadata] += 1
            
            if num_metadata > 0:
                # Select random metadata templates
                selected_metadata = random.sample(metadata_templates, num_metadata)
                # Assign the templates to student (this creates the relationship)
                student.metadata.set(selected_metadata)

        # Print statistics
        self.stdout.write(self.style.SUCCESS(f"✅ Successfully created {len(created_students)} students"))
        
        # Detailed metadata distribution
        self.stdout.write("\n📊 Metadata distribution:")
        for count, students_count in metadata_stats.items():
            if students_count > 0:
                self.stdout.write(f"   {count} metadata items: {students_count} students")

        # Show sample students
        self.stdout.write("\n👥 Sample students created:")
      