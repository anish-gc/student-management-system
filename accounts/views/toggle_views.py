# views.py
from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class GenericToggleView(LoginRequiredMixin, View):
    """
    Generic view to toggle any boolean field for any model
    URL pattern: /api/toggle/<str:model_name>/<int:pk>/<str:field_name>/
    """

    # Define which models and fields are allowed to be toggled
    ALLOWED_TOGGLES = {
        "staff": {
            "model": "auth.User",  # app_label.ModelName
            "fields": ["is_active"],
            "permission_required": "auth.change_user",
            "display_name_field": "username",
        },
        "student": {
            "model": "students.Student",
            "fields": ["is_active"],
            "permission_required": "students.change_student",
            "display_name_field": "first_name",
        },
         "instructor": {
            "model": "students.Instructor",
            "fields": ["is_active"],
            "permission_required": "students.change_instructor",
            "display_name_field": "first_name",  
        },
        "course": {
            "model": "students.Course",
            "fields": ["is_active"],
            "permission_required": "students.change_course",
            "display_name_field": "name",
        },
        "enrollment": {
            "model": "students.Enrollment",
            "fields": ["is_active"],
            "permission_required": "students.change_enrollment",
            "display_name_field": "Enrollment Name",
        },
       
        "metadata": {
            "model": "students.MetaData",  
            "fields": ["is_active"],
            "permission_required": "students.change_metadata",
            "display_name_field": "key",  
        },
    }

    def _is_toggle_allowed(self, model_name, field_name):
        """Check if the model and field are allowed to be toggled"""
        if model_name not in self.ALLOWED_TOGGLES:
            return False
        return field_name in self.ALLOWED_TOGGLES[model_name]["fields"]

    def _check_permissions(self, user, model_name):
        """Check if user has permission to toggle this model"""
        if not user.is_authenticated:
            return False

        permission_required = self.ALLOWED_TOGGLES[model_name]["permission_required"]
        return user.has_perm(permission_required)

    def _get_model_class(self, model_name):
        """Get the model class from the model name"""
        model_path = self.ALLOWED_TOGGLES[model_name]["model"]
        app_label, model_class_name = model_path.split(".")
        return apps.get_model(app_label, model_class_name)

    def _get_instance(self, model_class, pk):
        """Get the instance of the model"""
        return model_class.objects.get(pk=pk)


# Alternative view with permission checking per instance
class GenericToggleWithObjectPermissionView(GenericToggleView):
    """
    Extended version that also checks object-level permissions
    Useful if you have object-level permissions set up
    """

    def _check_permissions(self, user, model_name, instance=None):
        """Check both model-level and object-level permissions"""
        # Check model-level permission first
        if not super()._check_permissions(user, model_name):
            return False

        # If instance is provided, check object-level permissions
        if instance and hasattr(user, "has_perm"):
            permission_required = self.ALLOWED_TOGGLES[model_name][
                "permission_required"
            ]

            return user.has_perm(permission_required)

        return True

    def post(self, request, model_name, pk, field_name="is_active"):
        """Override to include object-level permission check"""
        try:
            # Basic validation first
            if not self._is_toggle_allowed(model_name, field_name):
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"Toggle not allowed for {model_name}.{field_name}",
                    },
                    status=403,
                )

            # Get instance for object-level permission check
            model_class = self._get_model_class(model_name)
            instance = self._get_instance(model_class, pk)

            # Check permissions with instance
            if not self._check_permissions(request.user, model_name, instance):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "You do not have permission to perform this action",
                    },
                    status=403,
                )

            # Continue with the rest of the logic from parent class
            display_name_field = self.ALLOWED_TOGGLES[model_name]["display_name_field"]
            display_name = getattr(instance, display_name_field, f"{model_name} #{pk}")
            old_value = getattr(instance, field_name)
            new_value = not old_value
            with transaction.atomic():
                setattr(instance, field_name, new_value)
                instance.save(update_fields=[field_name])

            action = "activated" if new_value else "deactivated"
            logger.info(
                f"User {request.user.username} {action} {model_name} {display_name} (ID: {pk})"
            )

            response_data = {
                "success": True,
                "message": f"{display_name} has been {action} successfully!",
                field_name: new_value,
                "display_name": display_name,
                "model_name": model_name,
                "instance_id": pk,
            }

            if field_name == "is_active":
                response_data["is_active"] = new_value

            return JsonResponse(response_data)

        except ObjectDoesNotExist:
            return JsonResponse(
                {"success": False, "message": f"{model_name.title()} not found"},
                status=404,
            )

        except Exception as e:
            logger.error(f"Error toggling {model_name} {pk}: {str(e)}")
            return JsonResponse(
                {
                    "success": False,
                    "message": "An error occurred while updating the status",
                },
                status=500,
            )
