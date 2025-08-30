# students/forms.py
from django import forms
from django.core.exceptions import ValidationError
import re
from datetime import date

from students.models.metadata_model import MetaData
from students.models.student_model import Student


class StudentForm(forms.ModelForm):
    metadata = forms.ModelMultipleChoiceField(
        queryset=MetaData.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2bs4'}),
        required=False,
        help_text="Select applicable metadata for this student."
    )

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'date_of_birth',  'metadata']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'max': date.today().isoformat()  # Prevent future dates
            }),
          
        }
        help_texts = {
            'email': 'This will be used for student communications.',
            'date_of_birth': 'Student\'s date of birth',
        }



    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if not self.instance.pk:  # Adding new student
                if Student.objects.filter(email=email).exists():
                    raise ValidationError('A student with that email already exists.')
            else:  # Editing existing student
                if Student.objects.filter(email=email).exclude(id=self.instance.id).exists():
                    raise ValidationError('A student with that email already exists.')
        return email

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get('date_of_birth')
        if date_of_birth:
            if date_of_birth > date.today():
                raise ValidationError('Date of birth cannot be in the future.')
            
            age = (date.today() - date_of_birth).days / 365.25
            if age > 100:
                raise ValidationError('Please enter a valid date of birth.')
        return date_of_birth

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            first_name = first_name.strip().title()
            if not re.match(r'^[a-zA-Z\s\'-]+$', first_name):
                raise ValidationError('First name can only contain letters, spaces, hyphens, and apostrophes.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            last_name = last_name.strip().title()
            if not re.match(r'^[a-zA-Z\s\'-]+$', last_name):
                raise ValidationError('Last name can only contain letters, spaces, hyphens, and apostrophes.')
        return last_name

    def save(self, commit=True):
        student = super().save(commit=False)
        if commit:
            student.save()
            self.save_m2m()  # Save many-to-many data (metadata)
        return student