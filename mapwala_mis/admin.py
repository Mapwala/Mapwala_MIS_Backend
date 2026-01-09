from django.contrib import admin
from .models import *


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
    list_display = ("id","name","phone_number","email","state","district","gst_number","pan_number","created_at",)
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
    list_display = ("id","name","phone_number","email","state","district","gst_number","pan_number","created_at",)
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
    list_display = ("id","name","phone_number","email","state","district","gst_number","pan_number","created_at",)
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
    list_display = ("id","partner_name","phone_number","email","state","district","gst_number","pan_number","created_at",)
    search_fields = ("partner_name","phone_number","email","gst_number","pan_number",)
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
    list_display = ("id","name","phone_number","email","linked_to","manufacturer","created_at",)

    search_fields = ("name","phone_number","email","gst_number","pan_number","manufacturer__name",)

    list_filter = ("linked_to","state","district","created_at",)

    ordering = ("-id",)
    readonly_fields = ("created_at",)

    filter_horizontal = (
        "authorised_states",
        "authorised_districts",
    )

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "phone_number", "email", "address")
        }),
        ("Address Location", {
            "fields": ("state", "district")
        }),
        ("Linking Information", {
            "fields": ("linked_to", "manufacturer")
        }),
        ("Authorised Area", {
            "fields": ("authorised_states", "authorised_districts")
        }),
        ("Bank Details", {
            "fields": (
                "bank_name",
                "account_holder_name",
                "account_number",
                "ifsc_code",
            )
        }),
        ("GST Details", {
            "fields": ("gst_number", "gst_document")
        }),
        ("TAN Details", {
            "fields": ("tan_number", "tan_document")
        }),
        ("PAN Details", {
            "fields": ("pan_number", "pan_document")
        }),
        ("System Info", {
            "fields": ("created_at",)
        }),
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

    search_fields = (
        "name",
        "phone_number",
        "email",
        "gst_number",
        "pan_number",
    )

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
        ("Basic Information", {
            "fields": ("name", "phone_number", "email", "address")
        }),
        ("Address Location", {
            "fields": ("state", "district")
        }),
        ("Bank Details", {
            "fields": (
                "bank_name",
                "account_holder_name",
                "account_number",
                "ifsc_code",
            )
        }),
        ("Tax Documents", {
            "fields": (
                "gst_number", "gst_document",
                "tan_number", "tan_document",
                "pan_number", "pan_document",
            )
        }),
        ("Business Linking", {
            "fields": ("linked_to", "manufacturer", "distributor")
        }),
        ("Authorised Area", {
            "fields": (
                "authorised_states",
                "authorised_districts",
            )
        }),
        ("System Info", {
            "fields": ("created_at",)
        }),
    )


# ------------------ Product ------------------

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("product_id", "created_at")
    search_fields = ("product_id",)
    ordering = ("product_id",)
    readonly_fields = ("created_at",)


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
        ("Party Information", {
            "fields": (
                "party_type",
                "b2b_partner",
                "b2c_customer",
                "dealer",
                "distributor",
            )
        }),
        ("Product & Pricing", {
            "fields": (
                "product",
                "selling_price",
                "discount_percent",
                "quantity",
                "shipping_charges",
                "grand_total",
            )
        }),
        ("Payment & Delivery", {
            "fields": (
                "payment_terms",
                "delivery_date",
                "delivery_address",
                "state",
            )
        }),
        ("Contact Information", {
            "fields": (
                "contact_person_name",
                "mobile_no",
                "gstn",
            )
        }),
        ("System Info", {
            "fields": ("created_at",)
        }),
    )



# ------------------ Device ------------------

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "created_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "created_by__username")
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Device Status", {"fields": ("status",)}),
        ("Created Info", {"fields": ("created_by", "created_at")}),
    )


@admin.register(DeviceInformation)
class DeviceInformationAdmin(admin.ModelAdmin):
    list_display = ("device", "make", "model", "mrp", "state_of_supply")
    search_fields = ("make", "model", "device__id")

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


@admin.register(BOMComponent)
class BOMComponentAdmin(admin.ModelAdmin):
    list_display = ("bom", "identification_mark", "part_no", "part_make", "per_device_quantity")
    search_fields = ("identification_mark", "part_no", "part_make")
    list_filter = ("part_make",)

    fieldsets = (
        ("BOM Reference", {"fields": ("bom",)}),
        ("Component Details", {"fields": (
            "identification_mark", "description", "designator", "footprint", "volt"
        )}),
        ("Part Info", {"fields": ("part_no", "part_make", "per_device_quantity", "remarks")}),
    )


# ------------------ Enclosure ------------------

@admin.register(Enclosure)
class EnclosureAdmin(admin.ModelAdmin):
    list_display = ("device", "length", "breadth", "height", "material", "color", "quantity")

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


@admin.register(WireHarness)
class WireHarnessAdmin(admin.ModelAdmin):
    list_display = ("device", "number_of_wires", "specification", "make", "part_number")
    inlines = [WireConnectorInline]

    fieldsets = (
        ("Device", {"fields": ("device",)}),
        ("Harness Details", {"fields": ("number_of_wires", "specification")}),
        ("Part Info", {"fields": ("make", "part_number")}),
    )


@admin.register(WireConnector)
class WireConnectorAdmin(admin.ModelAdmin):
    list_display = ("wire_harness", "connector_name", "number_of_pins", "wire_colors")

    fieldsets = (
        ("Wire Harness", {"fields": ("wire_harness",)}),
        ("Connector Info", {"fields": ("connector_name", "number_of_pins", "wire_colors")}),
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
        ("Accessory Info", {"fields": ("name", "quantity", "specifications", "description")}),
    )