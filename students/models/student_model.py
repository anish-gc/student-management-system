from utilities.models import BaseModel
from django.db import models


class Student(BaseModel):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField()
  

    metadata = models.ManyToManyField("MetaData", blank=True, related_name="students")

    class Meta:
        db_table = "students"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["last_name", "first_name"]),
        ]
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


    