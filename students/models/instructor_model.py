


from students.models.course_model import Course
from utilities.models import BaseModel
from django.db import models

class Instructor(BaseModel):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)

    phone_number = models.CharField(max_length=15, blank=True)
    courses = models.ManyToManyField(Course, related_name='instructors', blank=True)
   
    metadata = models.ManyToManyField("MetaData", blank=True, related_name='instructors')
    
    class Meta:
        db_table = 'instructors'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['last_name', 'first_name']),
        ]
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"Prof. {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"