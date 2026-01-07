from django.contrib import admin
from .models import (
    UserProfile,
    State,
    District,
    ParentCompany,
    Vendor,
    B2CCustomer,
    B2BPartner,
)


# ------------------ User Profile ------------------


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "accepted_terms", "accepted_at")
    search_fields = ("user__username",)
    list_filter = ("accepted_terms",)


# ------------------ State ------------------


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "created_at")
    search_fields = ("name",)
    list_filter = ("status",)
    ordering = ("id",)
    readonly_fields = ("created_at",)


# ------------------ District ------------------


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "state", "status", "created_at")
    search_fields = ("name", "code", "state__name")
    list_filter = ("status", "state")
    ordering = ("id",)
    readonly_fields = ("created_at",)


# ------------------ Parent Company ------------------


@admin.register(ParentCompany)
class ParentCompanyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "phone_number",
        "email",
        "state",
        "district",
        "gst_number",
        "pan_number",
        "created_at",
    )
    search_fields = ("name", "phone_number", "email", "gst_number", "pan_number")
    list_filter = ("state", "district", "created_at")
    ordering = ("-id",)
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Company Details", {"fields": ("name", "phone_number", "email", "address")}),
        ("Location", {"fields": ("state", "district")}),
        (
            "Bank Details",
            {
                "fields": (
                    "bank_name",
                    "account_holder_name",
                    "account_number",
                    "ifsc_code",
                )
            },
        ),
        ("GST Details", {"fields": ("gst_number", "gst_document")}),
        ("TAN Details", {"fields": ("tan_number", "tan_document")}),
        ("PAN Details", {"fields": ("pan_number", "pan_document")}),
        ("System Info", {"fields": ("created_at",)}),
    )


# ------------------ Vendor ------------------


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "phone_number",
        "email",
        "state",
        "district",
        "gst_number",
        "pan_number",
        "created_at",
    )
    search_fields = ("name", "phone_number", "email", "gst_number", "pan_number")
    list_filter = ("state", "district", "created_at")
    ordering = ("-id",)
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Vendor Details", {"fields": ("name", "phone_number", "email", "address")}),
        ("Location", {"fields": ("state", "district")}),
        (
            "Bank Details",
            {
                "fields": (
                    "bank_name",
                    "account_holder_name",
                    "account_number",
                    "ifsc_code",
                )
            },
        ),
        ("GST Details", {"fields": ("gst_number", "gst_document")}),
        ("TAN Details", {"fields": ("tan_number", "tan_document")}),
        ("PAN Details", {"fields": ("pan_number", "pan_document")}),
        ("System Info", {"fields": ("created_at",)}),
    )


# ------------------ B2C Customer ------------------


@admin.register(B2CCustomer)
class B2CCustomerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "phone_number",
        "email",
        "state",
        "district",
        "gst_number",
        "pan_number",
        "created_at",
    )
    search_fields = ("name", "phone_number", "email", "gst_number", "pan_number")
    list_filter = ("state", "district", "created_at")
    ordering = ("-id",)
    readonly_fields = ("created_at",)
    list_per_page = 25

    fieldsets = (
        ("Customer Details", {"fields": ("name", "phone_number", "email", "address")}),
        ("Location", {"fields": ("state", "district")}),
        (
            "Bank Details",
            {
                "fields": (
                    "bank_name",
                    "account_holder_name",
                    "account_number",
                    "ifsc_code",
                )
            },
        ),
        ("GST Details", {"fields": ("gst_number", "gst_document")}),
        ("TAN Details", {"fields": ("tan_number", "tan_document")}),
        ("PAN Details", {"fields": ("pan_number", "pan_document")}),
        ("System Info", {"fields": ("created_at",)}),
    )


# ------------------ B2B Partner ------------------


@admin.register(B2BPartner)
class B2BPartnerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "partner_name",
        "phone_number",
        "email",
        "state",
        "district",
        "gst_number",
        "pan_number",
        "created_at",
    )
    search_fields = (
        "partner_name",
        "phone_number",
        "email",
        "gst_number",
        "pan_number",
    )
    list_filter = ("state", "district", "created_at")
    ordering = ("-id",)
    readonly_fields = ("created_at",)

    fieldsets = (
        (
            "Partner Details",
            {"fields": ("partner_name", "phone_number", "email", "address")},
        ),
        ("Location", {"fields": ("state", "district")}),
        (
            "Bank Details",
            {
                "fields": (
                    "bank_name",
                    "account_holder_name",
                    "account_number",
                    "ifsc_code",
                )
            },
        ),
        ("GST Details", {"fields": ("gst_number", "gst_document")}),
        ("TAN Details", {"fields": ("tan_number", "tan_document")}),
        ("PAN Details", {"fields": ("pan_number", "pan_document")}),
        ("System Info", {"fields": ("created_at",)}),
    )
