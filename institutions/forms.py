from django import forms
from django.utils.translation import gettext_lazy as _

from accounts.models import User

from .models import Institution


class InstitutionForm(forms.ModelForm):

    class Meta:
        model = Institution

        fields = [
            "name",
            "short_name",
            "logo",
            "address",
            "phone_number",
            "email",
            "is_active",
            "users",
        ]

        widgets = {
            "address": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),
        }

        labels = {
            "name": _("Institution Name"),
            "short_name": _("Short Name"),
            "logo": _("Logo"),
            "address": _("Address"),
            "phone_number": _("Phone Number"),
            "email": _("Email"),
            "is_active": _("Active"),
            "users": _("Administrators"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        self.fields["is_active"].widget.attrs["class"] = "form-check-input"

        self.fields["logo"].widget.attrs["class"] = "form-control"

        self.fields["address"].widget.attrs["rows"] = 4

        self.fields["users"].queryset = User.objects.filter(
            role__in=(
                User.Role.MANAGER,
                User.Role.ASSISTANT_MANAGER,
            ),
        )

        self.fields["users"].help_text = _(
            "Assign the managers who will manage this institution's data."
        )

    def clean(self):
        cleaned_data = super().clean()
        users = cleaned_data.get("users")

        if users:
            other_institutions = Institution.objects.exclude(pk=self.instance.pk)
            for user in users:
                if other_institutions.filter(users=user).exists():
                    self.add_error(
                        "users",
                        _(
                            "%(name)s is already assigned to another "
                            "institution. Each manager can manage only one "
                            "institution."
                        )
                        % {"name": user.get_full_name() or user.username},
                    )

        return cleaned_data