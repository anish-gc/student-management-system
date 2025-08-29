# students/forms/instructor_form.py
from django import forms
from django.core.exceptions import ValidationError
import re

from students.models.metadata_model import MetaData
from students.models.instructor_model import Instructor
from students.models.course_model import Course


class InstructorForm(forms.ModelForm):
    metadata = forms.ModelMultipleChoiceField(
        queryset=MetaData.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2bs4'}),
        required=False,
        help_text="Select applicable metadata for this instructor."
    )
    
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2bs4'}),
        required=False,
        help_text="Select courses this instructor will teach."
    )

    class Meta:
        model = Instructor
        fields = ['first_name', 'last_name', 'email', 'courses', 'metadata']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
           
        }
        help_texts = {
            'email': 'This will be used for instructor communications.',
            'phone_number': 'Enter instructor\'s contact phone number.',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if not self.instance.pk:  # Adding new instructor
                if Instructor.objects.filter(email=email).exists():
                    raise ValidationError('An instructor with that email already exists.')
            else:  # Editing existing instructor
                if Instructor.objects.filter(email=email).exclude(id=self.instance.id).exists():
                    raise ValidationError('An instructor with that email already exists.')
        return email

  

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
        instructor = super().save(commit=False)
        if commit:
            instructor.save()
            self.save_m2m()  # Save many-to-many data (metadata and courses)
        return instructor