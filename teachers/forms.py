from django import forms
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from institutions.models import Institution

from .models import Teacher


class TeacherForm(forms.ModelForm):

    class Meta:
        model = Teacher

        fields = [
            "user",
            "institution",
            "employee_code",
            "specialization",
            "phone_number",
            "hire_date",
        ]

        labels = {
            "user": _("User"),
            "institution": _("Institution"),
            "employee_code": _("Employee Code"),
            "specialization": _("Specialization"),
            "phone_number": _("Phone Number"),
            "hire_date": _("Hire Date"),
        }

    def __init__(self, *args, **kwargs):

        institution = kwargs.pop("institution", None)

        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        self.fields["user"].queryset = User.objects.filter(
            role=User.Role.TEACHER,
        )

        if institution:

            self.fields["institution"].queryset = (
                Institution.objects.filter(pk=institution.pk)
            )

        else:

            self.fields["institution"].queryset = (
                Institution.objects.none()
            )

        self.fields["institution"].widget = forms.HiddenInput()

        if not self.is_bound and institution:

            self.fields["institution"].initial = institution