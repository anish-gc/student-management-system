



from students.models.course_model import Course
from students.models.student_model import Student
from utilities.models import BaseModel
from django.db import models
from django.core.validators import  MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
class Enrollment(BaseModel):
    GRADE_CHOICES = [
        ('A+', 'A+'), ('A', 'A'), ('A-', 'A-'),
        ('B+', 'B+'), ('B', 'B'), ('B-', 'B-'),
        ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'),
        ('D+', 'D+'), ('D', 'D'), ('F', 'F'),
        ('I', 'Incomplete'), ('W', 'Withdrawn'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True)
    score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    completion_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
   
    metadata = models.ManyToManyField("MetaData", blank=True, related_name='enrollments')
    
    class Meta:
        db_table = 'enrollments'
        constraints = [
            models.UniqueConstraint(fields=['student', 'course'], name='unique_student_course_enrollment')
        ]
        indexes = [
            models.Index(fields=['student', 'course']),
        ]
        ordering = ['-created_at']
    
    def clean(self):
        if self.score is not None and (self.score < 0 or self.score > 100):
            raise ValidationError({'score': 'Score must be between 0 and 100.'})
    
    def __str__(self):
        return f"{self.student.full_name} - {self.course.course_code}"
    
    @property
    def grade_points(self):
        grade_map = {
            'A+': 4.0, 'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'F': 0.0,
        }
        return grade_map.get(self.grade, 0.0)