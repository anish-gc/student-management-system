# models.py (in your accounts app or wherever your Dashboard model is)
from django.db import models

class Dashboard(models.Model):
    """Dummy model to hold dashboard permissions"""
    class Meta:
        # This creates the view_dashboard permission
        permissions = [
            ("view_dashboard", "Can view dashboard"),
        ]
        # Hide this model from admin if you don't want it visible
        default_permissions = ()