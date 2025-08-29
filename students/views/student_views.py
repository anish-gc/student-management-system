import logging
from django.http import JsonResponse
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q

from students.forms.student_form import StudentForm
from students.models.metadata_model import MetaData
from students.models.student_model import Student
from utilities.pagination_mixin import PaginatedListMixin
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

# Configure logger
logger = logging.getLogger(__name__)


class StudentView(LoginRequiredMixin, PaginatedListMixin, View):
    """Student view for listing, adding, editing, and deleting students"""

    login_url = "/login/"
    redirect_field_name = "next"
    paginate_by = 15  # Override default pagination

    def get(self, request, pk=None):
        """Handle GET requests based on URL name"""
        if request.resolver_match.url_name == "student-add":
            return self.add_student(request)
        elif request.resolver_match.url_name == "student-edit" and pk:
            return self.edit_student(request, pk)
        elif request.resolver_match.url_name == "student-delete" and pk:
            return self.delete_student(request, pk)

        else:
            return self.student_list(request)

    def post(self, request, pk=None):
        """Handle POST requests based on URL name"""
        if request.resolver_match.url_name == "student-add":
            return self.add_student_submit(request)
        elif request.resolver_match.url_name == "student-edit" and pk:
            return self.edit_student_submit(request, pk)
        elif request.resolver_match.url_name == "student-delete" and pk:
            return self.delete(request, pk)
        return redirect("students:students")

    def delete(self, request, pk=None):
        """Handle DELETE requests for student deletion"""
        if pk:
            return self.delete_student(request, pk)
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

    def get_queryset(self):
        """Get base queryset for students"""
        return Student.objects.all()

    def get_filtered_queryset(self, request):
        """Apply filters to the queryset"""
        queryset = self.get_queryset()

        # Metadata filter
        metadata_filter = request.GET.get("metadata")
        if metadata_filter:
            queryset = queryset.filter(metadata__name=metadata_filter)

        # Status filter (active/inactive)
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
                | Q(email__icontains=search_query)
            )

        return queryset.distinct().order_by("-created_at")

    @method_decorator(
        permission_required("students.view_student", raise_exception=True)
    )
    def student_list(self, request):
        """Display paginated list of students"""
        # Get filtered queryset
        filtered_queryset = self.get_filtered_queryset(request)

        # Get pagination context
        pagination_context = self.get_pagination_context(request, filtered_queryset)

        # Additional context
        metadata_list = MetaData.objects.all()
        print(metadata_list)
        context = {
            **pagination_context,
            "metadata_list": metadata_list,
            "current_filters": {
                "metadata": request.GET.get("metadata", ""),
                "active_status": request.GET.get("active_status", ""),
                "search": request.GET.get("search", ""),
            },
        }

        return render(request, "students/students/students_list.html", context)

    @method_decorator(permission_required("students.add_student", raise_exception=True))
    def add_student(self, request):
        """Display add student form"""
        form = StudentForm()
        metadata_list = MetaData.objects.all()

        context = {
            "form": form,
            "metadata_list": metadata_list,
            "is_adding": True,
            "page_title": "Add Student",
        }
        return render(request, "students/students/students_form.html", context)

    @method_decorator(permission_required("students.add_student", raise_exception=True))
    def add_student_submit(self, request):
        """Process add student form submission"""
        form = StudentForm(request.POST)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            try:
                # Create the student
                student = form.save(commit=False)
                student.is_active = True
                student.save()

                # Add metadata if selected
                metadata = form.cleaned_data.get("metadata")
                if metadata:
                    student.metadata.set(metadata)

                success_message = f"Student {student.full_name} added successfully!"

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect_url": request.build_absolute_uri(
                                reverse("students:students")
                            ),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("students:students")

            except Exception as e:
                error_message = f"Error adding student: {str(e)}"
                logger.error(f"Error adding student: {e}")

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
                "page_title": "Add Student",
            }
            return render(request, "students/students/students_form.html", context)

    @method_decorator(
        permission_required("students.change_student", raise_exception=True)
    )
    def edit_student(self, request, pk):
        """Display edit student form"""
        student = get_object_or_404(Student, pk=pk)

        form = StudentForm(instance=student)
        metadata_list = MetaData.objects.all()

        context = {
            "form": form,
            "metadata_list": metadata_list,
            "student_obj": student,
            "is_editing": True,
            "page_title": f"Edit Student: {student.full_name}",
        }
        return render(request, "students/students/students_form.html", context)

    @method_decorator(
        permission_required("students.change_student", raise_exception=True)
    )
    def edit_student_submit(self, request, pk):
        """Process edit student form submission"""
        student = get_object_or_404(Student, pk=pk)
        form = StudentForm(request.POST, instance=student)

        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            try:
                student = form.save(commit=False)
                student.save()
                form.save_m2m()  # This saves the many-to-many relationships

                success_message = f"Student {student.full_name} updated successfully!"

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect_url": request.build_absolute_uri(
                                reverse("students:students")
                            ),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("students:students")

            except Exception as e:
                error_message = f"Error updating student: {str(e)}"
                logger.error(f"Error updating student: {e}")

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
                "student_obj": student,
                "is_editing": True,
                "page_title": f"Edit Student: {student.full_name}",
            }
            return render(request, "students/students/students_form.html", context)

    @method_decorator(
        permission_required("students.delete_student", raise_exception=True)
    )
    def delete_student(self, request, pk):
        """Delete a student"""
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        try:
            student = get_object_or_404(Student, pk=pk)
            student_name = student.full_name
            student.delete()
            success_message = f"Student {student_name} deleted successfully!"

            if is_ajax:
                return JsonResponse(
                    {
                        "success": True,
                        "message": success_message,
                        "redirect": reverse("students:students"),
                    }
                )
            else:
                messages.success(request, success_message)
                return redirect("students:students")

        except Exception as e:
            error_message = f"Error deleting student: {str(e)}"
            logger.error(f"Error deleting student: {e}")

            if is_ajax:
                return JsonResponse(
                    {"success": False, "error": error_message}, status=500
                )
            else:
                messages.error(request, error_message)
                return redirect("students:students")
