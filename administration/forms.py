from django import forms
from django.utils.translation import gettext_lazy as _

from accounts.models import User


class UserAdminForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
            }
        ),
        required=False,
        label=_("Password"),
        help_text=_(
            "Leave empty to keep the current password when editing."
        ),
    )

    class Meta:
        model = User

        fields = [
            "username",
            "first_name",
            "last_name",
            "role",
            "gender",
            "phone_number",
            "is_active",
            "must_change_password",
        ]

        labels = {
            "username": _("Username"),
            "first_name": _("First Name"),
            "last_name": _("Last Name"),
            "role": _("Role"),
            "gender": _("Gender"),
            "phone_number": _("Phone Number"),
            "is_active": _("Active"),
            "must_change_password": _("Must change password on next login"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        for name in (
            "is_active",
            "must_change_password",
        ):
            self.fields[name].widget.attrs["class"] = "form-check-input"

        if not self.instance.pk:
            self.fields["password"].required = True

    def clean_username(self):

        username = self.cleaned_data["username"]

        queryset = User.objects.filter(
            username=username,
        )

        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if username and queryset.exists():
            raise forms.ValidationError(
                _("A user with this username already exists.")
            )

        return username

    def save(self, commit=True):

        user = super().save(commit=False)

        password = self.cleaned_data.get("password")

        if password:
            user.set_password(password)

        if commit:
            user.save()

        return user
