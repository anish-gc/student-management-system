import logging
from django.http import JsonResponse
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.db.models import Q
from accounts.forms.staff_form import StaffForm
from utilities.pagination_mixin import PaginatedListMixin
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

# Configure logger
logger = logging.getLogger(__name__)


class StaffView(LoginRequiredMixin, PaginatedListMixin, View):
    """Staff view for listing, adding, editing, and deleting staff members"""

    login_url = "/login/"
    redirect_field_name = "next"
    paginate_by = 10  # Override default pagination

    def get(self, request, pk=None):
        """Handle GET requests based on URL name"""
        if request.resolver_match.url_name == "staff-add":
            return self.add_staff(request)
        elif request.resolver_match.url_name == "staff-edit" and pk:
            return self.edit_staff(request, pk)
        elif request.resolver_match.url_name == "staff-delete" and pk:
            return self.delete_staff(request, pk)
        elif pk:
            return self.staff_detail(request, pk)
        else:
            return self.staff_list(request)

    def post(self, request, pk=None):
        """Handle POST requests based on URL pattern"""
        if request.resolver_match.url_name == "staff-add":
            return self.add_staff_submit(request)
        elif request.resolver_match.url_name == "staff-edit" and pk:
            return self.edit_staff_submit(request, pk)
        elif request.resolver_match.url_name == "staff-delete" and pk:
            return self.delete(request, pk)
        return redirect("accounts:staffs")

    def delete(self, request, pk=None):
        """Handle DELETE requests for staff deletion"""
        if pk:
            return self.delete_staff(request, pk)

        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

    def get_queryset(self):
        """Get base queryset for staff members"""
        return User.objects.filter(is_staff=True)

    def get_filtered_queryset(self, request):
        """Apply filters to the queryset"""
        queryset = self.get_queryset()

        # Group filter
        group_filter = request.GET.get("group")
        if group_filter:
            queryset = queryset.filter(groups__name=group_filter)

        # Status filter
        status_filter = request.GET.get("active_status")
        if status_filter:
            is_active = status_filter.lower() == "true"
            queryset = queryset.filter(is_active=is_active)

        # Search filter
        search_query = request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
                | Q(username__icontains=search_query)
                | Q(email__icontains=search_query)
            )

        return queryset.distinct().order_by("-date_joined")

    @method_decorator(permission_required("auth.view_user", raise_exception=True))
    def staff_list(self, request):
        """Display paginated list of staff members"""
        # Get filtered queryset
        filtered_queryset = self.get_filtered_queryset(request)

        # Get pagination context
        pagination_context = self.get_pagination_context(request, filtered_queryset)

        # Additional context
        groups = Group.objects.all()

        context = {
            **pagination_context,
            "groups": groups,
            "current_filters": {
                "group": request.GET.get("group", ""),
                "active_status": request.GET.get("active_status", ""),
                "search": request.GET.get("search", ""),
            },
        }

        return render(request, "accounts/staffs/staff_list.html", context)

    @method_decorator(permission_required("auth.add_user", raise_exception=True))
    def add_staff(self, request):
        """Display add staff form"""
        form = StaffForm(is_editing=False)  # Pass is_editing=False for new staff
        groups = Group.objects.all()

        context = {
            "form": form,
            "groups": groups,
            "is_editing": False,
            "page_title": "Add Staff Member",
        }
        return render(request, "accounts/staffs/staff_form.html", context)

    @method_decorator(permission_required("auth.add_user", raise_exception=True))
    def add_staff_submit(self, request):
        """Process add staff form submission"""
        form = StaffForm(request.POST, is_editing=False)  # Pass is_editing=False
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            try:
                # Create the user
                user = form.save(commit=False)
                user.is_staff = True
                user.is_active = True
                # Password is already set in form.save()
                user.save()

                # Add groups if selected
                groups = form.cleaned_data.get("groups")
                if groups:
                    user.groups.set(groups)

                success_message = (
                    f"Staff member {user.get_full_name()} added successfully!"
                )

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect_url": request.build_absolute_uri(
                                reverse("accounts:staffs")
                            ),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("accounts:staffs")

            except Exception as e:
                error_message = f"Error adding staff member: {str(e)}"

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

        # If we reach here and it's not AJAX, render the form with errors
        if not is_ajax:
            groups = Group.objects.all()
            context = {
                "form": form,
                "groups": groups,
                "is_editing": False,
                "page_title": "Add Staff Member",
            }
            return render(request, "accounts/staffs/staff_form.html", context)

    @method_decorator(permission_required("auth.change_user", raise_exception=True))
    def edit_staff(self, request, pk):
        """Display edit staff form"""
        user = get_object_or_404(User, pk=pk, is_staff=True)

        form = StaffForm(instance=user, is_editing=True)  
       
        groups = Group.objects.all()

        context = {
            "form": form,
            "groups": groups,
            "is_editing": True,
            "staff_obj": user,
            "page_title": f"Edit Staff: {user.get_full_name()}",
        }
        return render(request, "accounts/staffs/staff_form.html", context)


    @method_decorator(permission_required("auth.change_user", raise_exception=True))
    def edit_staff_submit(self, request, pk):
        """Process edit staff form submission"""
        user = get_object_or_404(User, pk=pk, is_staff=True)
        form = StaffForm(request.POST, instance=user, is_editing=True)  
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            try:
                user = form.save(commit=False)
                
                user.save()
                form.save_m2m() 

                success_message = (
                    f"Staff member {user.get_full_name()} updated successfully!"
                )

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect_url": request.build_absolute_uri(
                                reverse("accounts:staffs")
                            ),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("accounts:staffs")

            except Exception as e:
                error_message = f"Error updating staff member: {str(e)}"

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

        # If we reach here and it's not AJAX, render the form with errors
        if not is_ajax:
            groups = Group.objects.all()
            context = {
                "form": form,
                "groups": groups,
                "staff_obj": user,  
                "is_editing": True,
                "page_title": f"Edit Staff: {user.get_full_name()}",
            }
            return render(request, "accounts/staffs/staff_form.html", context)

    @method_decorator(permission_required("auth.delete_user", raise_exception=True))
    def delete_staff(self, request, pk):
        """Delete a staff member"""
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        try:
            user = get_object_or_404(User, pk=pk, is_staff=True)
            # Prevent deletion of superuser or self
            if user.is_superuser:
                error_message = "Cannot delete superuser account."
            elif user == request.user:
                error_message = "You cannot delete your own account."
            else:
                user_name = user.get_full_name() or user.username
                user.delete()
                success_message = f"Staff member {user_name} deleted successfully!"

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect": reverse("accounts:staffs"),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("accounts:staffs")

            # Error case
            if is_ajax:
                return JsonResponse(
                    {"success": False, "message": error_message}, status=400
                )
            else:
                messages.error(request, error_message)
                return redirect("accounts:staffs")

        except Exception as e:
            error_message = f"Error deleting staff member: {str(e)}"

            if is_ajax:
                return JsonResponse(
                    {"success": False, "error": error_message}, status=500
                )
            else:
                messages.error(request, error_message)
                return redirect("accounts:staffs")
