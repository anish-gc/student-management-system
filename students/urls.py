from django.urls import path

from students.views.course_views import CourseView
from students.views.enrollment_views import CheckEnrollmentView, EnrollmentView
from students.views.instructor_views import InstructorView
from students.views.metadata_views import MetaDataView
from students.views.student_views import StudentView

app_name = "students"

urlpatterns = [
    # ==================== METADATA URLS ====================
    path("metadata/", MetaDataView.as_view(), name="metadata"),
    path("metadata/add/", MetaDataView.as_view(), name="metadata-add"),
    path("metadata/<int:pk>/edit/", MetaDataView.as_view(), name="metadata-edit"),
    path("metadata/<int:pk>/delete/", MetaDataView.as_view(), name="metadata-delete"),
    
    # ==================== STUDENT URLS ====================
    path("students/", StudentView.as_view(), name="students"),
    path("students/add/", StudentView.as_view(), name="student-add"),
    path("students/<int:pk>/edit/", StudentView.as_view(), name="student-edit"),
    path("students/<int:pk>/delete/", StudentView.as_view(), name="student-delete"),
    
    # ==================== INSTRUCTOR URLS ====================
    path("instructors/", InstructorView.as_view(), name="instructors"),
    path("instructors/add/", InstructorView.as_view(), name="instructor-add"),
    path("instructors/<int:pk>/edit/", InstructorView.as_view(), name="instructor-edit"),
    path("instructors/<int:pk>/delete/", InstructorView.as_view(), name="instructor-delete"),
    
    # ==================== COURSE URLS ====================
    path("courses/", CourseView.as_view(), name="courses"),
    path("courses/add/", CourseView.as_view(), name="course-add"),
    path("courses/<int:pk>/edit/", CourseView.as_view(), name="course-edit"),
    path("courses/<int:pk>/delete/", CourseView.as_view(), name="course-delete"),
    
    # ==================== ENROLLMENT URLS ====================
    path("enrollments/", EnrollmentView.as_view(), name="enrollments"),
    path("enrollments/add/", EnrollmentView.as_view(), name="enrollment-add"),
    path("enrollments/<int:pk>/edit/", EnrollmentView.as_view(), name="enrollment-edit"),
    path("enrollments/<int:pk>/delete/", EnrollmentView.as_view(), name="enrollment-delete"),
    
    # ==================== CHECK ENROLLMENT URL ====================
    path("check-enrollment/", CheckEnrollmentView.as_view(), name="check-enrollment"),
]