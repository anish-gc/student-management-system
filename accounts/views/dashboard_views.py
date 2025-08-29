import logging
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
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

        # Get recent activities (you can customize this based on your needs)

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
        completed_enrollments = Enrollment.objects.filter(
            completion_date__isnull=False
        ).count()

        # Staff/Instructor statistics (assuming User model has is_staff or similar field)
        total_staff = User.objects.filter(is_staff=True).count()
        active_staff = User.objects.filter(is_staff=True, is_active=True).count()

        # Calculate completion rate
        completion_rate = 0
        if total_enrollments > 0:
            completion_rate = round((completed_enrollments / total_enrollments) * 100)

        # Recent student registrations
        one_week_ago = timezone.now() - timedelta(days=7)
        one_month_ago = timezone.now() - timedelta(days=30)

        new_students_week = Student.objects.filter(created_at__gte=one_week_ago).count()
        new_students_month = Student.objects.filter(
            created_at__gte=one_month_ago
        ).count()

        # Average grade
        # average_grade_result =
        # average_grade = average_grade_result['avg_grade']
        average_grade = None
        return {
            "total_students": total_students,
            "active_students": active_students,
            "total_courses": total_courses,
            "active_courses": active_courses,
            "total_enrollments": total_enrollments,
            "active_enrollments": active_enrollments,
            "completed_enrollments": completed_enrollments,
            "total_staff": total_staff,
            "active_staff": active_staff,
            "completion_rate": completion_rate,
            "new_students_week": new_students_week,
            "new_students_month": new_students_month,
            "average_grade": round(average_grade, 2) if average_grade else "N/A",
        }
