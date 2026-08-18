from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from classes.models import ClassRoom
from institutions.models import Institution
from students.models import Student
from subjects.models import Subject
from teachers.models import Teacher

from .models import Attendance


class AttendanceForm(forms.ModelForm):

    class Meta:

        model = Attendance

        fields = [
            "student",
            "teacher",
            "subject",
            "classroom",
            "date",
            "status",
            "note",
        ]

        labels = {
            "student": _("Student"),
            "teacher": _("Teacher"),
            "subject": _("Subject"),
            "classroom": _("Class"),
            "date": _("Date"),
            "status": _("Status"),
            "note": _("Note"),
        }

        widgets = {
            "date": forms.DateInput(
                attrs={"type": "date"},
            ),
        }

    def __init__(self, *args, **kwargs):

        institution = kwargs.pop("institution", None)

        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            field.widget.attrs["class"] = "form-control"

        if institution:

            self.fields["student"].queryset = (
                Student.objects.filter(institution=institution)
            )

            self.fields["teacher"].queryset = (
                Teacher.objects.filter(institution=institution)
            )

            self.fields["subject"].queryset = (
                Subject.objects.filter(institution=institution)
            )

            self.fields["classroom"].queryset = (
                ClassRoom.objects.filter(institution=institution)
            )

        else:

            self.fields["student"].queryset = (
                Student.objects.none()
            )

            self.fields["teacher"].queryset = (
                Teacher.objects.none()
            )

            self.fields["subject"].queryset = (
                Subject.objects.none()
            )

            self.fields["classroom"].queryset = (
                ClassRoom.objects.none()
            )

        self.fields["date"].initial = timezone.localdate()


class AttendanceSessionForm(forms.Form):

    classroom = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all(),
        label=_("Class"),
    )

    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        label=_("Subject"),
    )

    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.all(),
        label=_("Teacher"),
    )

    date = forms.DateField(
        label=_("Date"),
        initial=timezone.localdate,
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    def __init__(self, *args, **kwargs):

        user = kwargs.pop("user", None)

        institution = kwargs.pop("institution", None)

        super().__init__(*args, **kwargs)

        if user and user.role == "teacher":

            teacher = Teacher.objects.filter(
                user=user,
            ).first()

            if teacher:

                self.fields["teacher"].initial = teacher

                self.fields["teacher"].queryset = (
                    Teacher.objects.filter(pk=teacher.pk)
                )

                self.fields["subject"].queryset = Subject.objects.filter(
                    teacher=teacher,
                ).select_related(
                    "classroom",
                )

                classroom_ids = list(
                    Subject.objects.filter(
                        teacher=teacher,
                    ).exclude(
                        classroom__isnull=True,
                    ).values_list(
                        "classroom_id",
                        flat=True,
                    ).distinct()
                )

                self.fields["classroom"].queryset = ClassRoom.objects.filter(
                    id__in=classroom_ids,
                )

        elif institution:

            self.fields["classroom"].queryset = (
                ClassRoom.objects.filter(institution=institution)
            )

            self.fields["subject"].queryset = (
                Subject.objects.filter(institution=institution)
            )

            self.fields["teacher"].queryset = (
                Teacher.objects.filter(institution=institution)
            )

        else:

            self.fields["classroom"].queryset = (
                ClassRoom.objects.none()
            )

            self.fields["subject"].queryset = (
                Subject.objects.none()
            )

            self.fields["teacher"].queryset = (
                Teacher.objects.none()
            )

        for field in self.fields.values():

            field.widget.attrs["class"] = "form-control"

    def clean(self):

        cleaned_data = super().clean()

        classroom = cleaned_data.get("classroom")
        subject = cleaned_data.get("subject")

        if (
            classroom
            and subject
            and subject.classroom
            and subject.classroom != classroom
        ):

            raise forms.ValidationError(
                _(
                    "The selected subject does not belong to "
                    "the selected class."
                )
            )

        return cleaned_data
