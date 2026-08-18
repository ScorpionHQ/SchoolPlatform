from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path(
        "",
        views.charges,
        name="charges",
    ),
    path(
        "fees/",
        views.fee_type_list,
        name="fees",
    ),
    path(
        "fees/<int:pk>/toggle/",
        views.fee_type_toggle,
        name="fee_toggle",
    ),
    path(
        "fees/<int:pk>/delete/",
        views.fee_type_delete,
        name="fee_delete",
    ),
    path(
        "fees/prices/pdf/",
        views.fee_prices_pdf,
        name="prices_pdf",
    ),
    path(
        "charge-class/",
        views.charge_class,
        name="charge_class",
    ),
    path(
        "fees/<int:pk>/delete-charge/",
        views.student_fee_delete,
        name="student_fee_delete",
    ),
    path(
        "pay/",
        views.payment_create,
        name="payment_create",
    ),
    path(
        "pay/<int:pk>/delete/",
        views.payment_delete,
        name="payment_delete",
    ),
    path(
        "balances/",
        views.balances,
        name="balances",
    ),
    path(
        "my-fees/",
        views.my_fees,
        name="my_fees",
    ),
    path(
        "receipt/<int:pk>/",
        views.receipt,
        name="receipt",
    ),
]
