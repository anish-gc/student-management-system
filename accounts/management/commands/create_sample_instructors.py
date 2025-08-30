from django.core.management.base import BaseCommand
from faker import Faker
from students.models.course_model import Course
import random

from students.models.instructor_model import Instructor
from students.models.metadata_model import MetaData

class Command(BaseCommand):
    help = 'Create 100 sample instructors with realistic data and random associations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing instructors before creating new ones',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of instructors to create (default: 100)',
        )

    def handle(self, *args, **options):
        fake = Faker()
        instructor_count = options['count']
        
        if options['clear']:
            self.stdout.write('Deleting all existing instructors...')
            Instructor.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('All instructors deleted successfully')
            )

        # Get existing courses and metadata
        courses = list(Course.objects.all())
        instructor_metadata = list(MetaData.objects.filter(
            key__in=[
                "office_hours", "office_location", "teaching_specialties", 
                "years_experience", "phd_university", "research_interests",
                "preferred_communication", "available_for_advising"
            ]
        ))

        instructors_to_create = []
        
        for i in range(instructor_count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            instructors_to_create.append(Instructor(
                first_name=first_name,
                last_name=last_name,
                email=f"{first_name.lower()}.{last_name.lower()}{i}@university.edu",
                phone_number=fake.phone_number()[:15],
                created_by_id=1,
            ))

        # Bulk create instructors
        created_instructors = Instructor.objects.bulk_create(instructors_to_create)
        
        # Statistics tracking
        course_stats = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        metadata_stats = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
        
        for instructor in created_instructors:
            # Random course assignment (0-4 courses)
            if courses:
                num_courses = random.choices(
                    [0, 1, 2, 3, 4],
                    weights=[10, 20, 30, 25, 15],  # Weighted probabilities
                    k=1
                )[0]
                course_stats[num_courses] += 1
                
                if num_courses > 0:
                    instructor_courses = random.sample(courses, min(num_courses, len(courses)))
                    instructor.courses.set(instructor_courses)
            
            # Random metadata assignment (0-8 metadata items)
            if instructor_metadata:
                num_metadata = random.choices(
                    range(len(instructor_metadata) + 1),
                    weights=[5, 10, 15, 20, 20, 15, 10, 5, 5],  # Weighted probabilities
                    k=1
                )[0]
                metadata_stats[num_metadata] += 1
                
                if num_metadata > 0:
                    selected_metadata = random.sample(instructor_metadata, num_metadata)
                    instructor.metadata.set(selected_metadata)
        
        # Print statistics
        self.stdout.write(
            self.style.SUCCESS(f'✅ Successfully created {len(created_instructors)} instructors')
        )
        
        if courses:
            self.stdout.write("\n📚 Course assignments:")
            for count, instructors_count in course_stats.items():
                if instructors_count > 0:
                    self.stdout.write(f"   {count} courses: {instructors_count} instructors")
        
        if instructor_metadata:
            self.stdout.write("\n📊 Metadata distribution:")
            for count, instructors_count in metadata_stats.items():
                if instructors_count > 0:
                    self.stdout.write(f"   {count} metadata items: {instructors_count} instructors")
        
        # Show sample instructors
        self.stdout.write("\n👨‍🏫 Sample instructors created:")
        for instructor in created_instructors[:3]:
            course_count = instructor.courses.count()
            metadata_count = instructor.metadata.count()
            self.stdout.write(
                f"   {instructor.first_name} - "
                f"{course_count} courses, {metadata_count} metadata items"
            )