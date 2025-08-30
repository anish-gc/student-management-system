import logging
from django.http import JsonResponse
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from django.contrib.auth.models import Group, Permission

from accounts.forms.group_form import GroupForm
from utilities.pagination_mixin import PaginatedListMixin
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

# Configure logger
logger = logging.getLogger(__name__)


class GroupView(LoginRequiredMixin, PaginatedListMixin, View):
    """Group view for listing, adding, editing, and deleting groups"""

    login_url = "/login/"
    redirect_field_name = "next"
    paginate_by = 15  # Override default pagination

    def get(self, request, pk=None):
        """Handle GET requests based on URL name"""
        if request.resolver_match.url_name == "group-add":
            return self.add_group(request)
        elif request.resolver_match.url_name == "group-edit" and pk:
            return self.edit_group(request, pk)
        elif request.resolver_match.url_name == "group-manage-permissions" and pk:
            return self.manage_permissions(request, pk)

        else:
            return self.group_list(request)

    def post(self, request, pk=None):
        """Handle POST requests based on URL pattern"""
        if request.resolver_match.url_name == "group-add":
            return self.add_group_submit(request)
        elif request.resolver_match.url_name == "group-edit" and pk:
            return self.edit_group_submit(request, pk)
        elif request.resolver_match.url_name == "group-delete" and pk:
            return self.delete(request, pk)
        elif request.resolver_match.url_name == "group-manage-permissions" and pk:
            return self.update_permissions(request, pk)
        return redirect("accounts:groups")

    def delete(self, request, pk=None):
        """Handle DELETE requests for group deletion"""
        if pk:
            return self.delete_group(request, pk)
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

    def get_queryset(self):
        """Get base queryset for groups with user count"""
        return Group.objects.annotate(user_count=Count("user")).all()

    def get_filtered_queryset(self, request):
        """Apply filters to the queryset"""
        queryset = self.get_queryset()

        # Search filter
        search_query = request.GET.get("search")
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query))

        # User count filter
        user_count_filter = request.GET.get("user_count")
        if user_count_filter:
            if user_count_filter == "empty":
                queryset = queryset.filter(user_count=0)
            elif user_count_filter == "has_users":
                queryset = queryset.filter(user_count__gt=0)

        # Permission filter
        permission_filter = request.GET.get("has_permissions")
        if permission_filter:
            if permission_filter.lower() == "true":
                queryset = queryset.filter(permissions__isnull=False)
            elif permission_filter.lower() == "false":
                queryset = queryset.filter(permissions__isnull=True)

        return queryset.distinct().order_by("name")

    def group_list(self, request):
        """Display paginated list of groups"""
        # Get filtered queryset
        filtered_queryset = self.get_filtered_queryset(request)

        # Get pagination context
        pagination_context = self.get_pagination_context(request, filtered_queryset)

        context = {
            **pagination_context,
            "current_filters": {
                "search": request.GET.get("search", ""),
                "user_count": request.GET.get("user_count", ""),
                "has_permissions": request.GET.get("has_permissions", ""),
            },
        }

        return render(request, "accounts/groups/groups_list.html", context)

    @method_decorator(permission_required("auth.add_group", raise_exception=True))
    def add_group(self, request):
        """Display add group form"""
        form = GroupForm()

        context = {
            "form": form,
            "is_adding": True,
            "page_title": "Add Group",
        }
        return render(request, "accounts/groups/groups_form.html", context)

    @method_decorator(permission_required("auth.add_group", raise_exception=True))
    def add_group_submit(self, request):
        """Process add group form submission"""
        form = GroupForm(request.POST)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            try:
                # Create the group
                group = form.save(commit=False)
                group.save()

                # Add permissions if selected
                permissions = form.cleaned_data.get("permissions")
                if permissions:
                    group.permissions.set(permissions)

                success_message = f"Group '{group.name}' added successfully!"

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect_url": request.build_absolute_uri(
                                reverse("accounts:groups")
                            ),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("accounts:groups")

            except Exception as e:
                error_message = f"Error adding group: {str(e)}"
                logger.error(f"Error adding group: {e}")

                if is_ajax:
                    return JsonResponse(
                        {"success": False, "error": error_message}, status=500
                    )
                else:
                    messages.error(request, error_message)
        else:
            # Form validation failed
            if is_ajax:
                errors = {}
                for field_name, field_errors in form.errors.items():
                    errors[field_name] = [str(error) for error in field_errors]

                return JsonResponse(
                    {
                        "success": False,
                        "errors": errors,
                        "message": "Please correct the errors below.",
                    },
                    status=400,
                )
            else:
                messages.error(request, "Please correct the errors below.")

        if not is_ajax:
            context = {
                "form": form,
                "is_adding": True,
                "page_title": "Add Group",
            }
            return render(request, "accounts/groups/groups_form.html", context)

    @method_decorator(permission_required("auth.change_group", raise_exception=True))
    def edit_group(self, request, pk):
        """Display edit group form"""
        group = get_object_or_404(Group, pk=pk)
        form = GroupForm(instance=group)

        context = {
            "form": form,
            "group_obj": group,
            "is_editing": True,
            "page_title": f"Edit Group: {group.name}",
        }
        return render(request, "accounts/groups/groups_form.html", context)

    @method_decorator(permission_required("auth.change_group", raise_exception=True))
    def edit_group_submit(self, request, pk):
        """Process edit group form submission"""
        group = get_object_or_404(Group, pk=pk)
        form = GroupForm(request.POST, instance=group)

        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            try:
                group = form.save(commit=False)
                group.save()
                form.save_m2m()  

                success_message = f"Group '{group.name}' updated successfully!"

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect_url": request.build_absolute_uri(
                                reverse("accounts:groups")
                            ),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("accounts:groups")

            except Exception as e:
                error_message = f"Error updating group: {str(e)}"
                logger.error(f"Error updating group: {e}")

                if is_ajax:
                    return JsonResponse(
                        {"success": False, "error": error_message}, status=500
                    )
                else:
                    messages.error(request, error_message)
        else:
            # Form validation failed
            if is_ajax:
                errors = {}
                for field_name, field_errors in form.errors.items():
                    errors[field_name] = [str(error) for error in field_errors]

                return JsonResponse(
                    {
                        "success": False,
                        "errors": errors,
                        "message": "Please correct the errors below.",
                    },
                    status=400,
                )
            else:
                messages.error(request, "Please correct the errors below.")

        if not is_ajax:
            context = {
                "form": form,
                "group_obj": group,
                "is_editing": True,
                "page_title": f"Edit Group: {group.name}",
            }
            return render(request, "accounts/groups/groups_form.html", context)

    @method_decorator(permission_required("auth.delete_group", raise_exception=True))
    def delete_group(self, request, pk):
        """Delete a group"""
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        try:
            group = get_object_or_404(Group, pk=pk)

            user_count = group.user_set.count()
            if user_count > 0:
                error_message = f"Cannot delete group '{group.name}' because it has {user_count} associated user(s). Please remove all users from this group before deleting."

                if is_ajax:
                    return JsonResponse(
                        {"success": False, "error": error_message}, status=400
                    )
                else:
                    messages.error(request, error_message)
                    return redirect("accounts:groups")

            group_name = group.name
            group.delete()
            success_message = f"Group '{group_name}' deleted successfully!"

            if is_ajax:
                return JsonResponse(
                    {
                        "success": True,
                        "message": success_message,
                        "redirect": reverse("accounts:groups"),
                    }
                )
            else:
                messages.success(request, success_message)
                return redirect("accounts:groups")

        except Exception as e:
            error_message = f"Error deleting group: {str(e)}"
            logger.error(f"Error deleting group: {e}")

            if is_ajax:
                return JsonResponse(
                    {"success": False, "error": error_message}, status=500
                )
            else:
                messages.error(request, error_message)
                return redirect("accounts:groups")

    @method_decorator(permission_required("auth.view_permission", raise_exception=True))
    def manage_permissions(self, request, pk):
        """Display permissions management interface for a group"""
        group = get_object_or_404(Group, pk=pk)

        all_permissions = (
            Permission.objects.select_related("content_type")
            .exclude(content_type__app_label__in=["admin", "sessions", "contenttypes"])
            .order_by("content_type__app_label", "content_type__model", "codename")
        )

        assigned_permissions = set(group.permissions.values_list("id", flat=True))

        # Organize permissions by app and model
        permissions_by_app = {}
        for permission in all_permissions:
            app_label = permission.content_type.app_label
            model_name = permission.content_type.model

            if app_label not in permissions_by_app:
                permissions_by_app[app_label] = {}
            if model_name not in permissions_by_app[app_label]:
                permissions_by_app[app_label][model_name] = []

            permissions_by_app[app_label][model_name].append(
                {
                    "permission": permission,
                    "is_assigned": permission.id in assigned_permissions,
                }
            )

        context = {
            "group_obj": group,
            "permissions_by_app": permissions_by_app,
            "assigned_permissions": assigned_permissions,
            "page_title": f"Manage Permissions: {group.name}",
        }
        return render(request, "accounts/groups/manage_permissions.html", context)

    @method_decorator(permission_required("auth.change_permission", raise_exception=True))
    def update_permissions(self, request, pk):
        """Update group permissions"""
        group = get_object_or_404(Group, pk=pk)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        try:
            # Get selected permission IDs from form
            selected_permissions = request.POST.getlist("permissions")

            # Convert to integers and filter valid permissions
            permission_ids = []
            for perm_id in selected_permissions:
                try:
                    permission_ids.append(int(perm_id))
                except ValueError:
                    continue

            # Update group permissions
            permissions = Permission.objects.filter(id__in=permission_ids)
            group.permissions.set(permissions)

            success_message = (
                f"Permissions for group '{group.name}' updated successfully!"
            )

            if is_ajax:
                return JsonResponse(
                    {
                        "success": True,
                        "message": success_message,
                        "redirect_url": request.build_absolute_uri(
                            reverse("accounts:groups")
                        ),
                    }
                )
            else:
                messages.success(request, success_message)
                return redirect("accounts:groups")

        except Exception as e:
            error_message = f"Error updating permissions: {str(e)}"
            logger.error(f"Error updating permissions: {e}")

            if is_ajax:
                return JsonResponse(
                    {"success": False, "error": error_message}, status=500
                )
            else:
                messages.error(request, error_message)
                return redirect("accounts:manage-permissions", pk=pk)
