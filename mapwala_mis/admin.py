# mapwala_mis/admin.py

from django.contrib import admin, messages
from .models import *
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils.html import format_html
from django.forms.models import BaseInlineFormSet
from decimal import Decimal


# ------------------ User Profile ------------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "accepted_terms", "accepted_at")
    search_fields = ("user__username",)
    list_filter = ("accepted_terms",)
    ordering = ("user__username",)
    readonly_fields = ("accepted_at",)


from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.contrib import messages

from .models import State, District


# ─── District Inline (Full Control inside State) ──────────────────────────────


class DistrictInline(admin.TabularInline):
    model = District
    extra = 1
    fields = ("id", "name", "code", "status")  # ← "id" added here
    readonly_fields = ("id",)  # ← id is read-only (auto assigned)
    can_delete = True
    min_num = 0
    verbose_name = "District"
    verbose_name_plural = "Districts"


# ─── District Admin (Hidden from sidebar, registered only for autocomplete) ───


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    search_fields = ("name", "code", "state__name")  # Required for autocomplete

    def get_model_perms(self, request):
        """Return empty perms so District never appears in the sidebar."""
        return {}


# ─── State Admin (Single entry point — controls everything) ───────────────────


@admin.register(State)
class StateAdmin(admin.ModelAdmin):

    # ── List View ──
    list_display = (
        "id",
        "name",
        "status_badge",
        "district_count",
        "created_at_formatted",
    )
    list_display_links = ("name",)
    search_fields = ("name", "districts__name", "districts__code")
    list_filter = ("status", "created_at")
    ordering = ("id",)

    # ── Detail View ──
    readonly_fields = ("id_display", "created_at", "district_count")
    fieldsets = (
        (
            "🗺️ State Details",
            {
                "description": "Enter the official name of the state and set its status.",
                "fields": ("id_display", "name", "status"),
            },
        ),
        (
            "📊 Stats",
            {
                "fields": ("district_count",),
            },
        ),
        (
            "🕒 Metadata",
            {
                "classes": ("collapse",),
                "fields": ("created_at",),
            },
        ),
    )

    # Districts fully managed from this page
    inlines = [DistrictInline]

    # ── Bulk Actions ──
    actions = [
        "make_active",
        "make_inactive",
        "make_all_districts_active",
        "make_all_districts_inactive",
    ]

    # ── Custom Columns ──

    def status_badge(self, obj):
        colors = {"active": "#28a745", "inactive": "#6c757d"}
        bg = colors.get(obj.status, "#000")
        return mark_safe(
            f'<span style="background:{bg};color:white;padding:3px 10px;'
            f'border-radius:4px;font-weight:bold;">'
            f"{obj.get_status_display()}</span>"
        )

    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    def district_count(self, obj):
        count = obj.districts.count()
        return format_html("<strong>{}</strong> District(s)", count)

    district_count.short_description = "Total Districts"

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%b %d, %Y  %I:%M %p") if obj.created_at else "—"

    created_at_formatted.short_description = "Created At"

    def id_display(self, obj):
        return obj.id or "—"

    id_display.short_description = "ID"

    # ── State Bulk Actions ──

    def make_active(self, request, queryset):
        updated = queryset.update(status="active")
        self.message_user(
            request, f"{updated} state(s) marked as Active.", messages.SUCCESS
        )

    make_active.short_description = "✅ Mark selected States as Active"

    def make_inactive(self, request, queryset):
        updated = queryset.update(status="inactive")
        self.message_user(
            request, f"{updated} state(s) marked as Inactive.", messages.WARNING
        )

    make_inactive.short_description = "🚫 Mark selected States as Inactive"

    # ── District Bulk Actions (applied from State list) ──

    def make_all_districts_active(self, request, queryset):
        updated = District.objects.filter(state__in=queryset).update(status="active")
        self.message_user(
            request,
            f"{updated} district(s) under selected state(s) marked as Active.",
            messages.SUCCESS,
        )

    make_all_districts_active.short_description = (
        "✅ Mark all Districts of selected States as Active"
    )

    def make_all_districts_inactive(self, request, queryset):
        updated = District.objects.filter(state__in=queryset).update(status="inactive")
        self.message_user(
            request,
            f"{updated} district(s) under selected state(s) marked as Inactive.",
            messages.WARNING,
        )

    make_all_districts_inactive.short_description = (
        "🚫 Mark all Districts of selected States as Inactive"
    )

    # ── Auto-format on save ──
    def save_model(self, request, obj, form, change):
        obj.name = obj.name.strip().title()
        super().save_model(request, obj, form, change)


# ------------------ Parent Company ------------------
@admin.register(ParentCompany)
class ParentCompanyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "email",
        "phone_number_formatted",
        "state_link",
        "district_link",
        "gst_number",
        "pan_number",
        "created_at_formatted",
        "has_all_documents",
    )
    list_display_links = ("name",)
    search_fields = ("name", "phone_number", "email", "gst_number", "pan_number")
    list_filter = ("state", "district", "created_at")
    ordering = ("-id",)

    # Make critical identifiers read-only after creation
    readonly_fields = (
        "created_at",
        "id_display",
        "gst_document_link",
        "tan_document_link",
        "pan_document_link",
        "account_number_masked",
    )

    fieldsets = (
        (
            "Company Details",
            {
                "fields": ("id_display", "name", "phone_number", "email", "address"),
                "description": "Primary contact and address information.",
            },
        ),
        (
            "Location",
            {
                "fields": ("state", "district"),
                "description": "Administrative region of the company.",
            },
        ),
        (
            "Bank Details",
            {
                "fields": (
                    "bank_name",
                    "account_holder_name",
                    "account_number_masked",
                    "account_number",
                    "ifsc_code",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "GST Details",
            {
                "fields": ("gst_number", "gst_document", "gst_document_link"),
                "description": "Mandatory for B2B invoicing in India.",
            },
        ),
        (
            "TAN Details",
            {
                "fields": ("tan_number", "tan_document", "tan_document_link"),
            },
        ),
        (
            "PAN Details",
            {
                "fields": ("pan_number", "pan_document", "pan_document_link"),
                "description": "Permanent Account Number – must match GST records.",
            },
        ),
        (
            "System Info",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    # Custom display methods
    def id_display(self, obj):
        return obj.id

    id_display.short_description = "ID"

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%b %d, %Y") if obj.created_at else "—"

    created_at_formatted.short_description = "Created On"

    def phone_number_formatted(self, obj):
        # Simple formatting: e.g., +91 98765 43210
        num = obj.phone_number
        if len(num) == 10:
            return f"+91 {num[:5]} {num[5:]}"
        elif len(num) == 12 and num.startswith("91"):
            return f"+{num[:2]} {num[2:7]} {num[7:]}"
        return num

    phone_number_formatted.short_description = "Phone"

    def state_link(self, obj):
        url = reverse("admin:mapwala_mis_state_change", args=[obj.state.id])
        return mark_safe(f'<a href="{url}" target="_blank">{obj.state.name}</a>')

    state_link.short_description = "State"

    def district_link(self, obj):
        url = reverse("admin:mapwala_mis_district_change", args=[obj.district.id])
        return mark_safe(f'<a href="{url}" target="_blank">{obj.district.name}</a>')

    district_link.short_description = "District"

    def _document_link(self, doc_field, label):
        if doc_field:
            url = doc_field.url
            return mark_safe(
                f'<a href="{url}" target="_blank" style="color:#17a2b8;">📄 View {label}</a>'
            )
        return mark_safe('<span style="color:#dc3545;">⚠️ Missing</span>')

    def gst_document_link(self, obj):
        return self._document_link(obj.gst_document, "GST Doc")

    gst_document_link.short_description = "GST Document"

    def tan_document_link(self, obj):
        return self._document_link(obj.tan_document, "TAN Doc")

    tan_document_link.short_description = "TAN Document"

    def pan_document_link(self, obj):
        return self._document_link(obj.pan_document, "PAN Doc")

    pan_document_link.short_description = "PAN Document"

    def account_number_masked(self, obj):
        """Show only last 4 digits for security."""
        if obj.account_number:
            return "•" * (len(obj.account_number) - 4) + obj.account_number[-4:]
        return "—"

    account_number_masked.short_description = "Account Number (Masked)"

    def has_all_documents(self, obj):
        """Quick visual check if all compliance docs are uploaded."""
        missing = []
        if not obj.gst_document:
            missing.append("GST")
        if not obj.tan_document:
            missing.append("TAN")
        if not obj.pan_document:
            missing.append("PAN")

        if not missing:
            return mark_safe('<span style="color:green;">✓ Complete</span>')
        else:
            return mark_safe(
                f'<span style="color:orange;">⚠️ Missing: {", ".join(missing)}</span>'
            )

    has_all_documents.short_description = "Compliance Docs"
    has_all_documents.admin_order_field = None  # Not sortable

    # Prevent editing of key identifiers after creation (optional but recommended)
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ("gst_number", "pan_number", "tan_number")
        return self.readonly_fields


# ------------------ Vendor ------------------
@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "email",
        "phone_number_formatted",
        "state_link",
        "district_link",
        "gst_number",
        "pan_number",
        "created_at_formatted",
        "has_all_documents",
    )
    list_display_links = ("name",)
    search_fields = ("name", "phone_number", "email", "gst_number", "pan_number")
    list_filter = ("state", "district", "created_at")
    ordering = ("-id",)
    readonly_fields = (
        "created_at",
        "id_display",
        "gst_document_link",
        "tan_document_link",
        "pan_document_link",
        "account_number_masked",
    )
    fieldsets = (
        (
            "Vendor Details",
            {
                "fields": ("id_display", "name", "phone_number", "email", "address"),
                "description": "Primary contact and business address.",
            },
        ),
        (
            "Location",
            {
                "fields": ("state", "district"),
                "description": "Administrative region of the vendor.",
            },
        ),
        (
            "Bank Details",
            {
                "fields": (
                    "bank_name",
                    "account_holder_name",
                    "account_number_masked",
                    "ifsc_code",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Sensitive Data (Edit with caution)",
            {
                "fields": ("account_number",),
                "classes": ("collapse",),
                "description": "Full account number. Edit only if absolutely necessary.",
            },
        ),
        (
            "GST Details",
            {
                "fields": ("gst_number", "gst_document", "gst_document_link"),
                "description": "Mandatory for B2B transactions in India.",
            },
        ),
        (
            "TAN Details",
            {
                "fields": ("tan_number", "tan_document", "tan_document_link"),
            },
        ),
        (
            "PAN Details",
            {
                "fields": ("pan_number", "pan_document", "pan_document_link"),
                "description": "Must match GST registration records.",
            },
        ),
        (
            "System Info",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    # === Custom Display Methods ===

    def id_display(self, obj):
        return obj.id

    id_display.short_description = "ID"

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%b %d, %Y") if obj.created_at else "—"

    created_at_formatted.short_description = "Created On"

    def phone_number_formatted(self, obj):
        num = obj.phone_number
        if len(num) == 10:
            return f"+91 {num[:5]} {num[5:]}"
        elif len(num) == 12 and num.startswith("91"):
            return f"+{num[:2]} {num[2:7]} {num[7:]}"
        return num

    phone_number_formatted.short_description = "Phone"

    def state_link(self, obj):
        url = reverse(
            f"admin:{obj.state._meta.app_label}_{obj.state._meta.model_name}_change",
            args=[obj.state.pk],
        )
        return mark_safe(f'<a href="{url}" target="_blank">{obj.state.name}</a>')

    state_link.short_description = "State"

    def district_link(self, obj):
        url = reverse(
            f"admin:{obj.district._meta.app_label}_{obj.district._meta.model_name}_change",
            args=[obj.district.pk],
        )
        return mark_safe(f'<a href="{url}" target="_blank">{obj.district.name}</a>')

    district_link.short_description = "District"

    def _document_link(self, doc_field, label):
        if doc_field:
            url = doc_field.url
            return mark_safe(
                f'<a href="{url}" target="_blank" style="color:#17a2b8;">View {label}</a>'
            )
        return mark_safe('<span style="color:#dc3545;">Missing</span>')

    def gst_document_link(self, obj):
        return self._document_link(obj.gst_document, "GST Doc")

    gst_document_link.short_description = "GST Document"

    def tan_document_link(self, obj):
        return self._document_link(obj.tan_document, "TAN Doc")

    tan_document_link.short_description = "TAN Document"

    def pan_document_link(self, obj):
        return self._document_link(obj.pan_document, "PAN Doc")

    pan_document_link.short_description = "PAN Document"

    def account_number_masked(self, obj):
        if obj.account_number:
            return "•" * (len(obj.account_number) - 4) + obj.account_number[-4:]
        return "—"

    account_number_masked.short_description = "Account Number (Masked)"

    def has_all_documents(self, obj):
        missing = []
        if not obj.gst_document:
            missing.append("GST")
        if not obj.tan_document:
            missing.append("TAN")
        if not obj.pan_document:
            missing.append("PAN")

        if not missing:
            return mark_safe('<span style="color:green;">✓ Complete</span>')
        else:
            return mark_safe(
                f'<span style="color:orange;">⚠️ Missing: {", ".join(missing)}</span>'
            )

    has_all_documents.short_description = "Compliance Docs"
    has_all_documents.admin_order_field = None

    # Prevent editing of key identifiers after creation
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("gst_number", "pan_number", "tan_number")
        return self.readonly_fields


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


# ------------------ Manufacturer ------------------
@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):

    # ─── List View ────────────────────────────────────────────────────────────

    list_display = (
        "company_name",
        "applicant_name",
        "applicant_email",
        "company_phone",
        "tac_no",
        "tac_validity",
        "created_at",
        "created_by",
    )

    list_filter = (
        "tac_validity",
        "created_at",
        "created_by",
    )

    search_fields = (
        "company_name",
        "applicant_name",
        "applicant_email",
        "company_email",
        "company_gst_no",
        "company_pan_no",
        "tac_no",
        "company_registration_number",
    )

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    list_per_page = 25

    # ─── Detail View – Fieldsets ───────────────────────────────────────────────

    fieldsets = (
        (
            "👤 Applicant Information",
            {
                "fields": (
                    ("applicant_name", "applicant_email"),
                    ("applicant_mobile", "applicant_dob"),
                    "applicant_id_proof_no",
                    "applicant_address",
                    "applicant_pin",
                )
            },
        ),
        (
            "🏢 Company Information",
            {
                "fields": (
                    ("company_name", "company_email"),
                    "company_phone",
                    "company_address",
                    "company_pin",
                    ("company_gst_no", "company_pan_no"),
                    "company_registration_number",
                )
            },
        ),
        (
            "📋 TAC Information",
            {"fields": (("tac_no", "tac_validity"),)},
        ),
        (
            "📁 Document Uploads",
            {
                "description": "Upload required documents below. Existing files are shown as download links.",
                "fields": (
                    "self_certified_applicant",
                    "self_certified_applicant_link",
                    "authorization_letter",
                    "authorization_letter_link",
                    "pan_card",
                    "pan_card_link",
                    "gst_certificate",
                    "gst_certificate_link",
                    "company_registration_certificate",
                    "company_registration_certificate_link",
                    "technical_onboarding_request_letter",
                    "technical_onboarding_request_letter_link",
                    "tac_document",
                    "tac_document_link",
                ),
            },
        ),
        (
            "🔐 Meta",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_by",
                    "created_at",
                ),
            },
        ),
    )

    readonly_fields = (
        "created_at",
        # document preview links
        "self_certified_applicant_link",
        "authorization_letter_link",
        "pan_card_link",
        "gst_certificate_link",
        "company_registration_certificate_link",
        "technical_onboarding_request_letter_link",
        "tac_document_link",
    )

    # ─── Auto-fill created_by on save ─────────────────────────────────────────

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # ─── Document Preview Helpers ──────────────────────────────────────────────

    def _file_link(self, file_field, label):
        if file_field and hasattr(file_field, "url"):
            return format_html(
                '<a href="{}" target="_blank">📄 View / Download {}</a>',
                file_field.url,
                label,
            )
        return "No file uploaded"

    def self_certified_applicant_link(self, obj):
        return self._file_link(obj.self_certified_applicant, "Self Certified Document")

    self_certified_applicant_link.short_description = "Current File"

    def authorization_letter_link(self, obj):
        return self._file_link(obj.authorization_letter, "Authorization Letter")

    authorization_letter_link.short_description = "Current File"

    def pan_card_link(self, obj):
        return self._file_link(obj.pan_card, "PAN Card")

    pan_card_link.short_description = "Current File"

    def gst_certificate_link(self, obj):
        return self._file_link(obj.gst_certificate, "GST Certificate")

    gst_certificate_link.short_description = "Current File"

    def company_registration_certificate_link(self, obj):
        return self._file_link(
            obj.company_registration_certificate, "Company Registration Certificate"
        )

    company_registration_certificate_link.short_description = "Current File"

    def technical_onboarding_request_letter_link(self, obj):
        return self._file_link(
            obj.technical_onboarding_request_letter,
            "Technical Onboarding Request Letter",
        )

    technical_onboarding_request_letter_link.short_description = "Current File"

    def tac_document_link(self, obj):
        return self._file_link(obj.tac_document, "TAC Document")

    tac_document_link.short_description = "Current File"


# ------------------ Distributor ------------------
@admin.register(Distributor)
class DistributorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "phone_number",
        "email",
        "linked_to",
        "manufacturer",
        "created_at",
    )
    search_fields = (
        "name",
        "phone_number",
        "email",
        "gst_number",
        "pan_number",
        "manufacturer__name",
    )
    list_filter = ("linked_to", "state", "district", "created_at")
    ordering = ("-id",)
    readonly_fields = ("created_at",)
    filter_horizontal = ("authorised_states", "authorised_districts")
    fieldsets = (
        ("Basic Information", {"fields": ("name", "phone_number", "email", "address")}),
        ("Address Location", {"fields": ("state", "district")}),
        ("Linking Information", {"fields": ("linked_to", "manufacturer")}),
        ("Authorised Area", {"fields": ("authorised_states", "authorised_districts")}),
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


# ------------------ Dealer ------------------
@admin.register(Dealer)
class DealerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "phone_number",
        "email",
        "linked_to",
        "manufacturer",
        "distributor",
        "state",
        "district",
        "created_at",
    )
    search_fields = ("name", "phone_number", "email", "gst_number", "pan_number")
    list_filter = (
        "linked_to",
        "state",
        "district",
        "manufacturer",
        "distributor",
        "created_at",
    )
    ordering = ("-id",)
    readonly_fields = ("created_at",)
    filter_horizontal = ("authorised_states", "authorised_districts")
    fieldsets = (
        ("Basic Information", {"fields": ("name", "phone_number", "email", "address")}),
        ("Address Location", {"fields": ("state", "district")}),
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
        (
            "Tax Documents",
            {
                "fields": (
                    "gst_number",
                    "gst_document",
                    "tan_number",
                    "tan_document",
                    "pan_number",
                    "pan_document",
                )
            },
        ),
        ("Business Linking", {"fields": ("linked_to", "manufacturer", "distributor")}),
        (
            "Authorised Area",
            {"fields": ("authorised_states", "authorised_districts")},
        ),
        ("System Info", {"fields": ("created_at",)}),
    )


# ------------------ Product ------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("product_id", "created_at")
    search_fields = ("product_id",)
    ordering = ("product_id",)
    readonly_fields = ("created_at",)


# ------------------ Device and Inlines ------------------
class DeviceInformationInline(admin.StackedInline):
    model = DeviceInformation
    extra = 0
    can_delete = False


class BOMInline(admin.StackedInline):
    model = BOM
    extra = 0
    can_delete = False


class EnclosureInline(admin.StackedInline):
    model = Enclosure
    extra = 0


class WireHarnessInline(admin.StackedInline):
    model = WireHarness
    extra = 0


class BatteryInline(admin.StackedInline):
    model = Battery
    extra = 0


class SOSButtonInline(admin.StackedInline):
    model = SOSButton
    extra = 0


class UserManualInline(admin.StackedInline):
    model = UserManual
    extra = 0


class StickerInline(admin.TabularInline):
    model = Sticker
    extra = 0


class AccessoryInline(admin.TabularInline):
    model = Accessory
    extra = 0


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "id_link",
        "status_badge",
        "completion_status",
        "created_by",
        "created_at_formatted",
    )
    list_filter = ("status", "created_at")
    readonly_fields = ("status", "created_by", "created_at")

    inlines = [
        DeviceInformationInline,
        BOMInline,
        EnclosureInline,
        WireHarnessInline,
        BatteryInline,
        SOSButtonInline,
        StickerInline,
        UserManualInline,
        AccessoryInline,
    ]

    def has_add_permission(self, request):
        return False

    def id_link(self, obj):
        url = reverse(
            f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
            args=[obj.pk],
        )
        return mark_safe(f"<strong>Device-{obj.id}</strong>")
    id_link.short_description = "Device ID"

    def status_badge(self, obj):
        colors = {"draft": "#ffc107", "completed": "#28a745"}
        return mark_safe(
            f'<span style="background:{colors.get(obj.status)};'
            f'color:white;padding:4px 8px;border-radius:4px;">'
            f'{obj.get_status_display()}</span>'
        )
    status_badge.short_description = "Status"

    def completion_status(self, obj):
        steps = {
            "Info": hasattr(obj, "info"),
            "BOM": hasattr(obj, "bom"),
            "Enclosure": hasattr(obj, "enclosure"),
            "Wire": hasattr(obj, "wireharness"),
            "Battery": hasattr(obj, "battery"),
            "SOS": hasattr(obj, "sosbutton"),
            "Manual": hasattr(obj, "usermanual"),
        }

        return mark_safe(
            " ".join(
                f"<span style='color:{'green' if done else 'red'}'>{step}</span>"
                for step, done in steps.items()
            )
        )
    completion_status.short_description = "Completion"

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%d %b %Y %I:%M %p")
    created_at_formatted.short_description = "Created At"


# ------------------ Proforma Invoice ------------------
@admin.register(ProformaInvoice)
class ProformaInvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "party_type",
        "product",
        "quantity",
        "selling_price",
        "discount_percent",
        "grand_total",
        "payment_terms",
        "delivery_date",
        "state",
        "created_at",
    )
    search_fields = (
        "id",
        "product__product_id",
        "contact_person_name",
        "mobile_no",
        "gstn",
    )
    list_filter = (
        "party_type",
        "payment_terms",
        "state",
        "delivery_date",
        "created_at",
    )
    ordering = ("-id",)
    readonly_fields = ("created_at",)
    fieldsets = (
        (
            "Party Information",
            {
                "fields": (
                    "party_type",
                    "b2b_partner",
                    "b2c_customer",
                    "dealer",
                    "distributor",
                )
            },
        ),
        (
            "Product & Pricing",
            {
                "fields": (
                    "product",
                    "selling_price",
                    "discount_percent",
                    "quantity",
                    "shipping_charges",
                    "grand_total",
                )
            },
        ),
        (
            "Payment & Delivery",
            {"fields": ("payment_terms", "delivery_date", "delivery_address", "state")},
        ),
        (
            "Contact Information",
            {"fields": ("contact_person_name", "mobile_no", "gstn")},
        ),
        ("System Info", {"fields": ("created_at",)}),
    )


# -----------------------Order Batch Inline--------------------------
class OrderBatchInline(admin.TabularInline):
    """
    Inline batches under a product.
    IMPORTANT:
    - product FK is implicitly set by parent
    - fk_name explicitly tells Django which FK to use
    """

    model = OrderBatch
    fk_name = "product"
    extra = 1
    fields = ("batch_number", "available_stock")
    can_delete = True
    show_change_link = True
    ordering = ("batch_number",)


# # -----------------------Order Product Admin--------------------------
@admin.register(OrderProduct)
class OrderProductAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)
    inlines = [OrderBatchInline]
    fieldsets = (
        (
            "Product / Device Model",
            {"fields": ("name",)},
        ),
    )


# -----------------------Order Batch Admin--------------------------
@admin.register(OrderBatch)
class OrderBatchAdmin(admin.ModelAdmin):
    list_display = ("product", "batch_number", "available_stock")
    list_filter = ("product",)
    search_fields = ("product__name", "batch_number")
    ordering = ("product__name", "batch_number")
    fieldsets = (
        (
            "Product Reference",
            {
                "fields": ("product",),
            },
        ),
        (
            "Batch Details",
            {
                "fields": ("batch_number", "available_stock"),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        """
        Prevent changing product on existing batches.
        This avoids duplicate validation bugs.
        """
        if obj:
            return ("product",)
        return ()


# ----------------------------Sales Order Admin-------------------------------
@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_name",
        "customer_type",
        "product",
        "batch",
        "quantity",
        "grand_total",
        "payment_status",
        "delivery_date",
        "created_at",
    )
    list_filter = (
        "customer_type",
        "payment_mode",
        "payment_status",
        "delivery_date",
        "created_at",
    )
    search_fields = (
        "id",
        "customer_name",
        "contact_person",
        "mobile_no",
        "invoice_number",
        "product__name",
        "batch__batch_number",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    fieldsets = (
        (
            "Customer Information",
            {
                "fields": (
                    "customer_name",
                    "customer_type",
                    "contact_person",
                    "mobile_no",
                ),
            },
        ),
        (
            "Product & Batch",
            {
                "fields": ("product", "batch", "quantity", "unit_price"),
            },
        ),
        (
            "Pricing & Taxes",
            {
                "fields": (
                    "discount_percent",
                    "gst_percent",
                    "shipping_charges",
                    "grand_total",
                ),
            },
        ),
        (
            "Delivery Information",
            {
                "fields": ("delivery_date", "delivery_address"),
            },
        ),
        (
            "Payment Information",
            {
                "fields": ("payment_mode", "payment_status", "invoice_number"),
            },
        ),
        (
            "Additional Notes",
            {
                "fields": ("remarks",),
            },
        ),
        (
            "System Information",
            {
                "fields": ("created_at",),
            },
        ),
    )


# -----------------------Supplier / Vendor Admin--------------------------
@admin.register(SupplierVendor)
class SupplierVendorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)
    fieldsets = (("Supplier / Vendor", {"fields": ("name",)}),)


# -----------------------Production Order Admin--------------------------
@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "production_type",
        "product",
        "product_category",
        "quantity_added",
        "total_value",
        "supplier_vendor",
        "purchase_date",
        "manufacturing_date",
        "batch",
        "created_at",
    )
    list_filter = (
        "production_type",
        "product_category",
        "purchase_date",
        "manufacturing_date",
        "supplier_vendor",
        "created_at",
    )
    search_fields = (
        "id",
        "product__name",
        "supplier_vendor__name",
        "batch__batch_number",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Production Type", {"fields": ("production_type",)}),
        ("Product Information", {"fields": ("product", "product_category", "batch")}),
        (
            "Quantity & Pricing",
            {"fields": ("quantity_added", "unit_price", "total_value")},
        ),
        ("Supplier", {"fields": ("supplier_vendor",)}),
        ("Dates", {"fields": ("purchase_date", "manufacturing_date")}),
        ("Additional Notes", {"fields": ("remarks",)}),
        ("System Information", {"fields": ("created_at",)}),
    )


# ----------------------- Make To Order Admin --------------------------
@admin.register(OrderEntryMakeToOrder)
class OrderEntryMakeToOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_entry",
        "customer_name",
        "customer_type",
        "product",
        "quantity",
        "grand_total",
        "payment_terms",
        "order_priority",
        "expected_delivery_date",
        "created_at",
    )
    list_filter = (
        "customer_type",
        "payment_terms",
        "order_priority",
        "expected_delivery_date",
        "created_at",
    )
    search_fields = (
        "id",
        "order_entry__id",
        "customer_name",
        "contact_person",
        "mobile_no",
        "product__name",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Order Reference", {"fields": ("order_entry",)}),
        (
            "Customer Information",
            {
                "fields": (
                    "customer_name",
                    "customer_type",
                    "contact_person",
                    "mobile_no",
                )
            },
        ),
        (
            "Product & Customization",
            {"fields": ("product", "product_specifications", "customization_details")},
        ),
        ("Quantity & Delivery", {"fields": ("quantity", "expected_delivery_date")}),
        (
            "Pricing",
            {
                "fields": (
                    "unit_price",
                    "discount_percent",
                    "gst_percent",
                    "shipping_charges",
                    "grand_total",
                    "advance_payment",
                )
            },
        ),
        ("Payment & Priority", {"fields": ("payment_terms", "order_priority")}),
        ("Special Instructions", {"fields": ("special_instructions",)}),
        ("System Information", {"fields": ("created_at",)}),
    )


# ===================== RFQ SELECTION INLINE =====================
class RFQSelectionInline(admin.TabularInline):
    model = RFQSelection
    extra = 0
    fields = ("item_type", "reference")
    autocomplete_fields = ()
    show_change_link = True


# ===================== REQUEST FOR QUOTE ADMIN =====================
@admin.register(RequestForQuote)
class RequestForQuoteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_reference",
        "device_name",
        "assembly_type",
        "quantity",
        "srn_no",
        "delivery_date",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("assembly_type", "srn_no", "status", "delivery_date", "created_by")
    search_fields = ("order_reference", "device_name", "created_by__username")
    ordering = ("-created_at",)
    readonly_fields = ("created_by", "created_at")
    inlines = [RFQSelectionInline]
    fieldsets = (
        (
            "STEP 1 — Order Selection (UI Driven)",
            {"fields": ("order_reference", "device_name", "assembly_type", "quantity")},
        ),
        (
            "STEP 3 — Quote Details (UI Driven)",
            {
                "fields": (
                    "srn_no",
                    "delivery_date",
                    "delivery_address",
                    "additional_requirements",
                )
            },
        ),
        ("System Status", {"fields": ("status",)}),
        ("Audit Fields", {"fields": ("created_by", "created_at")}),
    )

    def save_model(self, request, obj, form, change):
        """
        Automatically assign logged-in admin user
        """
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# -------------------- Inlines --------------------
class PurchaseOrderTypeInline(admin.TabularInline):
    model = PurchaseOrderType
    extra = 1
    fields = ("order_type",)
    show_change_link = True


# -------------------- Inlines --------------------
class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = (
        "item_code",
        "item_type",
        "vendor_id",
        "vendor_name",
        "unit_price",
        "gst_amount",
        "total_price",
        "delivery_days",
    )
    show_change_link = True


# -------------------- Purchase Order Admin --------------------
@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_id",
        "buyer_name",
        "rfq_id",
        "assembly_type",
        "delivery_date",
        "payment_terms",
        "created_by",
        "created_at",
    )
    list_filter = ("assembly_type", "payment_terms", "delivery_date", "created_at")
    search_fields = (
        "order_id",
        "rfq_id",
        "buyer_name",
        "created_by__username",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    inlines = [PurchaseOrderTypeInline, PurchaseOrderItemInline]
    fieldsets = (
        (
            "Step 1 — Order Details",
            {"fields": ("buyer_name", "order_id", "rfq_id", "assembly_type")},
        ),
        (
            "Step 2 — Vendor & Delivery",
            {
                "fields": (
                    "wastage_percentage",
                    "selected_vendor_id",
                    "delivery_date",
                    "payment_terms",
                )
            },
        ),
        ("System Information", {"fields": ("created_by", "created_at")}),
    )


# -------------------- Purchase Order Type Admin --------------------
@admin.register(PurchaseOrderType)
class PurchaseOrderTypeAdmin(admin.ModelAdmin):
    list_display = ("purchase_order", "order_type")
    list_filter = ("order_type",)
    search_fields = ("purchase_order__order_id",)

    fieldsets = (
        ("Purchase Order", {"fields": ("purchase_order",)}),
        ("Order Type", {"fields": ("order_type",)}),
    )


# -------------------- Purchase Order Item Admin --------------------
@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "purchase_order",
        "item_code",
        "item_type",
        "quantity",
        "vendor_name",
        "unit_price",
        "total_price",
        "delivery_days",
    )

    list_filter = ("item_type",)
    search_fields = ("item_code", "vendor_name", "purchase_order__order_id")

    fieldsets = (
        ("Purchase Order", {"fields": ("purchase_order",)}),
        (
            "Item Details",
            {"fields": ("item_code", "item_type", "quantity", "delivery_days")},
        ),
        ("Vendor", {"fields": ("vendor_id", "vendor_name")}),
        ("Pricing", {"fields": ("unit_price", "gst_amount", "total_price")}),
    )


# -----------------------Material Receipt Item Admin--------------------------
class MaterialReceiptItemInline(admin.TabularInline):
    model = MaterialReceiptItem
    extra = 1
    fields = ("purchase_order_item", "received_qty", "serial_numbers", "balance_qty")
    readonly_fields = ("balance_qty",)
    autocomplete_fields = ("purchase_order_item",)
    show_change_link = True


# -----------------------Material Receipt Note Admin--------------------------
@admin.register(MaterialReceiptNote)
class MaterialReceiptNoteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "purchase_order",
        "vendor",
        "inward_type",
        "receipt_date",
        "batch_number",
        "created_at",
    )
    list_filter = ("inward_type", "receipt_date", "vendor")
    search_fields = (
        "batch_number",
        "invoice_number",
        "purchase_order__order_id",
        "vendor__name",
    )
    autocomplete_fields = ("purchase_order", "vendor")
    readonly_fields = ("created_at",)
    inlines = [MaterialReceiptItemInline]
    fieldsets = (
        (
            "Order & Vendor",
            {"fields": ("purchase_order", "po_date", "vendor", "inward_type")},
        ),
        ("Receipt", {"fields": ("receipt_date", "batch_number")}),
        (
            "Documents",
            {
                "fields": (
                    "invoice_number",
                    "invoice_file",
                    "delivery_challan_number",
                    "challan_file",
                    "eway_bill_number",
                    "eway_bill_file",
                )
            },
        ),
        ("Additional Info", {"fields": ("remarks",)}),
        ("System", {"fields": ("created_by", "created_at")}),
    )


# -----------------------Dispatch Admin--------------------------
@admin.register(Dispatch)
class DispatchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sales_order",
        "order_type",
        "product",
        "batch",
        "dispatch_quantity",
        "dispatch_date",
        "created_by",
        "created_at",
    )
    list_filter = (
        "order_type",
        "dispatch_date",
        "urgent_delivery_required",
        "insurance_required",
    )
    search_fields = (
        "sales_order__id",
        "customer_name",
        "customer_contact",
        "customer_email",
    )
    readonly_fields = ("created_by", "created_at")
    fieldsets = (
        (
            "STEP 1: Sales Order Selection",
            {"fields": ("sales_order", "order_type")},
        ),
        (
            "STEP 2: Stock Verification",
            {
                "fields": (
                    "product",
                    "batch",
                    "dispatch_quantity",
                    "imei_number",
                    "serial_number",
                    "iccid_number",
                )
            },
        ),
        (
            "STEP 3: Dispatch Details",
            {"fields": ("dispatch_date", "dispatch_remarks")},
        ),
        (
            "STEP 4: Customer Details & Review",
            {
                "fields": (
                    "customer_name",
                    "customer_contact",
                    "customer_email",
                    "customer_address",
                    "urgent_delivery_required",
                    "insurance_required",
                )
            },
        ),
        (
            "System Information",
            {"fields": ("created_by", "created_at")},
        ),
    )

    def save_model(self, request, obj, form, change):
        """
        Auto-assign created_by on first save
        """
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ---------------------- Inline Formset with validation & auto-calculation ----------------------
class PostDispatchReturnItemInlineFormset(BaseInlineFormSet):
    """
    Ensures:
    - return_qty <= dispatched_qty
    - return_amount is auto-calculated
    """

    def clean(self):
        super().clean()

        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue

            dispatched_qty = form.cleaned_data.get("dispatched_qty")
            return_qty = form.cleaned_data.get("return_qty")
            unit_price = form.cleaned_data.get("unit_price")

            if return_qty > dispatched_qty:
                raise ValueError("Return quantity cannot exceed dispatched quantity.")

            # Auto-calculate return_amount
            form.instance.return_amount = Decimal(return_qty) * unit_price


# --------------------------- Post Dispatch Return Item Inline --------------------------
class PostDispatchReturnItemInline(admin.TabularInline):
    model = PostDispatchReturnItem
    formset = PostDispatchReturnItemInlineFormset
    extra = 1
    readonly_fields = ("return_amount",)
    fields = (
        "product_id",
        "description",
        "dispatched_qty",
        "unit_price",
        "return_qty",
        "return_amount",
    )


# -----------------------Post Dispatch Return Admin--------------------------
@admin.register(PostDispatchReturn)
class PostDispatchReturnAdmin(admin.ModelAdmin):
    """
    Admin panel for Post-Dispatch Returns
    Allows controlled raw data insertion.
    """

    inlines = [PostDispatchReturnItemInline]
    # ---------------- List View ----------------
    list_display = (
        "id",
        "dispatch_id",
        "invoice_no",
        "customer_name",
        "return_type",
        "return_reason",
        "total_return_amount",
        "created_by",
        "created_at",
    )
    list_filter = ("return_type", "return_reason", "created_at")
    search_fields = ("dispatch_id", "invoice_no", "customer_name")
    ordering = ("-id",)
    date_hierarchy = "created_at"
    # ---------------- Form Layout ----------------
    fieldsets = (
        (
            "Dispatch Information",
            {
                "fields": (
                    "dispatch_id",
                    "invoice_no",
                    "customer_name",
                    "dispatch_total_value",
                )
            },
        ),
        (
            "Return Details",
            {
                "fields": (
                    "return_type",
                    "return_reason",
                    "return_date",
                    "return_remarks",
                )
            },
        ),
        (
            "System Information",
            {"fields": ("total_return_amount", "created_by")},
        ),
    )

    # ---------------- Readonly ----------------
    readonly_fields = (
        "total_return_amount",
        "created_at",
    )

    # ---------------- Auto fields ----------------
    def save_model(self, request, obj, form, change):
        """
        Auto-assign created_by when adding from admin
        """
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        """
        Recalculate total_return_amount after saving items
        """
        super().save_related(request, form, formsets, change)

        total = Decimal("0.00")
        for item in form.instance.items.all():
            total += item.return_amount

        form.instance.total_return_amount = total
        form.instance.save(update_fields=["total_return_amount"])

    # ---------------- Permissions ----------------
    def has_delete_permission(self, request, obj=None):
        """
        Optional: allow delete only to superusers
        """
        return request.user.is_superuser

    list_per_page = 25
    save_on_top = True


# -------------------------- BaseRegistrationAdmin --------------------------
class BaseRegistrationAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at",)
    list_filter = ("state", "district", "created_at")
    search_fields = ("phone_number", "email")

    autocomplete_fields = ("state", "district")

    fieldsets = (
        ("Basic Information", {"fields": ("phone_number", "email", "address")}),
        ("Location Details", {"fields": ("state", "district")}),
        (
            "Identity Details",
            {
                "fields": (
                    "aadhar_number",
                    "aadhar_document",
                    "pan_number",
                    "pan_document",
                )
            },
        ),
        ("System Information", {"fields": ("created_at",)}),
    )


# --------------------------------- Account Registration ---------------------------------
@admin.register(AccountRegistration)
class AccountRegistrationAdmin(BaseRegistrationAdmin):
    list_display = (
        "account_name",
        "phone_number",
        "email",
        "state",
        "district",
        "created_at",
    )
    search_fields = BaseRegistrationAdmin.search_fields + ("account_name",)
    fieldsets = (
        ("Account Information", {"fields": ("account_name",)}),
    ) + BaseRegistrationAdmin.fieldsets


# ----------------------- QC Inspector Registration ---------------------------
@admin.register(QCInspectorRegistration)
class QCInspectorRegistrationAdmin(BaseRegistrationAdmin):
    list_display = (
        "qc_inspector_name",
        "phone_number",
        "email",
        "state",
        "district",
        "created_at",
    )
    search_fields = BaseRegistrationAdmin.search_fields + ("qc_inspector_name",)
    fieldsets = (
        ("QC Inspector Information", {"fields": ("qc_inspector_name",)}),
    ) + BaseRegistrationAdmin.fieldsets


# ---------------------------- Purchase Department Registration ----------------------------
@admin.register(PurchaseDepartmentRegistration)
class PurchaseDepartmentRegistrationAdmin(BaseRegistrationAdmin):
    list_display = (
        "purchase_department_name",
        "phone_number",
        "email",
        "state",
        "district",
        "created_at",
    )
    search_fields = BaseRegistrationAdmin.search_fields + ("purchase_department_name",)
    fieldsets = (
        ("Purchase Department Information", {"fields": ("purchase_department_name",)}),
    ) + BaseRegistrationAdmin.fieldsets


# ------------------------- Store Manager Registration --------------------------
@admin.register(StoreManagerRegistration)
class StoreManagerRegistrationAdmin(BaseRegistrationAdmin):
    list_display = (
        "store_manager_name",
        "phone_number",
        "email",
        "state",
        "district",
        "created_at",
    )
    search_fields = BaseRegistrationAdmin.search_fields + ("store_manager_name",)
    fieldsets = (
        ("Store Manager Information", {"fields": ("store_manager_name",)}),
    ) + BaseRegistrationAdmin.fieldsets


# ------------------------- Repair Technician Registration --------------------------
@admin.register(RepairTechnicianRegistration)
class RepairTechnicianRegistrationAdmin(BaseRegistrationAdmin):
    list_display = (
        "repair_technician_name",
        "phone_number",
        "email",
        "state",
        "district",
        "created_at",
    )
    search_fields = BaseRegistrationAdmin.search_fields + ("repair_technician_name",)
    fieldsets = (
        ("Repair Technician Information", {"fields": ("repair_technician_name",)}),
    ) + BaseRegistrationAdmin.fieldsets


# ------------------ Product Category ------------------
@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("created_at",)


# ------------------ Store Transfer ------------------
@admin.register(StoreTransfer)
class StoreTransferAdmin(admin.ModelAdmin):
    list_display = (
        "transfer_id",
        "product_name",
        "product",
        "category",
        "vendor",
        "quantity",
        "total_value",
        "dispatch_status",
        "transfer_date",
        "created_at",
    )
    search_fields = (
        "transfer_id",
        "product_name",
        "batch_number",
        "mrn_number",
        "vendor__name",
        "product__product_id",
    )
    list_filter = (
        "dispatch_status",
        "transfer_date",
        "category",
        "vendor",
        "created_at",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Product Information", {"fields": ("product", "product_name", "category")}),
        ("Transfer Details", {"fields": ("transfer_id", "mrn_number", "batch_number")}),
        (
            "Vendor & Quantity",
            {"fields": ("vendor", "quantity", "unit_price", "total_value")},
        ),
        ("Dates & Status", {"fields": ("transfer_date", "dispatch_status")}),
        ("System Info", {"fields": ("created_by", "created_at", "updated_at")}),
    )


# ============================================================
# DEBIT NOTES & CREDIT NOTES - ACCOUNT MANAGEMENT
# ============================================================


# ------------------ Debit Note ------------------
@admin.register(DebitNote)
class DebitNoteAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "date",
        "vendor",
        "get_reason_display",
        "amount_formatted",
        "status_badge",
        "created_by",
        "created_at_formatted",
    )
    list_display_links = ("number",)
    search_fields = ("number", "vendor", "reference_document")
    list_filter = ("status", "reason", "date", "created_at")
    ordering = ("-created_at",)
    readonly_fields = ("number", "created_at", "updated_at", "created_by")
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": ("number", "date", "vendor", "reason", "amount"),
                "description": "Core debit note information",
            },
        ),
        (
            "Status & References",
            {
                "fields": ("status", "reference_document"),
            },
        ),
        (
            "Additional Details",
            {
                "fields": ("remarks",),
            },
        ),
        (
            "System Info",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def amount_formatted(self, obj):
        return f"₹{obj.amount:,.2f}"

    amount_formatted.short_description = "Amount"

    def status_badge(self, obj):
        colors = {
            "pending": "#FFA500",
            "approved": "#28a745",
            "rejected": "#dc3545",
            "processed": "#007bff",
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, "#6c757d"),
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%d-%m-%Y %H:%M")

    created_at_formatted.short_description = "Created At"

    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ------------------------- Credit Notes --------------------------
@admin.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "date",
        "customer",
        "get_reason_display",
        "amount_formatted",
        "status_badge",
        "created_by",
        "created_at_formatted",
    )
    list_display_links = ("number",)
    search_fields = ("number", "customer", "reference_document")
    list_filter = ("status", "reason", "date", "created_at")
    ordering = ("-created_at",)
    readonly_fields = ("number", "created_at", "updated_at", "created_by")
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": ("number", "date", "customer", "reason", "amount"),
                "description": "Core credit note information",
            },
        ),
        (
            "Status & References",
            {
                "fields": ("status", "reference_document"),
            },
        ),
        (
            "Additional Details",
            {
                "fields": ("remarks",),
            },
        ),
        (
            "System Info",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def amount_formatted(self, obj):
        return f"₹{obj.amount:,.2f}"

    amount_formatted.short_description = "Amount"

    def status_badge(self, obj):
        colors = {
            "pending": "#FFA500",
            "approved": "#28a745",
            "rejected": "#dc3545",
            "processed": "#007bff",
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, "#6c757d"),
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%d-%m-%Y %H:%M")

    created_at_formatted.short_description = "Created At"

    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ------------------------- Return Request Admin --------------------------
@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    """
    Admin configuration for Return Requests
    """

    # Columns shown in admin list view
    list_display = (
        "return_number",
        "date",
        "items",
        "reason",
        "status",
        "amount",
        "created_by",
        "created_at",
    )

    # Sidebar filters
    list_filter = ("status", "date", "created_at")

    # Search box fields
    search_fields = ("return_number", "reason", "items", "created_by__username")

    # Default ordering
    ordering = ("-date",)

    # Read-only fields (system managed)
    readonly_fields = ("created_at", "updated_at", "created_by")

    # Group fields nicely in admin form
    fieldsets = (
        (
            "Return Information",
            {
                "fields": (
                    "return_number",
                    "date",
                    "status",
                )
            },
        ),
        (
            "Return Details",
            {
                "fields": (
                    "items",
                    "reason",
                    "amount",
                )
            },
        ),
        (
            "Audit Information",
            {
                "fields": (
                    "created_by",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    # Performance optimization
    list_select_related = ("created_by",)


# ---------------------------- Repair Record Admin ----------------------------
@admin.register(RepairRecord)
class RepairRecordAdmin(admin.ModelAdmin):
    """
    Admin configuration for Repair Records
    """

    list_display = (
        "product_id",
        "product_name",
        "vendor",
        "mrn_number",
        "failed_qty",
        "repaired_qty",
        "rejected_qty",
        "repair_pending",
        "repair_type",
        "repair_center",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "repair_type", "vendor", "created_at")
    search_fields = (
        "product_id",
        "product_name",
        "vendor",
        "mrn_number",
        "repair_type",
        "repair_center",
        "created_by__username",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "created_by")

    fieldsets = (
        (
            "Product Information",
            {
                "fields": (
                    "product_id",
                    "product_name",
                )
            },
        ),
        (
            "Vendor & MRN",
            {
                "fields": (
                    "vendor",
                    "mrn_number",
                )
            },
        ),
        (
            "Repair Quantities",
            {
                "fields": (
                    "failed_qty",
                    "repaired_qty",
                    "rejected_qty",
                    "repair_pending",
                )
            },
        ),
        (
            "Repair Details",
            {
                "fields": (
                    "repair_type",
                    "repair_center",
                    "status",
                )
            },
        ),
        (
            "Audit Information",
            {
                "fields": (
                    "created_by",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    list_select_related = ("created_by",)


# --------------------------- Repair Type Admin ----------------------------
@admin.register(RejectedItem)
class RejectedItemAdmin(admin.ModelAdmin):
    """
    Admin configuration for Rejected Items
    """

    list_display = (
        "product_id",
        "product_name",
        "vendor",
        "mrn_number",
        "rejected_qty",
        "qc_date",
        "created_by",
    )
    list_filter = ("vendor", "qc_date", "created_at")
    search_fields = (
        "product_id",
        "product_name",
        "vendor",
        "mrn_number",
        "created_by__username",
    )
    ordering = ("-qc_date",)
    readonly_fields = ("created_at", "updated_at", "created_by")
    fieldsets = (
        (
            "Product Information",
            {
                "fields": (
                    "product_id",
                    "product_name",
                )
            },
        ),
        (
            "Vendor & MRN",
            {
                "fields": (
                    "vendor",
                    "mrn_number",
                )
            },
        ),
        (
            "Rejection Details",
            {
                "fields": (
                    "rejected_qty",
                    "qc_date",
                )
            },
        ),
        (
            "Audit Information",
            {
                "fields": (
                    "created_by",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    list_select_related = ("created_by",)


# ============================================================================
# Self Order
# ============================================================================
@admin.register(SelfOrder)
class SelfOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "device_info",
        "quantity",
        "supply_state",
        "rate_display",
        "gst_rate_display",
        "gross_amount_display",
        "delivery_date",
        "user",
        "created_at",
    )
    list_display_links = ("id",)
    search_fields = ("user__username", "delivery_address", "device__info__model")
    list_filter = ("supply_state", "gst_rate", "created_at", "user")
    readonly_fields = ("user", "created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Order Information",
            {
                "fields": (
                    "device",
                    "quantity",
                )
            },
        ),
        (
            "Pricing & Taxes",
            {
                "fields": (
                    "rate",
                    "gst_rate",
                    "gross_amount",
                )
            },
        ),
        (
            "Delivery Details",
            {
                "fields": (
                    "supply_state",
                    "delivery_date",
                    "delivery_address",
                )
            },
        ),
        ("Additional Information", {"fields": ("purpose_remark",)}),
        (
            "Audit Information",
            {
                "fields": (
                    "user",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )
    list_select_related = ("device", "supply_state", "user")

    def device_info(self, obj):
        """Display device model name"""
        return obj.device.info.model if obj.device.info else f"Device {obj.device.id}"

    device_info.short_description = "Device"

    def rate_display(self, obj):
        """Display rate with currency"""
        return f"₹{obj.rate:,.2f}"

    rate_display.short_description = "Rate"

    def gst_rate_display(self, obj):
        """Display GST rate as percentage"""
        return f"{obj.gst_rate}%"

    gst_rate_display.short_description = "GST Rate"

    def gross_amount_display(self, obj):
        """Display gross amount with currency"""
        return f"₹{obj.gross_amount:,.2f}"

    gross_amount_display.short_description = "Gross Amount"


# ============================================================================
# RFQ QUOTATION ADMIN
# ============================================================================

@admin.register(RFQQuotation)
class RFQQuotationAdmin(admin.ModelAdmin):
    """
    Admin configuration for vendor quotations against RFQs
    """
    list_display = (
        "rfq",
        "vendor",
        "status",
        "quotation_rate",
        "quotation_date",
        "created_at",
    )
    list_filter = ("status", "quotation_date", "created_at")
    search_fields = ("rfq__id", "vendor__name")
    ordering = ("-created_at",)
    autocomplete_fields = ("rfq", "vendor")

    readonly_fields = ("created_at", "updated_at")


# ============================================================================
# QUOTATION SEQUENCE ADMIN
# ============================================================================

@admin.register(QuotationSequence)
class QuotationSequenceAdmin(admin.ModelAdmin):
    """
    Maintains year-wise quotation number sequence
    """
    list_display = ("year", "last_number")
    ordering = ("-year",)


# ============================================================================
# QUOTATION ITEM INLINE
# ============================================================================

class QuotationItemInline(admin.TabularInline):
    """
    Inline items displayed inside Quotation admin
    """
    model = QuotationItem
    extra = 0
    min_num = 1

    fields = (
        "item_name",
        "item_type",
        "quantity",
        "net_unit_price_excl_gst",
        "gst_rate",
        "subtotal_excl_gst",
        "gst_amount",
        "total_incl_gst",
    )

    readonly_fields = ("gst_amount", "total_incl_gst")


# ============================================================================
# QUOTATION ADMIN
# ============================================================================

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    """
    Admin configuration for final quotation documents
    """
    list_display = (
        "quotation_number",
        "customer_name",
        "vendor",
        "status",
        "grand_total_incl_gst",
        "valid_until",
        "created_at",
    )

    list_filter = ("status", "created_at", "valid_until")
    search_fields = (
        "quotation_number",
        "customer_name",
        "vendor__name",
        "rfq__id",
    )

    ordering = ("-created_at",)
    autocomplete_fields = ("rfq", "vendor", "created_by")

    readonly_fields = (
        "quotation_number",
        "subtotal_excl_gst",
        "total_gst",
        "grand_total_incl_gst",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Reference Details", {
            "fields": ("quotation_number", "rfq", "vendor", "customer_name")
        }),
        ("Status & Validity", {
            "fields": ("status", "valid_until")
        }),
        ("Pricing Summary", {
            "fields": (
                "subtotal_excl_gst",
                "total_gst",
                "grand_total_incl_gst",
            )
        }),
        ("Audit Information", {
            "fields": ("created_by", "created_at", "updated_at")
        }),
    )

    inlines = [QuotationItemInline]

    actions = ["recalculate_totals"]

    def recalculate_totals(self, request, queryset):
        """
        Admin action to recalculate quotation totals
        """
        for quotation in queryset:
            quotation.calculate_totals()

        self.message_user(request, "Selected quotations recalculated successfully.")

    recalculate_totals.short_description = "Recalculate totals for selected quotations"
