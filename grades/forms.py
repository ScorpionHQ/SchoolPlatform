from django import forms
from django.utils.translation import gettext_lazy as _

from institutions.models import Institution
from students.models import Student
from subjects.models import Subject
from teachers.models import Teacher

from .models import Grade


class GradeForm(forms.ModelForm):

    class Meta:

        model = Grade

        fields = [
            "student",
            "subject",
            "teacher",
            "exam_name",
            "score",
            "max_score",
            "exam_date",
            "note",
        ]

        labels = {
            "student": _("Student"),
            "subject": _("Subject"),
            "teacher": _("Teacher"),
            "exam_name": _("Exam"),
            "score": _("Score"),
            "max_score": _("Maximum Score"),
            "exam_date": _("Exam Date"),
            "note": _("Note"),
        }

        widgets = {
            "exam_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "note": forms.Textarea(
                attrs={
                    "rows": 3,
                }
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

            self.fields["subject"].queryset = (
                Subject.objects.filter(institution=institution)
            )

            self.fields["teacher"].queryset = (
                Teacher.objects.filter(institution=institution)
            )

        else:

            self.fields["student"].queryset = (
                Student.objects.none()
            )

            self.fields["subject"].queryset = (
                Subject.objects.none()
            )

            self.fields["teacher"].queryset = (
                Teacher.objects.none()
            )

    def clean(self):

        cleaned_data = super().clean()

        score = cleaned_data.get("score")
        max_score = cleaned_data.get("max_score")

        if (
            score is not None
            and max_score is not None
        ):

            if score < 0:

                raise forms.ValidationError(
                    _("Score cannot be negative.")
                )

            if max_score <= 0:

                raise forms.ValidationError(
                    _("Maximum score must be greater than zero.")
                )

            if score > max_score:

                raise forms.ValidationError(
                    _("Score cannot be greater than maximum score.")
                )

        return cleaned_data