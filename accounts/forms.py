from django import forms
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _


class PasswordChangeForm(forms.Form):

    current_password = forms.CharField(
        label=_("Current Password"),
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
            }
        ),
    )

    new_password = forms.CharField(
        label=_("New Password"),
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
            }
        ),
    )

    confirm_password = forms.CharField(
        label=_("Confirm New Password"),
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
            }
        ),
    )

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean_current_password(self):

        current_password = self.cleaned_data.get(
            "current_password",
        )

        if self.user and not self.user.check_password(current_password):

            raise forms.ValidationError(
                _("Your current password is incorrect."),
            )

        return current_password

    def clean_new_password(self):

        new_password = self.cleaned_data.get(
            "new_password",
        )

        if self.user:

            validate_password(
                new_password,
                user=self.user,
            )

        return new_password

    def clean(self):

        cleaned_data = super().clean()

        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if (
            new_password
            and confirm_password
            and new_password != confirm_password
        ):

            raise forms.ValidationError(
                _("The two password fields did not match."),
            )

        return cleaned_data
