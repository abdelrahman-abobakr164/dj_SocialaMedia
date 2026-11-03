from django import forms
from django.core.exceptions import ValidationError
from core.validations import file_validation
from .models import Conversation


class CreateForm(forms.ModelForm):
    MIN_OTHER_MEMBERS = 2

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
        fields = ["group_name", "group_image", "admin", "participants"]
        widgets = {
            "admin": forms.CheckboxSelectMultiple,
            "participants": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, candidates, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("admin", "participants"):
            field = self.fields[name]
            field.queryset = candidates
            field.label_from_instance = lambda user: user.username
        self.fields["admin"].required = False

    def clean_group_image(self):
        image = self.cleaned_data.get("group_image")
        if image and "group_image" in self.changed_data:
            file_validation(image)
        return image

    def clean_participants(self):
        participants = self.cleaned_data["participants"]
        if participants.count() < self.MIN_OTHER_MEMBERS:
            raise ValidationError(
                f"Select at least {self.MIN_OTHER_MEMBERS} other members "
                "(a group needs 3 including you)."
            )
        return participants

    def clean(self):
        cleaned = super().clean()
        admins = cleaned.get("admin")
        participants = cleaned.get("participants")
        if admins is not None and participants is not None:
            if admins.exclude(pk__in=participants).exists():
                self.add_error("admin", "Every admin must also be a selected member.")
        return cleaned
