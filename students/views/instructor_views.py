import logging
from django.http import JsonResponse
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q

from students.forms.instructor_form import InstructorForm
from students.models.metadata_model import MetaData
from students.models.instructor_model import Instructor
from students.models.course_model import Course
from utilities.pagination_mixin import PaginatedListMixin
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

# Configure logger
logger = logging.getLogger(__name__)


class InstructorView(LoginRequiredMixin, PaginatedListMixin, View):
    """Instructor view for listing, adding, editing, and deleting instructors"""

    login_url = "/login/"
    redirect_field_name = "next"
    paginate_by = 15  # Override default pagination

    def get(self, request, pk=None):
        """Handle GET requests based on URL name"""
        if request.resolver_match.url_name == "instructor-add":
            return self.add_instructor(request)
        elif request.resolver_match.url_name == "instructor-edit" and pk:
            return self.edit_instructor(request, pk)
        elif request.resolver_match.url_name == "instructor-delete" and pk:
            return self.delete_instructor(request, pk)

        else:
            return self.instructor_list(request)

    def post(self, request, pk=None):
        """Handle POST requests based on URL name"""
        if request.resolver_match.url_name == "instructor-add":
            return self.add_instructor_submit(request)
        elif request.resolver_match.url_name == "instructor-edit" and pk:
            return self.edit_instructor_submit(request, pk)
        elif request.resolver_match.url_name == "instructor-delete" and pk:
            return self.delete(request, pk)
        return redirect("students:instructors")

    def delete(self, request, pk=None):
        """Handle DELETE requests for instructor deletion"""
        if pk:
            return self.delete_instructor(request, pk)
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

    def get_queryset(self):
        """Get base queryset for instructors"""
        return Instructor.objects.all()

    def get_filtered_queryset(self, request):
        """Apply filters to the queryset"""
        queryset = self.get_queryset()

        # Metadata filter
        metadata_filter = request.GET.get("metadata")
        if metadata_filter:
            queryset = queryset.filter(metadata__key=metadata_filter)

        # Status filter (active/inactive)
        status_filter = request.GET.get("active_status")
        if status_filter:
            is_active = status_filter.lower() == "true"
            queryset = queryset.filter(is_active=is_active)

        # Course filter
        course_filter = request.GET.get("course")
        if course_filter:
            queryset = queryset.filter(courses__id=course_filter)

        # Search filter
        search_query = request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
                | Q(email__icontains=search_query)
            )

        return queryset.distinct().order_by("-created_at")

    @method_decorator(
        permission_required("students.view_instructor", raise_exception=True)
    )
    def instructor_list(self, request):
        """Display paginated list of instructors"""
        # Get filtered queryset
        filtered_queryset = self.get_filtered_queryset(request)

        # Get pagination context
        pagination_context = self.get_pagination_context(request, filtered_queryset)

        # Additional context
        metadata_list = MetaData.objects.all()
        course_list = Course.objects.all()

        context = {
            **pagination_context,
            "metadata_list": metadata_list,
            "course_list": course_list,
            "current_filters": {
                "metadata": request.GET.get("metadata", ""),
                "active_status": request.GET.get("active_status", ""),
                "course": request.GET.get("course", ""),
                "search": request.GET.get("search", ""),
            },
        }

        return render(request, "students/instructors/instructors_list.html", context)

    @method_decorator(
        permission_required("students.add_instructor", raise_exception=True)
    )
    def add_instructor(self, request):
        """Display add instructor form"""
        form = InstructorForm()
        metadata_list = MetaData.objects.all()
        course_list = Course.objects.all()

        context = {
            "form": form,
            "metadata_list": metadata_list,
            "course_list": course_list,
            "is_adding": True,
            "page_title": "Add Instructor",
        }
        return render(request, "students/instructors/instructors_form.html", context)

    @method_decorator(
        permission_required("students.add_instructor", raise_exception=True)
    )
    def add_instructor_submit(self, request):
        """Process add instructor form submission"""
        form = InstructorForm(request.POST)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            try:
                # Create the instructor
                instructor = form.save(commit=False)
                instructor.is_active = True
                instructor.save()

                # Add metadata if selected
                metadata = form.cleaned_data.get("metadata")
                if metadata:
                    instructor.metadata.set(metadata)

                # Add courses if selected
                courses = form.cleaned_data.get("courses")
                if courses:
                    instructor.courses.set(courses)

                success_message = (
                    f"Instructor {instructor.full_name} added successfully!"
                )

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect_url": request.build_absolute_uri(
                                reverse("students:instructors")
                            ),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("students:instructors")

            except Exception as e:
                error_message = f"Error adding instructor: {str(e)}"
                logger.error(f"Error adding instructor: {e}")

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
            metadata_list = MetaData.objects.all()
            course_list = Course.objects.all()
            context = {
                "form": form,
                "metadata_list": metadata_list,
                "course_list": course_list,
                "is_adding": True,
                "page_title": "Add Instructor",
            }
            return render(
                request, "students/instructors/instructors_form.html", context
            )

    @method_decorator(
        permission_required("students.change_instructor", raise_exception=True)
    )
    def edit_instructor(self, request, pk):
        """Display edit instructor form"""
        instructor = get_object_or_404(Instructor, pk=pk)

        form = InstructorForm(instance=instructor)
        metadata_list = MetaData.objects.all()
        course_list = Course.objects.all()

        context = {
            "form": form,
            "metadata_list": metadata_list,
            "course_list": course_list,
            "instructor_obj": instructor,
            "is_editing": True,
            "page_title": f"Edit Instructor: {instructor.full_name}",
        }
        return render(request, "students/instructors/instructors_form.html", context)

    @method_decorator(
        permission_required("students.change_instructor", raise_exception=True)
    )
    def edit_instructor_submit(self, request, pk):
        """Process edit instructor form submission"""
        instructor = get_object_or_404(Instructor, pk=pk)
        form = InstructorForm(request.POST, instance=instructor)

        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            try:
                instructor = form.save(commit=False)
                instructor.save()
                form.save_m2m()  # This saves the many-to-many relationships

                success_message = (
                    f"Instructor {instructor.full_name} updated successfully!"
                )

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect_url": request.build_absolute_uri(
                                reverse("students:instructors")
                            ),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("students:instructors")

            except Exception as e:
                error_message = f"Error updating instructor: {str(e)}"
                logger.error(f"Error updating instructor: {e}")

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
            metadata_list = MetaData.objects.all()
            course_list = Course.objects.all()
            context = {
                "form": form,
                "metadata_list": metadata_list,
                "course_list": course_list,
                "instructor_obj": instructor,
                "is_editing": True,
                "page_title": f"Edit Instructor: {instructor.full_name}",
            }
            return render(
                request, "students/instructors/instructors_form.html", context
            )

    @method_decorator(
        permission_required("students.delete_instructor", raise_exception=True)
    )
    def delete_instructor(self, request, pk):
        """Delete an instructor"""
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        try:
            instructor = get_object_or_404(Instructor, pk=pk)
            instructor_name = instructor.full_name
            instructor.delete()
            success_message = f"Instructor {instructor_name} deleted successfully!"

            if is_ajax:
                return JsonResponse(
                    {
                        "success": True,
                        "message": success_message,
                        "redirect": reverse("students:instructors"),
                    }
                )
            else:
                messages.success(request, success_message)
                return redirect("students:instructors")

        except Exception as e:
            error_message = f"Error deleting instructor: {str(e)}"
            logger.error(f"Error deleting instructor: {e}")

            if is_ajax:
                return JsonResponse(
                    {"success": False, "error": error_message}, status=500
                )
            else:
                messages.error(request, error_message)
                return redirect("students:instructors")
