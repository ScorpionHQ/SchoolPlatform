from django import forms
from django.utils.translation import gettext_lazy as _

from classes.models import ClassRoom
from institutions.models import Institution
from teachers.models import Teacher

from .models import Subject


class SubjectForm(forms.ModelForm):

    class Meta:

        model = Subject

        fields = [
            "institution",
            "classroom",
            "teacher",
            "name",
            "code",
            "description",
        ]

        labels = {
            "institution": _("Institution"),
            "classroom": _("Class"),
            "teacher": _("Teacher"),
            "name": _("Subject Name"),
            "code": _("Subject Code"),
            "description": _("Description"),
        }

    def __init__(self, *args, **kwargs):

        institution = kwargs.pop("institution", None)

        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        if institution:

            self.fields["institution"].queryset = (
                Institution.objects.filter(pk=institution.pk)
            )

            self.fields["classroom"].queryset = (
                ClassRoom.objects.filter(institution=institution)
            )

            self.fields["teacher"].queryset = (
                Teacher.objects.filter(institution=institution)
            )

        else:

            self.fields["institution"].queryset = (
                Institution.objects.none()
            )

            self.fields["classroom"].queryset = (
                ClassRoom.objects.none()
            )

            self.fields["teacher"].queryset = (
                Teacher.objects.none()
            )

        self.fields["institution"].widget = forms.HiddenInput()

        if not self.is_bound and institution:

            self.fields["institution"].initial = institution