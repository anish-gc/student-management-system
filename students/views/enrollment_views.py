import logging
from django.http import JsonResponse
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count

from students.forms.enrollment_form import EnrollmentForm
from students.models.enrollment_model import Enrollment
from students.models.student_model import Student
from students.models.course_model import Course
from students.models.metadata_model import MetaData
from utilities.pagination_mixin import PaginatedListMixin
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

# Configure logger
logger = logging.getLogger(__name__)


class EnrollmentView(LoginRequiredMixin, PaginatedListMixin, View):
    """Enrollment view for listing, adding, editing, and deleting enrollments"""

    login_url = "/login/"
    redirect_field_name = "next"
    paginate_by = 15  # Override default pagination

    def get(self, request, pk=None):
        """Handle GET requests based on URL name"""
        if request.resolver_match.url_name == "enrollment-add":
            return self.add_enrollment(request)
        elif request.resolver_match.url_name == "enrollment-edit" and pk:
            return self.edit_enrollment(request, pk)
        elif request.resolver_match.url_name == "enrollment-delete" and pk:
            return self.delete_enrollment(request, pk)

        else:
            return self.enrollment_list(request)

    def post(self, request, pk=None):
        """Handle POST requests based on URL name"""
        if request.resolver_match.url_name == "enrollment-add":
            return self.add_enrollment_submit(request)
        elif request.resolver_match.url_name == "enrollment-edit" and pk:
            return self.edit_enrollment_submit(request, pk)
        elif request.resolver_match.url_name == "enrollment-delete" and pk:
            return self.delete(request, pk)
        return redirect("students:enrollments")

    def delete(self, request, pk=None):
        """Handle DELETE requests for enrollment deletion"""
        if pk:
            return self.delete_enrollment(request, pk)
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

    def get_queryset(self):
        """Get base queryset for enrollments"""
        return Enrollment.objects.select_related("student", "course").prefetch_related(
            "metadata"
        )

    def get_filtered_queryset(self, request):
        """Apply filters to the queryset"""
        queryset = self.get_queryset()

        # Student filter
        student_filter = request.GET.get("student")
        if student_filter:
            queryset = queryset.filter(student__id=student_filter)

        # Course filter
        course_filter = request.GET.get("course")
        if course_filter:
            queryset = queryset.filter(course__id=course_filter)

        # Grade filter
        grade_filter = request.GET.get("grade")
        if grade_filter:
            queryset = queryset.filter(grade=grade_filter)

        # Status filter (active/inactive)
        status_filter = request.GET.get("active_status")
        if status_filter:
            is_active = status_filter.lower() == "true"
            queryset = queryset.filter(is_active=is_active)

        # Completion status filter
        completion_filter = request.GET.get("completion_status")
        if completion_filter == "completed":
            queryset = queryset.filter(completion_date__isnull=False)
        elif completion_filter == "in_progress":
            queryset = queryset.filter(completion_date__isnull=True, is_active=True)

        # Metadata filter
        metadata_filter = request.GET.get("metadata")
        if metadata_filter:
            queryset = queryset.filter(metadata__key=metadata_filter)

        # Search filter
        search_query = request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(student__first_name__icontains=search_query)
                | Q(student__last_name__icontains=search_query)
                | Q(course__name__icontains=search_query)
                | Q(course__course_code__icontains=search_query)
                | Q(grade__icontains=search_query)
            )

        return queryset.distinct().order_by("-created_at")

    @method_decorator(
        permission_required("students.view_enrollment", raise_exception=True)
    )
    def enrollment_list(self, request):
        """Display paginated list of enrollments"""
        # Get filtered queryset
        filtered_queryset = self.get_filtered_queryset(request)

        # Get pagination context
        pagination_context = self.get_pagination_context(request, filtered_queryset)

        # Additional context
        student_list = Student.objects.filter(is_active=True).order_by(
            "first_name", "last_name"
        )
        course_list = Course.objects.filter(is_active=True).order_by("name")
        metadata_list = MetaData.objects.all()

        # Grade choices for filter
        grade_choices = Enrollment.GRADE_CHOICES

        # Get some statistics
        stats = {
            "total_enrollments": filtered_queryset.count(),
            "active_enrollments": filtered_queryset.filter(is_active=True).count(),
            "completed_enrollments": filtered_queryset.filter(
                completion_date__isnull=False
            ).count(),
            "in_progress_enrollments": filtered_queryset.filter(
                completion_date__isnull=True, is_active=True
            ).count(),
        }

        context = {
            **pagination_context,
            "student_list": student_list,
            "course_list": course_list,
            "metadata_list": metadata_list,
            "grade_choices": grade_choices,
            "stats": stats,
            "current_filters": {
                "student": request.GET.get("student", ""),
                "course": request.GET.get("course", ""),
                "grade": request.GET.get("grade", ""),
                "active_status": request.GET.get("active_status", ""),
                "completion_status": request.GET.get("completion_status", ""),
                "metadata": request.GET.get("metadata", ""),
                "search": request.GET.get("search", ""),
            },
        }

        return render(request, "students/enrollments/enrollments_list.html", context)

    @method_decorator(
        permission_required("students.add_enrollment", raise_exception=True)
    )
    def add_enrollment(self, request):
        """Display add enrollment form"""
        form = EnrollmentForm()
        student_list = Student.objects.filter(is_active=True).order_by(
            "first_name", "last_name"
        )
        metadata_list = MetaData.objects.all()

        context = {
            "form": form,
            "student_list": student_list,
            "metadata_list": metadata_list,
            "is_adding": True,
            "page_title": "Add Enrollment",
        }
        return render(request, "students/enrollments/enrollments_form.html", context)

    @method_decorator(
        permission_required("students.add_enrollment", raise_exception=True)
    )
    def add_enrollment_submit(self, request):
        """Process add enrollment form submission"""
        form = EnrollmentForm(request.POST)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            try:
                # Create the enrollment
                enrollment = form.save(commit=False)
                enrollment.save()

                # Add metadata if selected
                metadata = form.cleaned_data.get("metadata")
                if metadata:
                    enrollment.metadata.set(metadata)

                success_message = f"Enrollment for {enrollment.student.full_name} in {enrollment.course.name} added successfully!"

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect_url": request.build_absolute_uri(
                                reverse("students:enrollments")
                            ),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("students:enrollments")

            except Exception as e:
                error_message = f"Error adding enrollment: {str(e)}"
                logger.error(f"Error adding enrollment: {e}")

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
            student_list = Student.objects.filter(is_active=True).order_by(
                "first_name", "last_name"
            )
            course_list = Course.objects.filter(is_active=True).order_by("name")
            metadata_list = MetaData.objects.all()
            context = {
                "form": form,
                "student_list": student_list,
                "course_list": course_list,
                "metadata_list": metadata_list,
                "is_adding": True,
                "page_title": "Add Enrollment",
            }
            return render(
                request, "students/enrollments/enrollments_form.html", context
            )

    @method_decorator(
        permission_required("students.change_enrollment", raise_exception=True)
    )
    def edit_enrollment(self, request, pk):
        """Display edit enrollment form"""
        enrollment = get_object_or_404(Enrollment, pk=pk)

        form = EnrollmentForm(instance=enrollment)
        student_list = Student.objects.filter(is_active=True).order_by(
            "first_name", "last_name"
        )
        course_list = Course.objects.filter(is_active=True).order_by("name")
        metadata_list = MetaData.objects.all()

        context = {
            "form": form,
            "student_list": student_list,
            "course_list": course_list,
            "metadata_list": metadata_list,
            "enrollment_obj": enrollment,
            "is_editing": True,
            "page_title": f"Edit Enrollment: {enrollment.student.full_name} - {enrollment.course.course_code}",
        }
        return render(request, "students/enrollments/enrollments_form.html", context)

    @method_decorator(
        permission_required("students.change_enrollment", raise_exception=True)
    )
    def edit_enrollment_submit(self, request, pk):
        """Process edit enrollment form submission"""
        enrollment = get_object_or_404(Enrollment, pk=pk)
        form = EnrollmentForm(request.POST, instance=enrollment)

        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            try:
                enrollment = form.save(commit=False)
                enrollment.save()
                form.save_m2m()  # This saves the many-to-many relationships

                success_message = f"Enrollment for {enrollment.student.full_name} in {enrollment.course.name} updated successfully!"

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect_url": request.build_absolute_uri(
                                reverse("students:enrollments")
                            ),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("students:enrollments")

            except Exception as e:
                error_message = f"Error updating enrollment: {str(e)}"
                logger.error(f"Error updating enrollment: {e}")

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
            student_list = Student.objects.filter(is_active=True).order_by(
                "first_name", "last_name"
            )
            course_list = Course.objects.filter(is_active=True).order_by("name")
            metadata_list = MetaData.objects.all()
            context = {
                "form": form,
                "student_list": student_list,
                "course_list": course_list,
                "metadata_list": metadata_list,
                "enrollment_obj": enrollment,
                "is_editing": True,
                "page_title": f"Edit Enrollment: {enrollment.student.full_name} - {enrollment.course.course_code}",
            }
            return render(
                request, "students/enrollments/enrollments_form.html", context
            )

    @method_decorator(
        permission_required("students.delete_enrollment", raise_exception=True)
    )
    def delete_enrollment(self, request, pk):
        """Delete an enrollment"""
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        try:
            enrollment = get_object_or_404(Enrollment, pk=pk)
            enrollment_info = (
                f"{enrollment.student.full_name} - {enrollment.course.name}"
            )
            enrollment.delete()
            success_message = f"Enrollment {enrollment_info} deleted successfully!"

            if is_ajax:
                return JsonResponse(
                    {
                        "success": True,
                        "message": success_message,
                        "redirect": reverse("students:enrollments"),
                    }
                )
            else:
                messages.success(request, success_message)
                return redirect("students:enrollments")

        except Exception as e:
            error_message = f"Error deleting enrollment: {str(e)}"
            logger.error(f"Error deleting enrollment: {e}")

            if is_ajax:
                return JsonResponse(
                    {"success": False, "error": error_message}, status=500
                )
            else:
                messages.error(request, error_message)
                return redirect("students:enrollments")


from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from students.models.enrollment_model import Enrollment


class CheckEnrollmentView(LoginRequiredMixin, View):
    """View to check for duplicate enrollments"""

    login_url = "/login/"
    redirect_field_name = "next"

    def get(self, request):
        """Check if a student is already enrolled in a course"""
        student_id = request.GET.get("student")
        course_id = request.GET.get("course")
        exclude_id = request.GET.get(
            "exclude"
        )  # For edit mode, exclude current enrollment

        if not student_id or not course_id:
            return JsonResponse(
                {
                    "exists": False,
                    "error": "Student and course parameters are required",
                },
                status=400,
            )

        try:
            # Check for existing enrollment
            queryset = Enrollment.objects.filter(
                student_id=student_id,
                course_id=course_id,
                is_active=True,  # Only check active enrollments
            )

            # Exclude current enrollment if in edit mode
            if exclude_id:
                queryset = queryset.exclude(id=exclude_id)

            exists = queryset.exists()

            # If enrollment exists, get details for the warning message
            enrollment_details = None
            if exists:
                enrollment = queryset.first()
                enrollment_details = {
                    "student_name": enrollment.student.full_name,
                    "course_name": enrollment.course.name,
                    "status": "Active" if enrollment.is_active else "Inactive",
                }

            return JsonResponse(
                {"exists": exists, "enrollment_details": enrollment_details}
            )

        except ValueError:
            return JsonResponse(
                {"exists": False, "error": "Invalid student or course ID"}, status=400
            )
        except Exception as e:
            logger.error(f"Error checking enrollment: {e}")
            return JsonResponse(
                {
                    "exists": False,
                    "error": "An error occurred while checking enrollment",
                },
                status=500,
            )
