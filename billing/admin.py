from django.contrib import admin

from .models import FeeType, Payment, StudentFee


@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "institution", "amount", "is_required", "is_active"]
    list_filter = ["institution", "is_active"]
    search_fields = ["name"]


@admin.register(StudentFee)
class StudentFeeAdmin(admin.ModelAdmin):
    list_display = ["student", "fee_type", "academic_year", "amount", "paid_amount"]
    list_filter = ["institution"]
    search_fields = ["student__student_code"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["student", "amount", "method", "created_by", "created_at"]
    list_filter = ["institution", "method"]
