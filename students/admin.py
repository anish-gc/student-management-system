from django.contrib import admin
from .models import MetaData
from .models import Course
from .models import Instructor
from .models import Enrollment
from .models import Student


@admin.register(MetaData)
class MetaDataAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "key",
        "value_short",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
        "is_active",
    )
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("key", "value")

    def value_short(self, obj):
        return (obj.value[:75] + "...") if len(obj.value) > 75 else obj.value

    value_short.short_description = "Value"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "email",
        "date_of_birth",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
        "is_active",
    )
    list_filter = ("is_active", "created_at", "updated_at", "date_of_birth")
    search_fields = ("first_name", "last_name", "email")
    ordering = ("last_name", "first_name")
    filter_horizontal = ("metadata",)

    # Automatically set created_by and updated_by to the logged-in user
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
        "is_active",
    )
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("first_name", "last_name", "email", "phone_number")
    ordering = ("last_name", "first_name")
    filter_horizontal = ("courses", "metadata")

    # Auto set created_by and updated_by
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "course_code",
        "name",
        "description_short",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
        "is_active",
    )
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("course_code", "name", "description")
    ordering = ("course_code",)
    filter_horizontal = ("metadata",)

    # Show shorter description in list view
    def description_short(self, obj):
        return (
            (obj.description[:75] + "...")
            if len(obj.description) > 75
            else obj.description
        )

    description_short.short_description = "Description"

    # Auto set created_by and updated_by
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "course",
        "grade",
        "score",
        "completion_date",
        "grade_points",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
        "is_active",
    )
    list_filter = ("is_active", "grade", "completion_date", "created_at", "updated_at")
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__email",
        "course__course_code",
        "course__name",
    )
    ordering = ("-created_at",)
    filter_horizontal = ("metadata",)
    autocomplete_fields = ("student", "course")

    # Show grade points directly in list view
    def grade_points(self, obj):
        return obj.grade_points

    grade_points.short_description = "Grade Points"

    # Auto set created_by and updated_by
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
