from django import forms
from django.forms import widgets
from .models import Contact


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
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(
            attrs={
                "class": "style2-input ps-5 form-control text-grey-900 font-xsss fw-600",
            }
        ),
    )

    class Meta:
        model = Contact
        fields = ["email", "message"]
