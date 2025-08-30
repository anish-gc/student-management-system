from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from students.models.metadata_model import MetaData

User = get_user_model()


class Command(BaseCommand):
    help = "Create sample metadata entries for students, courses, enrollments, and instructors"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing metadata before creating new samples",
        )

    def handle(self, *args, **options):
        # Get or create a default user for created_by field
        default_user = User.objects.filter(is_superuser=True).first()

        # Define all metadata samples
        metadata_samples = {
            "student": [
                {"key": "learning_style", "value": "visual"},
                {"key": "preferred_contact_method", "value": "email"},
                {"key": "scholarship_status", "value": "merit-based"},
                {"key": "accessibility_needs", "value": "extra time on exams"},
                {"key": "emergency_contact", "value": "John Doe - 555-0123"},
                {"key": "advisor", "value": "Dr. Smith"},
                {"key": "campus_residence", "value": "North Hall Room 204"},
                {"key": "graduation_track", "value": "4-year plan"},
            ],
            "course": [
                {"key": "prerequisites", "value": "MATH 101, MATH 102"},
                {
                    "key": "required_materials",
                    "value": "Textbook: Calculus Early Transcendentals",
                },
                {"key": "credit_hours", "value": "3"},
                {"key": "department", "value": "Mathematics"},
                {"key": "course_level", "value": "Undergraduate 200-level"},
                {"key": "syllabus_version", "value": "2023-2"},
                {"key": "lab_required", "value": "true"},
                {"key": "max_capacity", "value": "30"},
            ],
            "enrollment": [
                {"key": "attendance_percentage", "value": "92.5"},
                {"key": "participation_score", "value": "A"},
                {"key": "last_accessed", "value": "2023-10-15 14:32:00"},
                {"key": "assignment_submissions", "value": "8/10 completed"},
                {"key": "status", "value": "active"},
                {"key": "financial_aid_applied", "value": "true"},
                {"key": "special_approval", "value": "Department Chair override"},
                {"key": "learning_goals", "value": "Master differential equations"},
            ],
            "instructor": [
                {"key": "office_hours", "value": "MWF 10am-12pm"},
                {"key": "office_location", "value": "Science Building Room 305"},
                {"key": "teaching_specialties", "value": "Calculus, Linear Algebra"},
                {"key": "years_experience", "value": "12"},
                {"key": "phd_university", "value": "Stanford University"},
                {
                    "key": "research_interests",
                    "value": "Applied Mathematics, Numerical Analysis",
                },
                {
                    "key": "preferred_communication",
                    "value": "Email during business hours",
                },
                {"key": "available_for_advising", "value": "true"},
            ],
        }

        if options["clear"]:
            self.stdout.write("Deleting all existing metadata...")
            MetaData.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("All metadata deleted successfully"))

        created_count = 0

        # Create metadata entries only if they don't exist
        for category, items in metadata_samples.items():
            for item in items:
                obj, created = MetaData.objects.get_or_create(
                    key=item["key"],
                    defaults={
                        "value": item["value"],
                        "created_by": default_user,
                    },
                )
                if created:
                    created_count += 1

        # Print summary
        total_items = sum(len(items) for items in metadata_samples.values())
        self.stdout.write(
            self.style.SUCCESS(
                f"Metadata creation completed: {created_count} new entries created "
                f"(skipped {total_items - created_count} existing entries)"
            )
        )

        # Print detailed breakdown
        for category, items in metadata_samples.items():
            self.stdout.write(
                self.style.SUCCESS(f"  {category}: {len(items)} metadata entries")
            )
