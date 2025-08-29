from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group, Permission
import re


class GroupForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all().select_related('content_type'),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2bs4'}),
        required=False,
        help_text="Select permissions for this group."
    )

    class Meta:
        model = Group
        fields = ['name', 'permissions']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter group name...'
            }),
        }
        help_texts = {
            'name': 'Enter a unique name for this group.',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            
            # Check for valid characters (letters, numbers, spaces, hyphens, underscores)
            if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
                raise ValidationError('Group name can only contain letters, numbers, spaces, hyphens, and underscores.')
            
            # Check for uniqueness
            if not self.instance.pk:  # Adding new group
                if Group.objects.filter(name__iexact=name).exists():
                    raise ValidationError('A group with that name already exists.')
            else:  # Editing existing group
                if Group.objects.filter(name__iexact=name).exclude(id=self.instance.id).exists():
                    raise ValidationError('A group with that name already exists.')
                    
            # Ensure name is not too short
            if len(name) < 2:
                raise ValidationError('Group name must be at least 2 characters long.')
                
        return name

    def save(self, commit=True):
        group = super().save(commit=False)
        if commit:
            group.save()
            self.save_m2m()  # Save many-to-many data (permissions)
        return group