from django import forms

from students.models.metadata_model import MetaData


class MetaDataForm(forms.ModelForm):
    class Meta:
        model = MetaData
        fields = ["key", "value", "is_active"]
        widgets = {
            "key": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter metadata key"}
            ),
            "value": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Enter metadata value",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {"key": "Key", "value": "Value", "is_active": "Active"}
        help_texts = {
            "key": "Unique identifier for the metadata",
            "value": "The actual metadata content",
            "is_active": "Whether this metadata is active",
        }

    def clean_key(self):
        key = self.cleaned_data.get("key")
        if (
            MetaData.objects.filter(key=key)
            .exclude(pk=self.instance.pk if self.instance else None)
            .exists()
        ):
            raise forms.ValidationError(
                "A metadata entry with this key already exists."
            )
        return key
