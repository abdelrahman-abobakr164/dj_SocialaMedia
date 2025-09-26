from django import forms
from django.contrib.auth import get_user_model
from .models import Contact

User = get_user_model()


class UserForm(forms.ModelForm):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username...",
            }
        ),
    )
    bio = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Bio...",
            }
        ),
    )
    email = forms.EmailField(
        required=False,
        disabled=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email Address...",
            }
        ),
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "City...",
            }
        ),
    )
    place = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Location...",
            }
        ),
    )

    class Meta:
        model = User
        fields = [
            "username",
            "bio",
            "city",
            "email",
            "place",
            "img",
            "cover",
            "about_me",
            "show_events",
            "is_private",
            "show_followers",
            "show_following",
            "check_followers",
        ]


class ContactForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "style2-input ps-5 form-control text-grey-900 font-xsss fw-600",
                "placeholder": "Your Email Address...",
            }
        ),
    )
    class Meta:
        model = Contact
        fields = ["email", "message"]
