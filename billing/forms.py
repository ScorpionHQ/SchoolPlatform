from django import forms
from django.utils.translation import gettext_lazy as _

from classes.models import ClassRoom

from .models import FeeType, Payment


class FeeTypeForm(forms.ModelForm):

    class Meta:

        model = FeeType

        fields = [
            "name",
            "amount",
            "is_required",
            "is_active",
            "sort_order",
        ]

        labels = {
            "name": _("Fee name"),
            "amount": _("Amount (IQD)"),
            "is_required": _("Required"),
            "is_active": _("Active"),
            "sort_order": _("Sort order"),
        }

    def __init__(self, *args, **kwargs):

        institution = kwargs.pop("institution", None)

        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        self.fields["is_required"].widget.attrs["class"] = "form-check-input"
        self.fields["is_active"].widget.attrs["class"] = "form-check-input"

        self.fields["sort_order"].required = False

        if institution:
            self.instance.institution = institution

    def clean_amount(self):

        amount = self.cleaned_data["amount"]

        if amount is None or amount <= 0:
            raise forms.ValidationError(
                _("Amount must be greater than zero.")
            )

        return amount


class ChargeClassForm(forms.Form):

    classroom = forms.ModelChoiceField(
        queryset=ClassRoom.objects.none(),
        label=_("Class"),
    )

    fee_type = forms.ModelChoiceField(
        queryset=FeeType.objects.none(),
        label=_("Fee type"),
    )

    academic_year = forms.CharField(
        max_length=20,
        required=False,
        label=_("Academic year"),
    )

    def __init__(self, *args, **kwargs):

        institution = kwargs.pop("institution", None)

        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        if institution:
            self.fields["classroom"].queryset = (
                ClassRoom.objects.filter(institution=institution)
            )
            self.fields["fee_type"].queryset = (
                FeeType.objects.filter(
                    institution=institution,
                    is_active=True,
                )
            )


class PaymentForm(forms.Form):

    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label=_("Amount (IQD)"),
    )

    method = forms.ChoiceField(
        choices=Payment.Method.choices,
        label=_("Method"),
    )

    note = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 2,
            }
        ),
        label=_("Note"),
    )

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["amount"].widget.attrs["class"] = "form-control"
        self.fields["method"].widget.attrs["class"] = "form-select"
        self.fields["note"].widget.attrs["class"] = "form-control"
