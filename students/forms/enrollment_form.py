from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal

from students.models.enrollment_model import Enrollment
from students.models.student_model import Student
from students.models.course_model import Course
from students.models.metadata_model import MetaData


class EnrollmentForm(forms.ModelForm):
    metadata = forms.ModelMultipleChoiceField(
        queryset=MetaData.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2bs4'}),
        required=False,
        help_text="Select applicable metadata for this enrollment."
    )

    class Meta:
        model = Enrollment
        fields = ['student', 'course', 'grade', 'score', 'completion_date', 'is_active', 'metadata']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control select2bs4'}),
            'course': forms.Select(attrs={'class': 'form-control select2bs4'}),
            'grade': forms.Select(attrs={'class': 'form-control'}),
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
            'completion_date': forms.DateInput(attrs={
                'class': 'form-control datepicker',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'student': 'Select the student for this enrollment.',
            'course': 'Select the course for this enrollment.',
            'grade': 'Select the final grade (optional).',
            'score': 'Enter numerical score between 0-100 (optional).',
            'completion_date': 'Date when the course was completed (optional).',
            'is_active': 'Check if this enrollment is currently active.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values
        if not self.instance.pk:  # New enrollment
            self.fields['is_active'].initial = True
        self.fields['course'].queryset = Course.objects.filter(is_active=True)
        self.fields['student'].queryset = Student.objects.filter(is_active=True)
        # Make student and course required
        self.fields['student'].required = True
        self.fields['course'].required = True

    def clean_student(self):
        student = self.cleaned_data.get('student')
        if not student:
            raise ValidationError('Please select a student.')
        return student

    def clean_course(self):
        course = self.cleaned_data.get('course')
        if not course:
            raise ValidationError('Please select a course.')
        return course

    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score is not None:
            if score < 0 or score > 100:
                raise ValidationError('Score must be between 0 and 100.')
            # Convert to Decimal for consistency
            score = Decimal(str(score))
        return score

    def clean_grade(self):
        grade = self.cleaned_data.get('grade')
        score = self.cleaned_data.get('score')
        
        # If score is provided, suggest appropriate grade
        if score is not None and not grade:
            if score >= 97:
                self.cleaned_data['grade'] = 'A+'
            elif score >= 93:
                self.cleaned_data['grade'] = 'A'
            elif score >= 90:
                self.cleaned_data['grade'] = 'A-'
            elif score >= 87:
                self.cleaned_data['grade'] = 'B+'
            elif score >= 83:
                self.cleaned_data['grade'] = 'B'
            elif score >= 80:
                self.cleaned_data['grade'] = 'B-'
            elif score >= 77:
                self.cleaned_data['grade'] = 'C+'
            elif score >= 73:
                self.cleaned_data['grade'] = 'C'
            elif score >= 70:
                self.cleaned_data['grade'] = 'C-'
            elif score >= 67:
                self.cleaned_data['grade'] = 'D+'
            elif score >= 60:
                self.cleaned_data['grade'] = 'D'
            else:
                self.cleaned_data['grade'] = 'F'
        
        return grade

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        course = cleaned_data.get('course')
        completion_date = cleaned_data.get('completion_date')
        grade = cleaned_data.get('grade')

        # Check for duplicate enrollment
        if student and course:
            existing_enrollment = Enrollment.objects.filter(
                student=student, 
                course=course
            )
            
            if self.instance.pk:
                existing_enrollment = existing_enrollment.exclude(pk=self.instance.pk)
            
            if existing_enrollment.exists():
                raise ValidationError({
                    'student': 'This student is already enrolled in this course.',
                    'course': 'This student is already enrolled in this course.'
                })

        # If completion date is provided, enrollment should have a grade
        if completion_date and not grade:
            raise ValidationError({
                'grade': 'A grade is required when a completion date is provided.'
            })

        return cleaned_data

    def save(self, commit=True):
        enrollment = super().save(commit=False)
        if commit:
            enrollment.save()
            self.save_m2m()  # Save many-to-many data (metadata)
        return enrollment