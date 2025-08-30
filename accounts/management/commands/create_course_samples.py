# management/commands/create_sample_courses.py
from django.core.management.base import BaseCommand
from students.models.course_model import Course
from students.models.metadata_model import MetaData

class Command(BaseCommand):
    help = 'Create sample courses with metadata'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing courses before creating new ones',
        )

    def handle(self, *args, **options):
        # Course definitions with integrated metadata
        course_definitions = [
            {
                'name': 'Introduction to Computer Science',
                'course_code': 'CS101',
                'description': 'Fundamentals of programming and computer science principles',
                'metadata': {
                    'prerequisites': 'None',
                    'required_materials': 'Introduction to Python Programming, 3rd Edition',
                    'credit_hours': '4',
                    'department': 'Computer Science',
                    'course_level': 'Undergraduate 100-level',
                    'syllabus_version': '2024-1',
                    'lab_required': 'false',
                    'max_capacity': '40'
                }
            },
            {
                'name': 'Calculus I',
                'course_code': 'MATH101',
                'description': 'Differential and integral calculus of one variable',
                'metadata': {
                    'prerequisites': 'High School Algebra',
                    'required_materials': 'Calculus: Early Transcendentals, 8th Edition',
                    'credit_hours': '4',
                    'department': 'Mathematics',
                    'course_level': 'Undergraduate 100-level',
                    'syllabus_version': '2024-1',
                    'lab_required': 'false',
                    'max_capacity': '35'
                }
            },
            {
                'name': 'General Chemistry',
                'course_code': 'CHEM101',
                'description': 'Basic principles of chemistry including atomic structure and reactions',
                'metadata': {
                    'prerequisites': 'High School Chemistry',
                    'required_materials': 'Chemistry: The Central Science, 14th Edition',
                    'credit_hours': '4',
                    'department': 'Chemistry',
                    'course_level': 'Undergraduate 100-level',
                    'syllabus_version': '2024-1',
                    'lab_required': 'true',
                    'max_capacity': '24'
                }
            },
            {
                'name': 'Introduction to Psychology',
                'course_code': 'PSYC101',
                'description': 'Survey of major concepts and theories in psychology',
                'metadata': {
                    'prerequisites': 'None',
                    'required_materials': 'Psychology, 13th Edition',
                    'credit_hours': '3',
                    'department': 'Psychology',
                    'course_level': 'Undergraduate 100-level',
                    'syllabus_version': '2024-1',
                    'lab_required': 'false',
                    'max_capacity': '50'
                }
            },
            {
                'name': 'English Composition',
                'course_code': 'ENG101',
                'description': 'Development of writing skills for academic purposes',
                'metadata': {
                    'prerequisites': 'None',
                    'required_materials': 'The Norton Field Guide to Writing, 5th Edition',
                    'credit_hours': '3',
                    'department': 'English',
                    'course_level': 'Undergraduate 100-level',
                    'syllabus_version': '2024-1',
                    'lab_required': 'false',
                    'max_capacity': '25'
                }
            },
            {
                'name': 'Principles of Economics',
                'course_code': 'ECON101',
                'description': 'Introduction to microeconomic and macroeconomic principles',
                'metadata': {
                    'prerequisites': 'None',
                    'required_materials': 'Principles of Economics, 9th Edition',
                    'credit_hours': '3',
                    'department': 'Economics',
                    'course_level': 'Undergraduate 100-level',
                    'syllabus_version': '2024-1',
                    'lab_required': 'false',
                    'max_capacity': '45'
                }
            },
            {
                'name': 'World History',
                'course_code': 'HIST101',
                'description': 'Survey of world civilizations from ancient times to present',
                'metadata': {
                    'prerequisites': 'None',
                    'required_materials': 'World Civilizations: The Global Experience, 8th Edition',
                    'credit_hours': '3',
                    'department': 'History',
                    'course_level': 'Undergraduate 100-level',
                    'syllabus_version': '2024-1',
                    'lab_required': 'false',
                    'max_capacity': '55'
                }
            },
            {
                'name': 'Introduction to Biology',
                'course_code': 'BIO101',
                'description': 'Study of living organisms and life processes',
                'metadata': {
                    'prerequisites': 'High School Biology',
                    'required_materials': 'Biology, 11th Edition',
                    'credit_hours': '4',
                    'department': 'Biology',
                    'course_level': 'Undergraduate 100-level',
                    'syllabus_version': '2024-1',
                    'lab_required': 'true',
                    'max_capacity': '24'
                }
            }
        ]

        if options['clear']:
            self.stdout.write('Deleting all existing courses...')
            Course.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All courses deleted successfully'))

        # Get all metadata templates at once
        metadata_keys = set()
        for course_def in course_definitions:
            metadata_keys.update(course_def['metadata'].keys())
        
        metadata_templates = MetaData.objects.filter(key__in=metadata_keys)
        metadata_dict = {meta.key: meta for meta in metadata_templates}

        # Check for missing metadata templates
        missing_metadata = metadata_keys - set(metadata_dict.keys())
        if missing_metadata:
            self.stdout.write(
                self.style.ERROR(f"Missing metadata templates: {', '.join(missing_metadata)}")
            )
            self.stdout.write(
                self.style.WARNING("Run create_sample_metadata command first")
            )
            return

        created_courses = []
        metadata_stats = []

        for course_def in course_definitions:
            # Create course
            course, created = Course.objects.get_or_create(
                course_code=course_def['course_code'],
                defaults={
                    'name': course_def['name'],
                    'description': course_def['description'],
                    'created_by_id': 1,
                    'updated_by_id': 1,
                }
            )
            
            if created:
                # Assign metadata
                metadata_to_assign = []
                for key, value in course_def['metadata'].items():
                    metadata_obj = metadata_dict[key]
                    metadata_to_assign.append(metadata_obj)
                
                course.metadata.set(metadata_to_assign)
                created_courses.append(course)
                metadata_stats.append(len(metadata_to_assign))
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Created: {course.course_code} - {course.name}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Already exists: {course.course_code}")
                )

        # Print summary
        if created_courses:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Successfully created {len(created_courses)} courses'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'📊 Metadata: {sum(metadata_stats)} total items '
                    f'(avg {sum(metadata_stats)/len(metadata_stats):.1f} per course)'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('No new courses created (all already exist)')
            )