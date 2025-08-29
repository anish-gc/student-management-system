import logging
from django.db import models
from django.conf import settings
from typing import TypeVar, Optional, Type



logger = logging.getLogger(__name__)

T = TypeVar("T", bound="BaseModel")


class BaseModel(models.Model):
    """
    Abstract base model for all models in the project.
    Provides common fields and methods with robust error handling.
    """

    id = models.BigAutoField(primary_key=True, null=False, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(class)s_created",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(class)s_updated",
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    is_active = models.BooleanField(
        default=True, db_index=True, help_text="Status to check if the entity is active"
    )

    remarks = models.CharField(max_length=300, blank=True, null=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "created_at"]),
            models.Index(fields=["created_by", "is_active"]),
        ]

    @classmethod
    def get_by_reference_id(cls: Type[T], reference_id: str) -> Optional[T]:
        """
        Get an object by its reference_id.

        Args:
            reference_id: The reference ID to search for

        Returns:
            The object if found, None otherwise
        """
        try:
            return cls.objects.get(reference_id=reference_id)
        except cls.DoesNotExist:
            return None
        except cls.MultipleObjectsReturned:
            logger.warning(
                f"Multiple {cls.__name__} found for reference_id={reference_id}"
            )
            return None
        except Exception as e:
            logger.exception(f"Unexpected error in get_by_reference_id: {e}")
            return None

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id}, reference_id={self.reference_id})"
        )
