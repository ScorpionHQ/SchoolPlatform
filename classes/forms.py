from django import forms
from django.utils.translation import gettext_lazy as _

from institutions.models import Institution

from .models import ClassRoom


class ClassRoomForm(forms.ModelForm):

    class Meta:

        model = ClassRoom

        fields = [
            "institution",
            "stage",
            "name",
            "level",
            "academic_year",
        ]

        labels = {
            "institution": _("Institution"),
            "stage": _("Educational Stage"),
            "name": _("Class Name"),
            "level": _("Level"),
            "academic_year": _("Academic Year"),
        }

    def __init__(self, *args, **kwargs):

        institution = kwargs.pop("institution", None)

        super().__init__(*args, **kwargs)

        self.fields["stage"].widget = forms.Select(
            choices=ClassRoom.Stage.choices,
        )

        for field in self.fields.values():

            field.widget.attrs["class"] = "form-control"

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