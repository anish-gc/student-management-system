from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
import re


class StaffForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        min_length=1,
        help_text="Password must be at least 8 characters long.",
        required=False,  
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="Confirm Password",
        required=False,  
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control select2bs4",
            }
        ),
        required=False,
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "groups"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }
        help_texts = {
            "username": "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
        }

    def __init__(self, *args, **kwargs):
        self.is_editing = kwargs.pop("is_editing", False)
        super().__init__(*args, **kwargs)

        # If it's a new user (not editing), make password fields required
        if not self.is_editing:
            self.fields["password"].required = True
            self.fields["confirm_password"].required = True

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if not self.instance or not self.instance.pk:
            if User.objects.filter(username=username).exists():
                raise ValidationError("A user with that username already exists.")
        else:
            if (
                User.objects.filter(username=username)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise ValidationError("A user with that username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not self.instance or not self.instance.pk:
            if User.objects.filter(email=email).exists():
                raise ValidationError("A user with that email already exists.")
        else:
            if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
                raise ValidationError("A user with that email already exists.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")

        # If editing and no password provided, that's OK
        if self.is_editing and not password:
            return password

        # If password is provided, validate it
        if password:

            if len(password) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            if not re.search(r'[A-Z]', password):
                raise ValidationError('Password must contain at least one uppercase letter.')
            if not re.search(r'[a-z]', password):
                raise ValidationError('Password must contain at least one lowercase letter.')
            if not re.search(r'[0-9]', password):
                raise ValidationError('Password must contain at least one digit.')

        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        # Only validate password matching if password is provided
        if password or confirm_password:
            if password != confirm_password:
                raise ValidationError({"confirm_password": "Passwords do not match."})

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Only set password if it's provided
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)

        if commit:
            user.save()
            self.save_m2m()  # Save many-to-many data (groups)
        return user
