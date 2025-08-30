import logging
from django.http import JsonResponse
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q

from students.forms.course_form import CourseForm
from students.models.metadata_model import MetaData
from students.models.course_model import Course
from utilities.pagination_mixin import PaginatedListMixin
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

# Configure logger
logger = logging.getLogger(__name__)


class CourseView(LoginRequiredMixin, PaginatedListMixin, View):
    """Course view for listing, adding, editing, and deleting courses"""

    login_url = "/login/"
    redirect_field_name = "next"
    paginate_by = 15  # Override default pagination

    def get(self, request, pk=None):
        """Handle GET requests based on URL name"""
        if request.resolver_match.url_name == "course-add":
            return self.add_course(request)
        elif request.resolver_match.url_name == "course-edit" and pk:
            return self.edit_course(request, pk)
        elif request.resolver_match.url_name == "course-delete" and pk:
            return self.delete_course(request, pk)

        else:
            return self.course_list(request)

    def post(self, request, pk=None):
        """Handle POST requests based on URL name"""
        if request.resolver_match.url_name == "course-add":
            return self.add_course_submit(request)
        elif request.resolver_match.url_name == "course-edit" and pk:
            return self.edit_course_submit(request, pk)
        elif request.resolver_match.url_name == "course-delete" and pk:
            return self.delete(request, pk)
        return redirect("students:courses")

    def delete(self, request, pk=None):
        """Handle DELETE requests for course deletion"""
        if pk:
            return self.delete_course(request, pk)
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

    def get_queryset(self):
        """Get base queryset for courses"""
        return Course.objects.all()

    def get_filtered_queryset(self, request):
        """Apply filters to the queryset"""
        queryset = self.get_queryset()

        # Metadata filter
        metadata_filter = request.GET.get("metadata")
        if metadata_filter:
            queryset = queryset.filter(metadata__key=metadata_filter)

        # Search filter
        search_query = request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(course_code__icontains=search_query)
                | Q(description__icontains=search_query)
            )

        return queryset.distinct().order_by("course_code")

    @method_decorator(permission_required("students.view_course", raise_exception=True))
    def course_list(self, request):
        """Display paginated list of courses"""
        # Get filtered queryset
        filtered_queryset = self.get_filtered_queryset(request)

        # Get pagination context
        pagination_context = self.get_pagination_context(request, filtered_queryset)

        # Additional context
        metadata_list = MetaData.objects.all()

        context = {
            **pagination_context,
            "metadata_list": metadata_list,
            "current_filters": {
                "metadata": request.GET.get("metadata", ""),
                "search": request.GET.get("search", ""),
            },
        }

        return render(request, "students/courses/courses_list.html", context)

    @method_decorator(permission_required("students.add_course", raise_exception=True))
    def add_course(self, request):
        """Display add course form"""
        form = CourseForm()
        metadata_list = MetaData.objects.all()

        context = {
            "form": form,
            "metadata_list": metadata_list,
            "is_adding": True,
            "page_title": "Add Course",
        }
        return render(request, "students/courses/courses_form.html", context)

    @method_decorator(permission_required("students.add_course", raise_exception=True))
    def add_course_submit(self, request):
        """Process add course form submission"""
        form = CourseForm(request.POST)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            try:
                # Create the course
                course = form.save(commit=False)
                course.save()

                # Add metadata if selected
                metadata = form.cleaned_data.get("metadata")
                if metadata:
                    course.metadata.set(metadata)

                success_message = (
                    f"Course {course.course_code} - {course.name} added successfully!"
                )

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect_url": request.build_absolute_uri(
                                reverse("students:courses")
                            ),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("students:courses")

            except Exception as e:
                error_message = f"Error adding course: {str(e)}"
                logger.error(f"Error adding course: {e}")

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
            context = {
                "form": form,
                "metadata_list": metadata_list,
                "is_adding": True,
                "page_title": "Add Course",
            }
            return render(request, "students/courses/courses_form.html", context)

    @method_decorator(
        permission_required("students.change_course", raise_exception=True)
    )
    def edit_course(self, request, pk):
        """Display edit course form"""
        course = get_object_or_404(Course, pk=pk)

        form = CourseForm(instance=course)
        metadata_list = MetaData.objects.all()

        context = {
            "form": form,
            "metadata_list": metadata_list,
            "course_obj": course,
            "is_editing": True,
            "page_title": f"Edit Course: {course.name}",
        }
        return render(request, "students/courses/courses_form.html", context)

    @method_decorator(
        permission_required("students.change_course", raise_exception=True)
    )
    def edit_course_submit(self, request, pk):
        """Process edit course form submission"""
        course = get_object_or_404(Course, pk=pk)
        form = CourseForm(request.POST, instance=course)

        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            try:
                course = form.save(commit=False)
                course.save()
                form.save_m2m()  # This saves the many-to-many relationships

                success_message = (
                    f"Course {course.course_code} - {course.name} updated successfully!"
                )

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect_url": request.build_absolute_uri(
                                reverse("students:courses")
                            ),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("students:courses")

            except Exception as e:
                error_message = f"Error updating course: {str(e)}"
                logger.error(f"Error updating course: {e}")

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
            context = {
                "form": form,
                "metadata_list": metadata_list,
                "course_obj": course,
                "is_editing": True,
                "page_title": f"Edit Course: {course.name}",
            }
            return render(request, "students/courses/courses_form.html", context)

    @method_decorator(
        permission_required("students.delete_course", raise_exception=True)
    )
    def delete_course(self, request, pk):
        """Delete a course"""
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        try:
            course = get_object_or_404(Course, pk=pk)
            course_name = f"{course.course_code} - {course.name}"
            course.delete()
            success_message = f"Course {course_name} deleted successfully!"

            if is_ajax:
                return JsonResponse(
                    {
                        "success": True,
                        "message": success_message,
                        "redirect": reverse("students:courses"),
                    }
                )
            else:
                messages.success(request, success_message)
                return redirect("students:courses")

        except Exception as e:
            error_message = f"Error deleting course: {str(e)}"
            logger.error(f"Error deleting course: {e}")

            if is_ajax:
                return JsonResponse(
                    {"success": False, "error": error_message}, status=500
                )
            else:
                messages.error(request, error_message)
                return redirect("students:courses")
