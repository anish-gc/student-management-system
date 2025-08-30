from django.core.management.base import BaseCommand
from django.utils import timezone
from students.models.enrollment_model import Enrollment
from students.models.metadata_model import MetaData
from students.models.student_model import Student
from students.models.course_model import Course
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Create sample enrollments with random assignments and metadata'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing enrollments before creating new ones',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=200,
            help='Number of enrollments to create (default: 200)',
        )

    def handle(self, *args, **options):
        # Get existing data
        students = list(Student.objects.filter(is_active=True))
        courses = list(Course.objects.all())
        
        if not students or not courses:
            self.stdout.write(
                self.style.ERROR('Please create students and courses first!')
            )
            return

        # Get enrollment metadata templates
        enrollment_metadata_keys = [
            "attendance_percentage", "participation_score", "last_accessed",
            "assignment_submissions", "status", "financial_aid_applied",
            "special_approval", "learning_goals"
        ]
        
        enrollment_metadata = list(MetaData.objects.filter(key__in=enrollment_metadata_keys))

        if options['clear']:
            self.stdout.write('Deleting all existing enrollments...')
            Enrollment.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All enrollments deleted successfully'))

        enrollments_to_create = []
        existing_enrollments = set()
        
        enrollment_count = options['count']
        
        for i in range(enrollment_count):
            # Select random student and course
            student = random.choice(students)
            course = random.choice(courses)
            
            # Avoid duplicate enrollments
            enrollment_key = (student.id, course.id)
            if enrollment_key in existing_enrollments:
                continue
                
            existing_enrollments.add(enrollment_key)
            
            # Determine enrollment status and dates
            current_year = timezone.now().year
            semester_start = datetime(current_year, random.choice([1, 8]), 1)
            enrollment_date = semester_start + timedelta(days=random.randint(0, 14))
            
            # 80% completed, 20% current
            is_completed = random.random() < 0.8
            
            if is_completed:
                completion_date = enrollment_date + timedelta(days=random.randint(90, 120))
                grade = random.choice([g[0] for g in Enrollment.GRADE_CHOICES if g[0] not in ['I', 'W']])
                
                # Calculate score based on grade
                grade_score_map = {
                    'A+': (95, 100), 'A': (90, 94), 'A-': (85, 89),
                    'B+': (80, 84), 'B': (75, 79), 'B-': (70, 74),
                    'C+': (65, 69), 'C': (60, 64), 'C-': (55, 59),
                    'D+': (50, 54), 'D': (45, 49), 'F': (0, 44),
                }
                score_range = grade_score_map.get(grade, (0, 100))
                score = random.uniform(score_range[0], score_range[1])
            else:
                completion_date = None
                grade = ''
                score = None
            
            # Create enrollment
            enrollment = Enrollment(
                student=student,
                course=course,
                grade=grade,
                score=score,
                completion_date=completion_date,
                created_at=enrollment_date,
                created_by_id=1,
                updated_by_id=1,
            )
            
            enrollments_to_create.append(enrollment)

        # Bulk create enrollments
        created_enrollments = Enrollment.objects.bulk_create(enrollments_to_create)
        
        # Assign random metadata to enrollments (0-8 items)
        metadata_stats = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
        
        for enrollment in created_enrollments:
            # Random number of metadata items
            num_metadata = random.choices(
                range(len(enrollment_metadata) + 1),
                weights=[5, 10, 15, 20, 20, 15, 10, 5, 5],
                k=1
            )[0]
            
            metadata_stats[num_metadata] += 1
            
            if num_metadata > 0:
                selected_metadata = random.sample(enrollment_metadata, num_metadata)
                enrollment.metadata.set(selected_metadata)
        
        # Calculate statistics
        student_enrollments = {}
        course_enrollments = {}
        
        for enrollment in created_enrollments:
            student_enrollments[enrollment.student_id] = student_enrollments.get(enrollment.student_id, 0) + 1
            course_enrollments[enrollment.course_id] = course_enrollments.get(enrollment.course_id, 0) + 1

        # Print results
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully created {len(created_enrollments)} enrollments'))
        
        self.stdout.write(f"\n📊 Enrollment distribution:")
        self.stdout.write(f"   Students with enrollments: {len(student_enrollments)}/{len(students)}")
        self.stdout.write(f"   Courses with enrollments: {len(course_enrollments)}/{len(courses)}")
        
        if student_enrollments:
            avg_per_student = sum(student_enrollments.values()) / len(student_enrollments)
            self.stdout.write(f"   Avg courses per student: {avg_per_student:.1f}")
        
        self.stdout.write(f"\n📝 Metadata distribution:")
        for count, enrollments_count in metadata_stats.items():
            if enrollments_count > 0:
                self.stdout.write(f"   {count} metadata items: {enrollments_count} enrollments")
        
        # Show sample enrollments
        self.stdout.write(f"\n🎓 Sample enrollments:")
        for enrollment in created_enrollments[:5]:
            status = "✅ Completed" if enrollment.completion_date else "📚 Active"
            grade_info = f", Grade: {enrollment.grade}" if enrollment.grade else ""
            metadata_count = enrollment.metadata.count()
            self.stdout.write(
                f"   {enrollment.student.first_name} → {enrollment.course.course_code} "
                f"({status}{grade_info}, {metadata_count} metadata items)"
            )