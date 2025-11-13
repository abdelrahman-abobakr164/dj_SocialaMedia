from django import forms

from core.utils import file_validation
from .models import Conversation


class CreateForm(forms.ModelForm):
    group_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter group name"}
        ),
    )
    group_image = forms.ImageField(
        required=False, widget=forms.FileInput(attrs={"class": "custom-file-inpu"})
    )

    class Meta:
        model = Conversation
        fields = ["group_name", "group_image"]

    def clean(self):
        file_name = self.cleaned_data.get("group_image")
        if file_name:
            if not file_validation(file_name):
                raise forms.ValidationError("File Extension is Not Supported ")
            return file_name
