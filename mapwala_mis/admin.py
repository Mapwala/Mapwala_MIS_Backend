from django.contrib import admin
from .models import *
from django.utils.safestring import mark_safe
from django.contrib import messages
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


# ------------------ State ------------------
@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status_badge", "created_at_formatted")
    list_display_links = ("name",)
    search_fields = ("name",)
    list_filter = ("status", "created_at")
    ordering = ("id",)
    readonly_fields = ("created_at", "id_display")

    # Organize form fields
    fieldsets = (
        (
            "State Details",
            {
                "fields": ("id_display", "name", "status"),
                "description": "Enter the official name of the state/region.",
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    # Bulk actions
    actions = ["make_active", "make_inactive"]

    # Custom display methods

    def status_badge(self, obj):
        """Color-coded status badge using mark_safe."""
        colors = {
            "active": "#28a745",  # Green
            "inactive": "#6c757d",  # Gray
        }
        bg_color = colors.get(obj.status, "#000")
        display_text = obj.get_status_display().title()

        # Manually construct safe HTML string
        html = (
            f'<span style="background-color: {bg_color}; color: white; padding: 4px 8px; '
            f'border-radius: 4px; font-weight: bold;">{display_text}</span>'
        )

        return mark_safe(html)

    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    def created_at_formatted(self, obj):
        """Format creation date for readability."""
        return (
            obj.created_at.strftime("%b %d, %Y at %I:%M %p") if obj.created_at else "—"
        )

    created_at_formatted.short_description = "Created At"

    def id_display(self, obj):
        """Show ID in form (read-only)."""
        return obj.id if obj.id else "—"

    id_display.short_description = "ID"

    # Bulk action: Activate selected states
    def make_active(self, request, queryset):
        updated = queryset.update(status="active")
        self.message_user(
            request,
            f"{updated} state(s) successfully marked as active.",
            messages.SUCCESS,
        )

    make_active.short_description = "Mark selected states as Active"

    # Bulk action: Deactivate selected states
    def make_inactive(self, request, queryset):
        updated = queryset.update(status="inactive")
        self.message_user(
            request,
            f"{updated} state(s) successfully marked as inactive.",
            messages.WARNING,
        )

    make_inactive.short_description = "Mark selected states as Inactive"

    # Optional: Prevent saving invalid data (extra safety)
    def save_model(self, request, obj, form, change):
        # Ensure name is title-cased (optional consistency)
        obj.name = obj.name.strip().title()
        super().save_model(request, obj, form, change)


# ------------------ District ------------------
@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("id","name","code","state_link","status_badge","created_at_formatted")
    list_display_links = ("name",)
    search_fields = ("name", "code", "state__name")
    list_filter = ("status", "state", "created_at")
    ordering = ("id",)
    readonly_fields = ("created_at", "id_display")

    # Organize form into logical sections
    fieldsets = (
        (
            "District Details",
            {
                "fields": ("id_display", "name", "code", "state", "status"),
                "description": "Ensure the district code is unique within the selected state.",
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    # Enable bulk actions
    actions = ["make_active", "make_inactive"]

    # --- Custom Display Methods ---

    def state_link(self, obj):
        """Link to the related State's admin change page."""
        if obj.state:
            url = reverse("admin:mapwala_mis_state_change", args=[obj.state.id])
            return mark_safe(f'<a href="{url}"><strong>{obj.state.name}</strong></a>')
        return "—"

    state_link.short_description = "State"
    state_link.admin_order_field = "state__name"

    def status_badge(self, obj):
        """Color-coded status using mark_safe."""
        colors = {
            "active": "#28a745",  # Green
            "inactive": "#6c757d",  # Gray
        }
        bg_color = colors.get(obj.status, "#000")
        display_text = obj.get_status_display().title()
        html = (
            f'<span style="background-color: {bg_color}; color: white; '
            f'padding: 4px 8px; border-radius: 4px; font-weight: bold;">'
            f"{display_text}</span>"
        )
        return mark_safe(html)

    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    def created_at_formatted(self, obj):
        """Human-readable creation timestamp."""
        if obj.created_at:
            return obj.created_at.strftime("%b %d, %Y at %I:%M %p")
        return "—"

    created_at_formatted.short_description = "Created At"

    def id_display(self, obj):
        return obj.id if obj.id else "—"

    id_display.short_description = "ID"

    # --- Bulk Actions ---

    def make_active(self, request, queryset):
        updated = queryset.update(status="active")
        self.message_user(
            request,
            f"{updated} district(s) successfully marked as active.",
            messages.SUCCESS,
        )

    make_active.short_description = "Mark selected districts as Active"

    def make_inactive(self, request, queryset):
        updated = queryset.update(status="inactive")
        self.message_user(
            request,
            f"{updated} district(s) successfully marked as inactive.",
            messages.WARNING,
        )

    make_inactive.short_description = "Mark selected districts as Inactive"

    # --- Optional: Auto-format name on save ---
    def save_model(self, request, obj, form, change):
        obj.name = obj.name.strip().title()
        obj.code = obj.code.strip().upper()
        super().save_model(request, obj, form, change)


# ------------------ Parent Company ------------------
@admin.register(ParentCompany)
class ParentCompanyAdmin(admin.ModelAdmin):
    list_display = ("id","name","email","phone_number_formatted","state_link","district_link","gst_number","pan_number","created_at_formatted","has_all_documents")
    list_display_links = ("name",)
    search_fields = ("name", "phone_number", "email", "gst_number", "pan_number")
    list_filter = ("state", "district", "created_at")
    ordering = ("-id",)

    # Make critical identifiers read-only after creation
    readonly_fields = ("created_at","id_display","gst_document_link","tan_document_link","pan_document_link","account_number_masked")

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
                    "account_number_masked",  # Show masked version
                    "account_number",  # Editable but hidden by default
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
    list_display = ("id","name","email","phone_number_formatted","state_link","district_link","gst_number","pan_number","created_at_formatted","has_all_documents")
    list_display_links = ("name",)
    search_fields = ("name", "phone_number", "email", "gst_number", "pan_number")
    list_filter = ("state", "district", "created_at")
    ordering = ("-id",)
    readonly_fields = ("created_at","id_display","gst_document_link","tan_document_link","pan_document_link","account_number_masked")
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
            "🔒 Sensitive Data (Edit with caution)",
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
    list_display = ("id","name","phone_number","email","state","district","gst_number","pan_number","created_at")
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
    list_display = ("id","partner_name","phone_number","email","state","district","gst_number","pan_number","created_at")
    search_fields = ("partner_name","phone_number","email","gst_number","pan_number")
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
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("id",)


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

    list_filter = (
        "linked_to",
        "state",
        "district",
        "created_at",
    )

    ordering = ("-id",)
    readonly_fields = ("created_at",)

    filter_horizontal = (
        "authorised_states",
        "authorised_districts",
    )

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

    filter_horizontal = (
        "authorised_states",
        "authorised_districts",
    )

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
            {
                "fields": (
                    "authorised_states",
                    "authorised_districts",
                )
            },
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


# ------------------ Device ------------------
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("id_link", "status_badge", "created_by", "created_at_formatted")
    list_filter = ("status", "created_at", "created_by")
    search_fields = ("id", "created_by__username", "created_by__email")
    readonly_fields = ("created_at", "id_display")
    ordering = ("-id",)

    fieldsets = (
        (
            "Device Status",
            {
                "fields": ("status",),
                "description": "Draft: Incomplete configuration. Completed: Ready for production.",
            },
        ),
        (
            "Created Info",
            {
                "fields": ("id_display", "created_by", "created_at"),
            },
        ),
    )

    def id_link(self, obj):
        url = reverse(
            f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk]
        )
        return mark_safe(f'<a href="{url}"><strong>Device-{obj.id}</strong></a>')

    id_link.short_description = "Device ID"
    id_link.admin_order_field = "id"

    def id_display(self, obj):
        return f"Device-{obj.id}"

    id_display.short_description = "Full ID"

    def status_badge(self, obj):
        colors = {"draft": "#ffc107", "completed": "#28a745"}
        return mark_safe(
            f'<span style="background-color:{colors.get(obj.status, "#6c757d")}; '
            f'color:white; padding:4px 8px; border-radius:4px; font-weight:bold;">'
            f"{obj.get_status_display()}</span>"
        )

    status_badge.short_description = "Status"

    def created_at_formatted(self, obj):
        return (
            obj.created_at.strftime("%b %d, %Y at %I:%M %p") if obj.created_at else "—"
        )

    created_at_formatted.short_description = "Created At"


# ------------------ Device Information ------------------
@admin.register(DeviceInformation)
class DeviceInformationAdmin(admin.ModelAdmin):
    list_display = ("device", "make", "model", "mrp", "state_of_supply")
    search_fields = ("make", "model", "device__id")
    list_filter = ("state_of_supply",)
    ordering = ("device__id",)

    fieldsets = (
        ("Device Reference", {"fields": ("device",)}),
        ("Basic Info", {"fields": ("make", "model", "version", "variant")}),
        ("Pricing", {"fields": ("mrp",)}),
        ("Supply Info", {"fields": ("unit_of_measure", "state_of_supply")}),
    )


# ------------------ BOM ------------------
class BOMComponentInline(admin.TabularInline):
    model = BOMComponent
    extra = 0


# ------------------ BOM ------------------
@admin.register(BOM)
class BOMAdmin(admin.ModelAdmin):
    list_display = ("device", "upload_type", "created_at")
    list_filter = ("upload_type", "created_at")
    readonly_fields = ("created_at",)
    inlines = [BOMComponentInline]

    fieldsets = (
        ("Device", {"fields": ("device",)}),
        ("Upload Info", {"fields": ("upload_type", "bom_file")}),
        ("System", {"fields": ("created_at",)}),
    )


# ------------------ BOM Component ------------------
@admin.register(BOMComponent)
class BOMComponentAdmin(admin.ModelAdmin):
    list_display = (
        "bom",
        "identification_mark",
        "part_no",
        "part_make",
        "per_device_quantity",
    )
    search_fields = ("identification_mark", "part_no", "part_make")
    list_filter = ("part_make",)

    fieldsets = (
        ("BOM Reference", {"fields": ("bom",)}),
        (
            "Component Details",
            {
                "fields": (
                    "identification_mark",
                    "description",
                    "designator",
                    "footprint",
                    "volt",
                )
            },
        ),
        (
            "Part Info",
            {"fields": ("part_no", "part_make", "per_device_quantity", "remarks")},
        ),
    )


# ------------------ Enclosure ------------------
@admin.register(Enclosure)
class EnclosureAdmin(admin.ModelAdmin):
    list_display = (
        "device",
        "length",
        "breadth",
        "height",
        "material",
        "color",
        "quantity",
    )

    fieldsets = (
        ("Device", {"fields": ("device",)}),
        ("Dimensions", {"fields": ("length", "breadth", "height")}),
        ("Material Info", {"fields": ("material", "color", "make", "part_number")}),
        ("Quantity", {"fields": ("quantity",)}),
    )


# ------------------ Wire Harness ------------------
class WireConnectorInline(admin.TabularInline):
    model = WireConnector
    extra = 0


# --------------------------- Wire Harness ------------------
@admin.register(WireHarness)
class WireHarnessAdmin(admin.ModelAdmin):
    list_display = ("device", "number_of_wires", "specification", "make", "part_number")
    inlines = [WireConnectorInline]

    fieldsets = (
        ("Device", {"fields": ("device",)}),
        ("Harness Details", {"fields": ("number_of_wires", "specification")}),
        ("Part Info", {"fields": ("make", "part_number")}),
    )


# ------------------ Wire Connector ------------------
@admin.register(WireConnector)
class WireConnectorAdmin(admin.ModelAdmin):
    list_display = ("wire_harness", "connector_name", "number_of_pins", "wire_colors")

    fieldsets = (
        ("Wire Harness", {"fields": ("wire_harness",)}),
        (
            "Connector Info",
            {"fields": ("connector_name", "number_of_pins", "wire_colors")},
        ),
    )


# ------------------ Battery ------------------
@admin.register(Battery)
class BatteryAdmin(admin.ModelAdmin):
    list_display = ("device", "capacity", "make", "part_number")

    fieldsets = (
        ("Device", {"fields": ("device",)}),
        ("Battery Specs", {"fields": ("capacity", "length", "breadth", "height")}),
        ("Part Info", {"fields": ("make", "part_number")}),
    )


# ------------------ SOS Button ------------------
@admin.register(SOSButton)
class SOSButtonAdmin(admin.ModelAdmin):
    list_display = ("device", "total_length", "quantity_per_set", "make", "part_number")

    fieldsets = (
        ("Device", {"fields": ("device",)}),
        ("Button Specs", {"fields": ("total_length", "quantity_per_set")}),
        ("Part Info", {"fields": ("make", "part_number")}),
    )


# ------------------ Sticker ------------------
@admin.register(Sticker)
class StickerAdmin(admin.ModelAdmin):
    list_display = ("device", "name", "length", "breadth", "quantity", "make")

    fieldsets = (
        ("Device", {"fields": ("device",)}),
        ("Sticker Details", {"fields": ("name", "length", "breadth", "quantity")}),
        ("File", {"fields": ("file",)}),
        ("Part Info", {"fields": ("make", "part_number")}),
    )


# ------------------ User Manual ------------------
@admin.register(UserManual)
class UserManualAdmin(admin.ModelAdmin):
    list_display = ("device", "file")

    fieldsets = (
        ("Device", {"fields": ("device",)}),
        ("Manual File", {"fields": ("file",)}),
    )


# ------------------ Accessories ------------------
@admin.register(Accessory)
class AccessoryAdmin(admin.ModelAdmin):
    list_display = ("device", "name", "quantity", "specifications")

    fieldsets = (
        ("Device", {"fields": ("device",)}),
        (
            "Accessory Info",
            {"fields": ("name", "quantity", "specifications", "description")},
        ),
    )


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
                "fields": (
                    "product",
                    "batch",
                    "quantity",
                    "unit_price",
                ),
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
                "fields": (
                    "delivery_date",
                    "delivery_address",
                ),
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
    list_display = ("id","production_type","product","product_category","quantity_added","total_value","supplier_vendor","purchase_date","manufacturing_date","batch","created_at")
    list_filter = ("production_type","product_category","purchase_date","manufacturing_date","supplier_vendor","created_at")
    search_fields = ("id","product__name","supplier_vendor__name","batch__batch_number")
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
    list_display = ("id","order_entry","customer_name","customer_type","product","quantity","grand_total","payment_terms","order_priority","expected_delivery_date","created_at")
    list_filter = ("customer_type","payment_terms","order_priority","expected_delivery_date","created_at")
    search_fields = ("id","order_entry__id","customer_name","contact_person","mobile_no","product__name")
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
    list_display = ("id","order_reference","device_name","assembly_type","quantity","srn_no","delivery_date","status","created_by","created_at")
    list_filter = ("assembly_type", "srn_no", "status", "delivery_date", "created_by")
    search_fields = ("order_reference", "device_name", "created_by__username")
    ordering = ("-created_at",)
    readonly_fields = ("created_by", "created_at")
    inlines = [RFQSelectionInline]
    fieldsets = (
        (
            "STEP 1 — Order Selection (UI Driven)",
            {
                "fields": (
                    "order_reference",
                    "device_name",
                    "assembly_type",
                    "quantity",
                )
            },
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


# # ===================== RFQ SELECTION ADMIN =====================
# @admin.register(RFQSelection)
# class RFQSelectionAdmin(admin.ModelAdmin):
#     list_display = ("rfq", "item_type", "reference")
#     list_filter = ("item_type",)
#     search_fields = ("rfq__order_reference", "reference")
#     fieldsets = (
#         ("RFQ", {"fields": ("rfq",)}),
#         ("Selection Value", {"fields": ("item_type", "reference")}),
#     )


# -------------------- Inlines --------------------
class PurchaseOrderTypeInline(admin.TabularInline):
    model = PurchaseOrderType
    extra = 1
    fields = ("order_type",)
    show_change_link = True


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
    list_display = ("id","order_id","buyer_name","rfq_id","assembly_type","delivery_date","payment_terms","created_by","created_at")
    list_filter = ("assembly_type","payment_terms","delivery_date","created_at")
    search_fields = ("order_id","rfq_id","buyer_name","created_by__username",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    inlines = [PurchaseOrderTypeInline, PurchaseOrderItemInline]
    fieldsets = (
        ("Step 1 — Order Details", {
            "fields": (
                "buyer_name",
                "order_id",
                "rfq_id",
                "assembly_type",
            )
        }),
        ("Step 2 — Vendor & Delivery", {
            "fields": (
                "wastage_percentage",
                "selected_vendor_id",
                "delivery_date",
                "payment_terms",
            )
        }),
        ("System Information", {
            "fields": ("created_by", "created_at")
        }),
    )


# -------------------- Purchase Order Type Admin --------------------
@admin.register(PurchaseOrderType)
class PurchaseOrderTypeAdmin(admin.ModelAdmin):
    list_display = ("purchase_order", "order_type")
    list_filter = ("order_type",)
    search_fields = ("purchase_order__order_id",)

    fieldsets = (
        ("Purchase Order", {
            "fields": ("purchase_order",)
        }),
        ("Order Type", {
            "fields": ("order_type",)
        }),
    )


# -------------------- Purchase Order Item Admin --------------------

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ("purchase_order","item_code","item_type","quantity","vendor_name","unit_price","total_price","delivery_days")

    list_filter = ("item_type",)
    search_fields = ("item_code","vendor_name","purchase_order__order_id")

    fieldsets = (
        ("Purchase Order", {
            "fields": ("purchase_order",)
        }),
        ("Item Details", {
            "fields": (
                "item_code",
                "item_type",
                "quantity",
                "delivery_days",
            )
        }),
        ("Vendor", {
            "fields": ("vendor_id", "vendor_name")
        }),
        ("Pricing", {
            "fields": ("unit_price", "gst_amount", "total_price")
        }),
    )


class MaterialReceiptItemInline(admin.TabularInline):
    model = MaterialReceiptItem
    extra = 1
    fields = ("purchase_order_item", "received_qty", "serial_numbers", "balance_qty")
    readonly_fields = ("balance_qty",)
    autocomplete_fields = ("purchase_order_item",)
    show_change_link = True


@admin.register(MaterialReceiptNote)
class MaterialReceiptNoteAdmin(admin.ModelAdmin):
    list_display = ("id","purchase_order","vendor","inward_type","receipt_date","batch_number","created_at")
    list_filter = ("inward_type", "receipt_date", "vendor")
    search_fields = ("batch_number", "invoice_number", "purchase_order__order_id", "vendor__name")
    autocomplete_fields = ("purchase_order", "vendor")
    readonly_fields = ("created_at",)
    inlines = [MaterialReceiptItemInline]
    fieldsets = (
        ("Order & Vendor", {
            "fields": ("purchase_order", "po_date", "vendor", "inward_type")
        }),
        ("Receipt", {
            "fields": ("receipt_date", "batch_number")
        }),
        ("Documents", {
            "fields": ("invoice_number", "invoice_file", "delivery_challan_number", "challan_file", "eway_bill_number", "eway_bill_file")
        }),
        ("Additional Info", {
            "fields": ("remarks",)
        }),
        ("System", {
            "fields": ("created_by", "created_at")
        }),
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

    readonly_fields = (
        "created_by",
        "created_at",
    )

    fieldsets = (
        (
            "STEP 1: Sales Order Selection",
            {
                "fields": (
                    "sales_order",
                    "order_type",
                )
            },
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
            {
                "fields": (
                    "dispatch_date",
                    "dispatch_remarks",
                )
            },
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
            {
                "fields": (
                    "created_by",
                    "created_at",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """
        Auto-assign created_by on first save
        """
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ---------------------------------------------------
# Inline Formset with validation & auto-calculation
# ---------------------------------------------------
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
                raise ValueError(
                    "Return quantity cannot exceed dispatched quantity."
                )

            # Auto-calculate return_amount
            form.instance.return_amount = (
                Decimal(return_qty) * unit_price
            )

# ---------------------------------------------------
# Inline admin for items
# ---------------------------------------------------
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

# ---------------------------------------------------
# Main admin
# ---------------------------------------------------
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
            {
                "fields": (
                    "total_return_amount",
                    "created_by",
                )
            },
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


