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

    def save(self, *args, **kwargs):
        """
        Override save method to automatically set created_by and updated_by
        using thread-local storage from middleware.
        """
        try:
            # Importing to avoid circular imports
            from accounts.middleware import get_current_user
            
            current_user = get_current_user()
            if current_user and current_user.is_authenticated:
                if not self.pk:  # New instance being created
                    self.created_by = current_user
                else:    
                    self.updated_by = current_user
                
        except ImportError:
            logger.warning("Middleware not available for user tracking")
        except Exception as e:
            logger.error(f"Error setting audit fields: {e}")
        
        super().save(*args, **kwargs)