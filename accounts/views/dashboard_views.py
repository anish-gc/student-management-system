import logging
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from students.models import Student, Course, Enrollment
from django.contrib.auth.models import User
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

# Configure logger
logger = logging.getLogger(__name__)


class DashboardView(LoginRequiredMixin, View):
    """Dashboard view showing overview of the student management system"""

    @method_decorator(
        permission_required("accounts.view_dashboard", raise_exception=True)
    )
    def get(self, request):
        # Calculate statistics
        stats = self.get_system_stats()


        context = {
            "stats": stats,
        }
        return render(request, "dashboard.html", context)

    def get_system_stats(self):
        """Calculate and return system statistics"""
        # Student statistics
        total_students = Student.objects.count()
        active_students = Student.objects.filter(is_active=True).count()

        # Course statistics
        total_courses = Course.objects.count()
        active_courses = Course.objects.filter(is_active=True).count()

        # Enrollment statistics
        total_enrollments = Enrollment.objects.count()
        active_enrollments = Enrollment.objects.filter(is_active=True).count()
     

        # Staff/Instructor statistics (assuming User model has is_staff or similar field)
        total_staff = User.objects.filter(is_staff=True).count()
        active_staff = User.objects.filter(is_staff=True, is_active=True).count()

     
       
       
        return {
            "total_students": total_students,
            "active_students": active_students,
            "total_courses": total_courses,
            "active_courses": active_courses,
            "total_enrollments": total_enrollments,
            "active_enrollments": active_enrollments,
            "total_staff": total_staff,
            "active_staff": active_staff,
        }
