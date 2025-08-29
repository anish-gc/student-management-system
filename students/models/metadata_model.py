from utilities.models import BaseModel
from django.db import models


class MetaData(BaseModel):
    key = models.CharField(max_length=100, db_index=True)
    value = models.TextField()

    class Meta:
        db_table = 'metadata'
        indexes = [
            models.Index(fields=["key"]),
            models.Index(fields=["created_at"]),
        ]
        verbose_name = "Metadata"
        verbose_name_plural = "Metadata"

    def __str__(self):
        return f"{self.key}: {self.value[:50]}"
