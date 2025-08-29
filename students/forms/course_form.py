# students/forms/course_form.py
from django import forms
from django.core.exceptions import ValidationError
import re

from students.models.metadata_model import MetaData
from students.models.course_model import Course


class CourseForm(forms.ModelForm):
    metadata = forms.ModelMultipleChoiceField(
        queryset=MetaData.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2bs4'}),
        required=False,
        help_text="Select applicable metadata for this course."
    )

    class Meta:
        model = Course
        fields = ['name', 'course_code', 'description', 'metadata']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'course_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., CS101, MATH1001'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter course description...'
            }),
        }
        help_texts = {
            'name': 'Full name of the course.',
            'course_code': 'Course code must be in format CS101 or MATH1001 (2-4 letters followed by 3-4 digits).',
            'description': 'Detailed description of the course content and objectives.',
        }

    def clean_course_code(self):
        course_code = self.cleaned_data.get('course_code')
        if course_code:
            course_code = course_code.strip().upper()
            
            # Check format with regex
            if not re.match(r'^[A-Z]{2,4}\d{3,4}$', course_code):
                raise ValidationError('Course code must be in format CS101 or MATH1001 (2-4 letters followed by 3-4 digits).')
            
            # Check uniqueness
            if not self.instance.pk:  # Adding new course
                if Course.objects.filter(course_code=course_code).exists():
                    raise ValidationError('A course with this course code already exists.')
            else:  # Editing existing course
                if Course.objects.filter(course_code=course_code).exclude(id=self.instance.id).exists():
                    raise ValidationError('A course with this course code already exists.')
        
        return course_code

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 3:
                raise ValidationError('Course name must be at least 3 characters long.')
            if len(name) > 200:
                raise ValidationError('Course name cannot exceed 200 characters.')
        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description:
            description = description.strip()
        return description

    def save(self, commit=True):
        course = super().save(commit=False)
        if commit:
            course.save()
            self.save_m2m()  # Save many-to-many data (metadata)
        return course