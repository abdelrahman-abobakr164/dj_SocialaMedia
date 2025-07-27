from django import forms
from .models import *


class PostForm(forms.ModelForm):
    body = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "h100 bor-0 w-100 rounded-xxl p-2 ps-5 font-xssss text-grey-500 fw-500 border-light-md theme-dark-bg",
                "placeholder": "What's on your mind?",
                "cols": "30",
                "rows": "10",
            }
        ),
    )

    class Meta:
        model = Post
        fields = ["body"]


class CommentForm(forms.ModelForm):
    comment = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Post a Comment...",
            }
        ),
    )
    parent = forms.HiddenInput()

    class Meta:
        model = Comment
        fields = ["comment", "parent"]
