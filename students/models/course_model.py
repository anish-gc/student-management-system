from utilities.models import BaseModel
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator


class Course(BaseModel):
    name = models.CharField(max_length=200)
    course_code = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(
                r"^[A-Z]{2,4}\d{3,4}$",
                "Course code must be in format CS101 or MATH1001",
            )
        ],
    )
    description = models.TextField(blank=True)
   
    metadata = models.ManyToManyField("MetaData", blank=True, related_name="courses")

    class Meta:
        db_table = 'courses'
        indexes = [
            models.Index(fields=["course_code"]),
            models.Index(fields=["name"]),
        ]
        ordering = ["course_code"]

    def __str__(self):
        return f"{self.course_code} - {self.name}"
