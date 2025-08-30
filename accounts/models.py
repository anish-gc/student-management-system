from django.db import models

class Dashboard(models.Model):
    """Dummy model to hold dashboard permissions"""
    class Meta:
        permissions = [
            ("view_dashboard", "Can view dashboard"),
        ]
        # Hide this model from admin if you don't want it visible
        default_permissions = ()