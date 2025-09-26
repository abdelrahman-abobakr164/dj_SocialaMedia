from django import forms
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
