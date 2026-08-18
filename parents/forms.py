from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from students.models import Student
from .models import Parent


class ParentForm(forms.Form):

    first_name = forms.CharField(max_length=150)

    last_name = forms.CharField(max_length=150)

    username = forms.CharField(max_length=150)

    password = forms.CharField(
        widget=forms.PasswordInput(
            render_value=True,
        ),
        required=False,
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            render_value=True,
        ),
        required=False,
    )

    relationship = forms.CharField(
        max_length=50,
        required=False,
    )

    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):

        self.is_update = kwargs.pop(
            "is_update",
            False,
        )

        institution = kwargs.pop("institution", None)

        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():

            if field_name != "students":

                field.widget.attrs["class"] = "form-control"

        if institution:

            self.fields["students"].queryset = (
                Student.objects.filter(institution=institution)
            )

        else:

            self.fields["students"].queryset = (
                Student.objects.none()
            )

        if self.is_update:

            self.fields["password"].required = False
            self.fields["confirm_password"].required = False

    def clean_username(self):

        username = self.cleaned_data.get(
            "username",
        )

        if username:

            queryset = User.objects.filter(
                username=username,
            )

            if self.is_update:

                parent_id = self.initial.get(
                    "parent_id",
                )

                if parent_id:

                    queryset = queryset.exclude(
                        parent_profile__id=parent_id,
                    )

            if queryset.exists():

                raise ValidationError(
                    _("Username already exists.")
                )

        return username

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if self.is_update:

            if password or confirm:

                if password != confirm:
                    raise forms.ValidationError(
                        _("Passwords do not match.")
                    )

        else:

            if password != confirm:
                raise forms.ValidationError(
                    _("Passwords do not match.")
                )

        return cleaned_data
