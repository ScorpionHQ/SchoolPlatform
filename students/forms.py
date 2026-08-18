from django import forms
from django.utils.translation import gettext_lazy as _

from classes.models import ClassRoom
from institutions.models import Institution

from .models import Student


GENDER_CHOICES = (
    ("", _("Not specified")),
    (Student.Gender.MALE, _("Male")),
    (Student.Gender.FEMALE, _("Female")),
)


class StudentCreationForm(forms.Form):

    first_name = forms.CharField(max_length=150)

    last_name = forms.CharField(max_length=150)

    username = forms.CharField(max_length=150)

    student_code = forms.CharField(max_length=30)

    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=False,
        label=_("Gender"),
    )

    password = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False,
        label=_("Password (optional)"),
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False,
        label=_("Confirm Password"),
    )

    institution = forms.ModelChoiceField(
        queryset=Institution.objects.all(),
    )

    classroom = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all(),
        required=False,
    )

    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
            }
        ),
    )

    parent_phone = forms.CharField(
        required=False,
    )

    def __init__(self, *args, **kwargs):

        self.is_update = kwargs.pop("is_update", False)

        institution = kwargs.pop("institution", None)

        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        self._restrict_to_institution(institution)

        if self.is_update:
            self.fields["password"].required = False
            self.fields["confirm_password"].required = False

    def _restrict_to_institution(self, institution):

        if institution:

            self.fields["institution"].queryset = (
                Institution.objects.filter(pk=institution.pk)
            )

            self.fields["classroom"].queryset = (
                ClassRoom.objects.filter(institution=institution)
            )

        else:

            self.fields["institution"].queryset = (
                Institution.objects.none()
            )

            self.fields["classroom"].queryset = (
                ClassRoom.objects.none()
            )

        self.fields["institution"].widget = forms.HiddenInput()

        if not self.is_bound and institution:

            self.fields["institution"].initial = institution

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if password != confirm:
            raise forms.ValidationError(
                _("Passwords do not match.")
            )

        return cleaned_data


class StudentsImportForm(forms.Form):

    excel_file = forms.FileField(
        label=_("Excel File"),
        widget=forms.ClearableFileInput(
            attrs={
                "accept": ".xlsx,.xls",
                "class": "form-control",
            }
        ),
    )

    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=False,
        label=_("Default Gender"),
        help_text=_(
            "Applied to all rows that do not have a gender column."
        ),
    )

    institution = forms.ModelChoiceField(
        queryset=Institution.objects.filter(
            is_active=True,
        ),
        label=_("Institution"),
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    classroom = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all(),
        required=False,
        label=_("Default Class (optional)"),
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    def __init__(self, *args, **kwargs):

        institution = kwargs.pop("institution", None)

        super().__init__(*args, **kwargs)

        if institution:

            self.fields["institution"].queryset = (
                Institution.objects.filter(pk=institution.pk)
            )

            self.fields["classroom"].queryset = (
                ClassRoom.objects.filter(institution=institution)
            )

        else:

            self.fields["institution"].queryset = (
                Institution.objects.none()
            )

            self.fields["classroom"].queryset = (
                ClassRoom.objects.none()
            )

        self.fields["institution"].widget = forms.HiddenInput()

        if not self.is_bound and institution:

            self.fields["institution"].initial = institution

    def clean_excel_file(self):

        excel_file = self.cleaned_data.get(
            "excel_file",
        )

        if excel_file:

            file_name = excel_file.name.lower()

            if not (
                file_name.endswith(".xlsx")
                or file_name.endswith(".xls")
            ):

                raise forms.ValidationError(
                    _("Only Excel files (.xlsx or .xls) are allowed.")
                )

        return excel_file