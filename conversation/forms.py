from django import forms
from django.contrib.auth import get_user_model


class CreateForm(forms.Form):
    group_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter group name"}
        ),
    )

