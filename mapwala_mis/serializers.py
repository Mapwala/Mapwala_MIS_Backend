# mapwala_mis/serializers.py
import re
from django.core.validators import RegexValidator
import json
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from .utils import format_order_id, get_media_path
from django.db.models import FileField
from .models import (
    UserProfile,
    State,
    District,
    ProductCategory,
    SupplierVendor,
    Product,
    ProductionOrder,
    OrderBatch,
    OrderEntry,
    OrderEntryMakeToOrder,
    RequestForQuote,
    PurchaseOrder,
    MaterialReceiptNote,
    Dispatch,
    PostDispatchReturn,
    B2CCustomer,
    B2BPartner,
    Distributor,
    Dealer,
    ProformaInvoice,
    DeviceInformation,
    BOM,
    BOMComponent,
    Enclosure,
    WireHarness,
    WireConnector,
    Battery,
    SOSButton,
    Sticker,
    UserManual,
    Accessory,
    AccountRegistration,
    QCInspectorRegistration,
    PurchaseDepartmentRegistration,
    StoreManagerRegistration,
    RepairTechnicianRegistration,
    Vendor,
    ParentCompany,
    OrderProduct,
    SalesOrder,
    StoreTransfer,
    DebitNote,
    RejectedItem,
    CreditNote,
    ReturnRequest,
    RepairRecord,
    Device,
    SelfOrder,
    RFQSelection,
    QuotationItem,
    Quotation,
    ProformaInvoice,
    Manufacturer,
    DeviceInventory,
    B2BOrder,
)

User = get_user_model()


# ---------------- File Size Validator ----------------
def validate_file_size(file):
    if not file:
        return
    # Use a dedicated custom setting, fallback to 5MB
    max_size = getattr(settings, "MAX_UPLOAD_FILE_SIZE", 5 * 1024 * 1024)
    if file.size > max_size:
        raise serializers.ValidationError(
            f"File size must be less than or equal to {max_size // (1024 * 1024)} MB."
        )


class BaseSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        for field in instance._meta.concrete_fields:
            if isinstance(field, FileField):
                file_obj = getattr(instance, field.name)
                data[field.name] = get_media_path(file_obj)
        return data

    def _validate_state_district(self, data):
        instance = getattr(self, "instance", None)
        state = data.get("state") or getattr(instance, "state", None)
        district = data.get("district") or getattr(instance, "district", None)

        if state and district and district.state_id != state.id:
            raise serializers.ValidationError(
                {"district": "Selected district does not belong to selected state."}
            )


class UserSerializer(serializers.ModelSerializer):
    accepted_terms = serializers.BooleanField(
        source="profile.accepted_terms", read_only=True
    )

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_active", "accepted_terms"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    accepted_terms = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "email",
            "accepted_terms",
        ]

    def validate_username(self, value):
        if not re.fullmatch(r"\d{10,15}", value):
            raise serializers.ValidationError(
                "Username must be a valid phone number (10–15 digits)."
            )

        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "This phone number is already registered."
            )

        return value

    def create(self, validated_data):
        accepted_terms = validated_data.pop("accepted_terms")

        user = User.objects.create_user(**validated_data)

        UserProfile.objects.create(user=user, accepted_terms=accepted_terms)

        return user


# ---------------- Login ----------------
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        validators=[
            RegexValidator(
                regex=r"^\d{10}$",
                message="Username must be a valid 10-digit mobile number.",
            )
        ]
    )
    password = serializers.CharField(write_only=True)
    accepted_terms = serializers.BooleanField()

    def validate_password(self, value):
        errors = []

        if len(value) < 8:
            errors.append("Password must be at least 8 characters long.")

        if not re.search(r"[A-Z]", value):
            errors.append("Password must contain at least one uppercase letter [A-Z].")

        if not re.search(r"[0-9]", value):
            errors.append("Password must contain at least one digit [0-9].")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-\[\]\\/\'\`~+=;]", value):
            errors.append("Password must contain at least one special character.")

        if errors:
            raise serializers.ValidationError(errors)

        return value

    def validate(self, data):
        if not data.get("accepted_terms"):
            raise serializers.ValidationError(
                {"accepted_terms": "Please accept the terms and conditions to continue"}
            )

        user = authenticate(
            username=data["username"],
            password=data["password"],
        )
        if user is None:
            raise serializers.ValidationError(
                {"credentials": "Invalid username or password"}
            )

        data["user"] = user
        return data


# ---------------- Location Models ----------------
class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ["id", "name", "status"]


# ---------------- Location Models ----------------
class DistrictSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source="state.name", read_only=True)

    class Meta:
        model = District
        fields = ["id", "name", "code", "state", "state_name", "status"]


# ---------------- Company Models ----------------
class ParentCompanySerializer(BaseSerializer):
    class Meta:
        model = ParentCompany
        fields = "__all__"

    def validate(self, data):
        self._validate_state_district(data)
        return data


# ---------------- Vendor ----------------
class VendorSerializer(BaseSerializer):
    class Meta:
        model = Vendor
        exclude = ("user",)

    def validate(self, data):
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError(
                "Request context is required for vendor validation."
            )
        user = request.user
        instance = getattr(self, "instance", None)

        # State/district check via helper
        self._validate_state_district(data)

        gst_number = data.get("gst_number") or getattr(instance, "gst_number", None)

        if gst_number:
            queryset = Vendor.objects.filter(user=user, gst_number=gst_number)
            if instance:
                queryset = queryset.exclude(id=instance.id)
            if queryset.exists():
                raise serializers.ValidationError(
                    {
                        "gst_number": (
                            "Vendor with this GST number already exists for this user."
                        )
                    }
                )

        return data


class B2CCustomerSerializer(BaseSerializer):
    class Meta:
        model = B2CCustomer
        fields = [
            "id",
            "name",
            "phone_number",
            "email",
            "address",
            "state",
            "district",
            "bank_name",
            "account_holder_name",
            "account_number",
            "ifsc_code",
            "gst_number",
            "gst_document",
            "tan_number",
            "tan_document",
            "pan_number",
            "pan_document",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, data):
        self._validate_state_district(data)
        return data


# ---------------- B2B Partner Registration ----------------
class B2BPartnerSerializer(BaseSerializer):
    class Meta:
        model = B2BPartner
        fields = [
            "id",
            "partner_name",
            "phone_number",
            "email",
            "address",
            "state",
            "district",
            "bank_name",
            "account_holder_name",
            "account_number",
            "ifsc_code",
            "gst_number",
            "gst_document",
            "tan_number",
            "tan_document",
            "pan_number",
            "pan_document",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, data):
        self._validate_state_district(data)
        return data


class LinkedToChoicesSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()


class ManufacturerSerializer(BaseSerializer):

    class Meta:
        model = Manufacturer
        fields = "__all__"
        read_only_fields = ["id", "created_at", "created_by"]
        extra_kwargs = {
            "self_certified_applicant": {"required": False},
            "authorization_letter": {"required": False},
            "pan_card": {"required": False},
            "gst_certificate": {"required": False},
            "technical_onboarding_request_letter": {"required": False},
            "tac_document": {"required": False},
        }

    def validate_applicant_mobile(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Mobile number must contain digits only.")
        if len(value) < 10:
            raise serializers.ValidationError(
                "Mobile number must be at least 10 digits."
            )
        return value

    def validate_company_gst_no(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Invalid GST number.")
        return value

    def validate_company_pan_no(self, value):
        if len(value) != 10:
            raise serializers.ValidationError("PAN number must be 10 characters.")
        return value.upper()


# ---------------- Distributor Registration ----------------
class DistributorRegistrationSerializer(BaseSerializer):
    authorised_states = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.all(), many=True
    )
    authorised_districts = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(), many=True
    )

    class Meta:
        model = Distributor
        fields = "__all__"

    def validate(self, data):
        instance = getattr(self, "instance", None)

        # State/district check via helper
        self._validate_state_district(data)

        # Linked-to / manufacturer validation
        linked_to = data.get("linked_to") or getattr(instance, "linked_to", None)
        manufacturer = data.get("manufacturer") or getattr(
            instance, "manufacturer", None
        )

        if linked_to == "manufacturer" and not manufacturer:
            raise serializers.ValidationError(
                {"manufacturer": "Manufacturer is required."}
            )

        # M2M validation — PATCH-safe using None sentinel
        authorised_states = data.get("authorised_states")
        if authorised_states is None:
            authorised_states = (
                list(instance.authorised_states.all()) if instance else []
            )

        authorised_districts = data.get("authorised_districts")
        if authorised_districts is None:
            authorised_districts = (
                list(instance.authorised_districts.all()) if instance else []
            )

        state_ids = {s.id for s in authorised_states}
        for d in authorised_districts:
            if d.state_id not in state_ids:
                raise serializers.ValidationError(
                    {"authorised_districts": "District not in authorised states."}
                )

        return data

    @transaction.atomic
    def create(self, validated_data):
        states = validated_data.pop("authorised_states")
        districts = validated_data.pop("authorised_districts")
        distributor = Distributor.objects.create(**validated_data)
        distributor.authorised_states.set(states)
        distributor.authorised_districts.set(districts)
        return distributor

    @transaction.atomic
    def update(self, instance, validated_data):
        states = validated_data.pop("authorised_states", None)
        districts = validated_data.pop("authorised_districts", None)

        instance = super().update(instance, validated_data)

        if states is not None:
            instance.authorised_states.set(states)
        if districts is not None:
            instance.authorised_districts.set(districts)

        return instance


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "product_id", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_product_id(self, value):
        if not value.strip():
            raise serializers.ValidationError("Product ID cannot be empty.")

        if Product.objects.filter(product_id=value).exists():
            raise serializers.ValidationError("Product with this ID already exists.")

        return value


class ProductDropdownSerializer(serializers.ModelSerializer):
    value = serializers.IntegerField(source="id")
    label = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["value", "label"]

    def get_label(self, obj):
        return str(obj)


# ---------------- Dealer Registration ----------------
class DealerRegistrationSerializer(BaseSerializer):
    authorised_states = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.all(),
        many=True,
        required=False,
    )
    authorised_districts = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Dealer
        fields = [
            "id",
            "name",
            "phone_number",
            "email",
            "address",
            "state",
            "district",
            "bank_name",
            "account_holder_name",
            "account_number",
            "ifsc_code",
            "gst_number",
            "gst_document",
            "tan_number",
            "tan_document",
            "pan_number",
            "pan_document",
            "linked_to",
            "manufacturer",
            "distributor",
            "authorised_states",
            "authorised_districts",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, data):
        instance = getattr(self, "instance", None)
        # State/district check via helper
        self._validate_state_district(data)
        linked_to = data.get("linked_to") or getattr(instance, "linked_to", None)
        manufacturer = data.get("manufacturer", getattr(instance, "manufacturer", None))
        distributor = data.get("distributor", getattr(instance, "distributor", None))

        if linked_to == "manufacturer":
            if not manufacturer:
                raise serializers.ValidationError(
                    {"manufacturer": "Manufacturer is required."}
                )
            data["distributor"] = None

        elif linked_to == "distributor":
            if not distributor:
                raise serializers.ValidationError(
                    {"distributor": "Distributor is required."}
                )
            data["manufacturer"] = None

        authorised_states = data.get("authorised_states")
        if authorised_states is None:
            authorised_states = (
                list(instance.authorised_states.all()) if instance else []
            )

        authorised_districts = data.get("authorised_districts")
        if authorised_districts is None:
            authorised_districts = (
                list(instance.authorised_districts.all()) if instance else []
            )

        state_ids = {s.id for s in authorised_states}
        for d in authorised_districts:
            if d.state_id not in state_ids:
                raise serializers.ValidationError(
                    {
                        "authorised_districts": (
                            f"District '{d.name}' does not belong to "
                            "selected authorised states."
                        )
                    }
                )

        return data

    @transaction.atomic
    def create(self, validated_data):
        states = validated_data.pop("authorised_states", [])
        districts = validated_data.pop("authorised_districts", [])
        dealer = Dealer.objects.create(**validated_data)
        dealer.authorised_states.set(states)
        dealer.authorised_districts.set(districts)
        return dealer

    @transaction.atomic
    def update(self, instance, validated_data):
        states = validated_data.pop("authorised_states", None)
        districts = validated_data.pop("authorised_districts", None)

        # Update all scalar fields via super()
        instance = super().update(instance, validated_data)

        if states is not None:
            instance.authorised_states.set(states)
        if districts is not None:
            instance.authorised_districts.set(districts)

        return instance


# ---------------- Proforma Invoice ----------------
class ProformaInvoiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProformaInvoice
        fields = "__all__"

    def validate(self, data):
        party_type = data["party_type"]

        party_fields = {
            "b2b": data.get("b2b_partner"),
            "b2c": data.get("b2c_customer"),
            "dealer": data.get("dealer"),
            "distributor": data.get("distributor"),
        }

        # ✅ Ensure selected party exists
        if not party_fields.get(party_type):
            raise serializers.ValidationError(
                {"party": f"{party_type.upper()} must be selected"}
            )

        # ✅ Ensure only ONE party is filled
        for key, value in party_fields.items():
            if key != party_type and value:
                raise serializers.ValidationError({key: "This field must be empty"})

        return data


# ---------------- STEP 1 ----------------
class DeviceInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceInformation
        exclude = ["device"]


# ---------------- STEP 2 ----------------
class BOMSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOM
        exclude = ["device", "created_at"]

    def validate(self, data):
        upload_type = data["upload_type"]
        bom_file = data.get("bom_file")

        if upload_type == "bulk" and not bom_file:
            raise serializers.ValidationError(
                {"bom_file": "Excel file required for bulk upload"}
            )

        if upload_type == "individual" and bom_file:
            raise serializers.ValidationError(
                {"bom_file": "Do not upload Excel file for individual entry"}
            )

        return data


# ---------------- STEP 3 ----------------
class BOMComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOMComponent
        exclude = ["bom", "created_at"]


# ---------------- STEP 4 ----------------
class EnclosureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enclosure
        exclude = ["device"]


# ---------------- STEP 5 ----------------
class WireConnectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = WireConnector
        exclude = ["wire_harness"]


# ---------------- STEP 5 ----------------
class WireHarnessSerializer(serializers.ModelSerializer):
    connectors = WireConnectorSerializer(many=True)

    class Meta:
        model = WireHarness
        exclude = ["device"]

    def create(self, validated_data):
        connectors = validated_data.pop("connectors")
        device = validated_data.pop("device")

        harness = WireHarness.objects.create(device=device, **validated_data)

        for connector in connectors:
            WireConnector.objects.create(wire_harness=harness, **connector)

        return harness


# ---------------- STEP 6 ----------------
class BatterySerializer(serializers.ModelSerializer):
    class Meta:
        model = Battery
        exclude = ["device"]


# ---------------- STEP 7 ----------------
class SOSButtonSerializer(serializers.ModelSerializer):
    class Meta:
        model = SOSButton
        exclude = ["device"]


# ---------------- STEP 8 ----------------
class StickerSerializer(BaseSerializer):

    class Meta:
        model = Sticker
        exclude = ["device"]
        extra_kwargs = {
            "file": {
                "validators": [validate_file_size],
            },
        }


# ---------------- STEP 9 ----------------
class UserManualSerializer(BaseSerializer):

    class Meta:
        model = UserManual
        exclude = ["device"]
        extra_kwargs = {
            "file": {
                "validators": [validate_file_size],
            },
        }


# ---------------- STEP 10 ----------------
class AccessorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Accessory
        exclude = ["device"]


# ============================================================
# DEVICE LIST & DETAIL SERIALIZERS
# ============================================================
class DeviceListSerializer(serializers.ModelSerializer):
    device_id = serializers.SerializerMethodField()
    name = serializers.CharField(source="info.make", read_only=True)
    model = serializers.CharField(source="info.model", read_only=True)
    updated = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = ["device_id", "name", "model", "status", "updated"]

    def get_device_id(self, obj):
        return f"DEV-{obj.id:04d}"

    def get_updated(self, obj):
        return obj.created_at.strftime("%Y-%m-%d") if obj.created_at else None


class EnclosureDetailSerializer(serializers.ModelSerializer):
    """Enclosure details for device view"""

    dimensions = serializers.SerializerMethodField()

    class Meta:
        model = Enclosure
        fields = ["dimensions", "color", "material", "quantity"]
        read_only_fields = fields

    def get_dimensions(self, obj):
        """Format dimensions as 'L × B × H mm'"""
        return f"{obj.length} × {obj.breadth} × {obj.height} mm"


class WireConnectorDetailSerializer(serializers.ModelSerializer):
    """Individual wire connector details"""

    class Meta:
        model = WireConnector
        fields = ["connector_name", "number_of_pins", "wire_colors"]
        read_only_fields = fields


class WireHarnessDetailSerializer(serializers.ModelSerializer):
    connectors = WireConnectorDetailSerializer(many=True, read_only=True)
    color = serializers.SerializerMethodField()
    length = serializers.SerializerMethodField()
    pin_type = serializers.SerializerMethodField()
    no_of_connectors = serializers.SerializerMethodField()

    class Meta:
        model = WireHarness
        fields = [
            "number_of_wires",
            "color",
            "length",
            "pin_type",
            "no_of_connectors",
            "connectors",
        ]
        read_only_fields = fields

    def _parse_specification(self, obj):
        """
        Expected specification format example:
        'Color: Multicolor, Length: 220 mm, Pin type: 4 pin'
        """
        result = {}
        if not obj.specification:
            return result

        parts = [p.strip() for p in obj.specification.split(",")]
        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                result[key.strip().lower()] = value.strip()
        return result

    def get_color(self, obj):
        return self._parse_specification(obj).get("color")

    def get_length(self, obj):
        return self._parse_specification(obj).get("length")

    def get_pin_type(self, obj):
        return self._parse_specification(obj).get("pin type")

    def get_no_of_connectors(self, obj):
        return obj.connectors.count()


class BatteryDetailSerializer(serializers.ModelSerializer):
    """Battery details for device view"""

    dimensions = serializers.SerializerMethodField()

    class Meta:
        model = Battery
        fields = ["capacity", "dimensions"]
        read_only_fields = fields

    def get_dimensions(self, obj):
        return f"{obj.length} × {obj.breadth} × {obj.height} mm"


class SOSButtonDetailSerializer(serializers.ModelSerializer):
    """SOS Button details for device view"""

    class Meta:
        model = SOSButton
        fields = ["total_length", "quantity_per_set"]
        read_only_fields = fields


class StickerDetailSerializer(serializers.ModelSerializer):
    dimensions = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Sticker
        fields = [
            "name",
            "dimensions",
            "quantity",
            "file_name",
            "file_url",
        ]
        read_only_fields = fields

    def get_dimensions(self, obj):
        return f"{obj.length} × {obj.breadth} mm"

    def get_file_name(self, obj):
        if obj.file:
            import os

            return os.path.basename(obj.file.name)
        return None

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class BOMDetailSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    bom_file = serializers.SerializerMethodField()

    class Meta:
        model = BOM
        fields = ["upload_type", "items", "bom_file"]
        read_only_fields = fields

    def get_bom_file(self, obj):
        if obj.bom_file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.bom_file.url)
            return obj.bom_file.url
        return None

    def get_items(self, obj):
        components = obj.components.all()
        items_list = []
        for idx, component in enumerate(components, 1):
            items_list.append(
                {
                    "sr": idx,
                    "item": component.description,
                    "type": (
                        "Bulk upload"
                        if obj.upload_type == "bulk"
                        else "Individually purchase"
                    ),
                    "qty": component.per_device_quantity,
                }
            )
        return items_list


class UserManualDetailSerializer(serializers.ModelSerializer):
    file_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = UserManual
        fields = ["file_name", "file_url"]
        read_only_fields = fields

    def get_file_name(self, obj):
        if obj.file:
            import os
            return os.path.basename(obj.file.name)
        return None

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class AccessoryDetailSerializer(serializers.ModelSerializer):
    """Accessory details"""

    class Meta:
        model = Accessory
        fields = ["name", "description", "quantity", "specifications"]
        read_only_fields = fields


class DeviceDetailSerializer(serializers.ModelSerializer):
    device_id = serializers.SerializerMethodField()
    name = serializers.CharField(source="info.make", read_only=True)
    model = serializers.CharField(source="info.model", read_only=True)
    created_date = serializers.SerializerMethodField()

    info = DeviceInformationSerializer(read_only=True)
    bom = BOMDetailSerializer(read_only=True)
    enclosure = EnclosureDetailSerializer(read_only=True)
    wire_harness = WireHarnessDetailSerializer(source="wireharness", read_only=True)
    battery = BatteryDetailSerializer(read_only=True)
    sos_button = SOSButtonDetailSerializer(source="sosbutton", read_only=True)
    stickers = StickerDetailSerializer(source="sticker_set", many=True, read_only=True)
    user_manual = UserManualDetailSerializer(source="usermanual", read_only=True)
    accessories = AccessoryDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Device
        fields = [
            "device_id",
            "id",
            "name",
            "model",
            "status",
            "created_date",
            "info",
            "bom",
            "enclosure",
            "wire_harness",
            "battery",
            "sos_button",
            "stickers",
            "user_manual",
            "accessories",
        ]
        read_only_fields = fields

    def get_device_id(self, obj):
        return f"DEV-{obj.id:04d}"

    def get_created_date(self, obj):
        return obj.created_at.strftime("%Y-%m-%d") if obj.created_at else None


# ──────────────────────────────────────────────
# ORDER ENTRY
# ──────────────────────────────────────────────

class OrderEntryStep1Serializer(serializers.ModelSerializer):
    class Meta:
        model = OrderEntry
        fields = ["order_type", "production_type", "assembly_type"]

    def validate(self, data):
        # Safe .get() — avoids KeyError if order_type is absent in partial update
        if data.get("order_type") == "production" and not data.get("production_type"):
            raise serializers.ValidationError(
                {"production_type": "Required for production order."}
            )
        return data


class OrderEntryReadSerializer(serializers.ModelSerializer):
    """Used for list / retrieve only — all fields are read-only."""

    class Meta:
        model = OrderEntry
        fields = [
            "id",
            "order_type",
            "production_type",
            "assembly_type",
            "is_step1_complete",
            "is_step2_complete",
            "created_at",
        ]
        read_only_fields = (
            "id",
            "order_type",
            "production_type",
            "assembly_type",
            "is_step1_complete",
            "is_step2_complete",
            "created_at",
        )

# ──────────────────────────────────────────────
# ORDER PRODUCT
# ──────────────────────────────────────────────

class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = ["id", "name"]


# ──────────────────────────────────────────────
# ORDER BATCH
# ──────────────────────────────────────────────


class OrderBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderBatch
        fields = ["id", "product", "batch_number", "available_stock"]


# ──────────────────────────────────────────────
# SALES ORDER — WRITE
# ──────────────────────────────────────────────


class SalesOrderCreateSerializer(serializers.ModelSerializer):
    # required=False — PATCH requests don't need to send these
    product_device_model = serializers.CharField(write_only=True, required=False)
    batch_number = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = SalesOrder
        exclude = ("product", "batch")

    def validate(self, data):
        product_name = data.pop("product_device_model", None)
        batch_number = data.pop("batch_number", None)

        if product_name is not None or batch_number is not None:
            instance = self.instance 
            if product_name is None and instance:
                product_name = instance.product.name
            if batch_number is None and instance:
                batch_number = instance.batch.batch_number

            # Both must be present to resolve (either from request or from instance)
            if not product_name or not batch_number:
                raise serializers.ValidationError(
                    {
                        "product_device_model": "Both product and batch_number are required together."
                    }
                )

            try:
                product = OrderProduct.objects.get(name=product_name)
            except OrderProduct.DoesNotExist:
                raise serializers.ValidationError(
                    {"product_device_model": "Invalid product / device model."}
                )

            try:
                batch = OrderBatch.objects.get(
                    product=product, batch_number=batch_number
                )
            except OrderBatch.DoesNotExist:
                raise serializers.ValidationError(
                    {"batch_number": "Invalid batch for selected product."}
                )

            data["product"] = product
            data["batch"] = batch

        # Stock check — only when quantity is being changed
        # Use incoming quantity or fall back to instance quantity
        instance = self.instance
        quantity = data.get("quantity", instance.quantity if instance else None)
        batch = data.get("batch", instance.batch if instance else None)

        if quantity is not None and batch is not None:
            # On update, restore the instance's own quantity before checking
            # (those units are being "released" back to stock during update)
            effective_stock = batch.available_stock
            if instance and instance.batch == batch:
                effective_stock += instance.quantity  # units being returned

            if quantity > effective_stock:
                raise serializers.ValidationError(
                    {"quantity": f"Only {effective_stock} units available."}
                )

        if instance:
            merged = {
                "quantity": data.get("quantity", instance.quantity),
                "unit_price": data.get("unit_price", instance.unit_price),
                "discount_percent": data.get(
                    "discount_percent", instance.discount_percent
                ),
                "gst_percent": data.get("gst_percent", instance.gst_percent),
                "shipping_charges": data.get(
                    "shipping_charges", instance.shipping_charges
                ),
                "product": data.get("product", instance.product),
                "batch": data.get("batch", instance.batch),
            }
        else:
            merged = data

        if "grand_total" in data:
            calculated = SalesOrder(**merged).calculate_grand_total()
            if calculated != data["grand_total"]:
                raise serializers.ValidationError(
                    {
                        "grand_total": (
                            f"Grand total mismatch. "
                            f"Backend calculated: {calculated}, "
                            f"Frontend sent: {data['grand_total']}."
                        )
                    }
                )

        return data


# ──────────────────────────────────────────────
# SALES ORDER — READ
# ──────────────────────────────────────────────


class SalesOrderReadSerializer(serializers.ModelSerializer):
    product = OrderProductSerializer(read_only=True)
    batch = OrderBatchSerializer(read_only=True)

    class Meta:
        model = SalesOrder
        fields = "__all__"


class SupplierVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierVendor
        fields = ["id", "name"]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Name cannot be empty.")

        queryset = SupplierVendor.objects.filter(name__iexact=value)

        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError(
                "Supplier/Vendor with this name already exists."
            )

        return value


# ──────────────────────────────────────────────
# PRODUCTION ORDER — WRITE
# ──────────────────────────────────────────────
class ProductionOrderCreateSerializer(serializers.ModelSerializer):
    # required=False — PATCH requests don't need to send these
    product_device_model = serializers.CharField(write_only=True, required=False)
    batch_number = serializers.CharField(write_only=True, required=False)
    supplier_vendor_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = ProductionOrder
        exclude = ("product", "batch", "supplier_vendor")

    def validate(self, data):
        instance = self.instance  # None on CREATE, ProductionOrder on UPDATE/PATCH

        product_name = data.pop("product_device_model", None)
        batch_number = data.pop("batch_number", None)
        supplier_vendor_id = data.pop("supplier_vendor_id", None)

        # ── Resolve product ──────────────────────────────────────
        if product_name is not None:
            try:
                product = OrderProduct.objects.get(name=product_name)
            except OrderProduct.DoesNotExist:
                raise serializers.ValidationError(
                    {"product_device_model": "Invalid product / device model."}
                )
            data["product"] = product
        elif instance:
            product = instance.product  # keep existing — not reassigned to data
        else:
            raise serializers.ValidationError(
                {"product_device_model": "This field is required."}
            )

        # ── Resolve supplier / vendor ────────────────────────────
        if supplier_vendor_id is not None:
            try:
                supplier = SupplierVendor.objects.get(id=supplier_vendor_id)
            except SupplierVendor.DoesNotExist:
                raise serializers.ValidationError(
                    {"supplier_vendor_id": "Invalid supplier / vendor ID."}
                )
            data["supplier_vendor"] = supplier
        elif not instance:
            raise serializers.ValidationError(
                {"supplier_vendor_id": "This field is required."}
            )

        # ── Resolve batch ────────────────────────────────────────
        if batch_number is not None:
            batch, _ = OrderBatch.objects.get_or_create(
                product=product,
                batch_number=batch_number,
                defaults={"available_stock": 0},
            )
            data["batch"] = batch
        elif not instance:
            raise serializers.ValidationError(
                {"batch_number": "This field is required."}
            )

        # ── Total value check ────────────────────────────────────
        # Only validate when at least one pricing field is being changed
        quantity_added = data.get(
            "quantity_added", instance.quantity_added if instance else None
        )
        unit_price = data.get("unit_price", instance.unit_price if instance else None)
        total_value = data.get(
            "total_value", instance.total_value if instance else None
        )

        if "quantity_added" in data or "unit_price" in data or "total_value" in data:
            calculated = quantity_added * unit_price
            if calculated != total_value:
                raise serializers.ValidationError(
                    {
                        "total_value": (
                            f"Total value mismatch. "
                            f"Backend calculated: {calculated}, "
                            f"Frontend sent: {total_value}."
                        )
                    }
                )

        return data


# ──────────────────────────────────────────────
# PRODUCTION ORDER — READ
# ──────────────────────────────────────────────


class ProductionOrderReadSerializer(serializers.ModelSerializer):
    product = OrderProductSerializer(read_only=True)
    batch = OrderBatchSerializer(read_only=True)
    supplier_vendor = serializers.StringRelatedField()

    class Meta:
        model = ProductionOrder
        fields = "__all__"


# ──────────────────────────────────────────────
# ORDER ENTRY — STEP 2 (MAKE TO ORDER)
# ──────────────────────────────────────────────

class OrderEntryStep2MakeToOrderSerializer(serializers.ModelSerializer):
    product_device_model = serializers.CharField(write_only=True)

    class Meta:
        model = OrderEntryMakeToOrder
        exclude = ("order_entry", "product")

    def validate(self, data):
        # Resolve product
        try:
            product = OrderProduct.objects.get(name=data.pop("product_device_model"))
        except OrderProduct.DoesNotExist:
            raise serializers.ValidationError(
                {"product_device_model": "Invalid Product / Device Model."}
            )

        data["product"] = product

        # Grand total calculation
        base = data["quantity"] * data["unit_price"]
        discount = (base * data["discount_percent"]) / Decimal("100")
        taxable = base - discount
        gst = (taxable * data["gst_percent"]) / Decimal("100")
        calculated_total = taxable + gst + data["shipping_charges"]

        if calculated_total != data["grand_total"]:
            raise serializers.ValidationError(
                {
                    "grand_total": f"Grand total mismatch with backend calculation. Backend calculated: {calculated_total} and frontend calculated: {data['grand_total']}."
                }
            )

        # Advance payment cannot exceed grand total
        if data["advance_payment"] > data["grand_total"]:
            raise serializers.ValidationError(
                {"advance_payment": "Advance payment cannot exceed grand total."}
            )

        return data

RFQ_SERVICES = [
    {
        "key": "pcb_assembly",
        "label": "PCB Assembly",
        "description": "Complete PCB manufacturing and component assembly\nSMT/THT component placement and soldering",
    },
    {
        "key": "quality_check",
        "label": "Quality Check",
        "description": "Comprehensive testing and quality assurance\nFunctional testing, AOI, and final inspection",
    },
    {
        "key": "device_assembly",
        "label": "Device Assembly",
        "description": "Final device assembly and packaging\nEnclosure fitting, wire harness, and final testing",
    },
]

def _dedupe_preserve_order(values):
    seen = set()
    deduped = []
    for item in values:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


class RFQStep1Serializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(write_only=True)

    quote_types = serializers.ListField(
        child=serializers.ChoiceField(
            choices=[c[0] for c in RequestForQuote.QUOTE_TYPE_CHOICES]
        ),
        min_length=1,
        error_messages={"min_length": "At least one quote type must be selected."},
    )

    assembly_type = serializers.ListField(
        child=serializers.ChoiceField(
            choices=[c[0] for c in RequestForQuote.ASSEMBLY_TYPE_CHOICES]
        ),
        min_length=1,
        error_messages={"min_length": "At least one assembly type must be selected."},
    )

    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = RequestForQuote
        fields = ["order_id", "quote_types", "assembly_type", "quantity"]

    def validate_order_id(self, value):
        try:
            order = OrderEntry.objects.select_related().get(id=value)
        except OrderEntry.DoesNotExist:
            raise serializers.ValidationError(f"Order with ID {value} does not exist.")

        if order.production_type != "make_to_order":
            raise serializers.ValidationError(
                "Only Make-to-Order entries can have an RFQ."
            )

        if not order.is_step2_complete:
            raise serializers.ValidationError(
                "Selected order must be confirmed before creating an RFQ."
            )

        if not hasattr(order, "make_to_order"):
            raise serializers.ValidationError(
                "Selected order has no Make-to-Order details. Complete Step 2 first."
            )

        return value

    def validate_quote_types(self, value):
        return _dedupe_preserve_order(value)

    def validate_assembly_type(self, value):
        return _dedupe_preserve_order(value)

    def create(self, validated_data):
        order_id = validated_data.pop("order_id")
        order = OrderEntry.objects.get(id=order_id)
        return RequestForQuote.objects.create(order=order, **validated_data)

    def update(self, instance, validated_data):
        order_id = validated_data.pop("order_id", None)
        if order_id is not None:
            instance.order = OrderEntry.objects.get(id=order_id)
        instance.quote_types = validated_data.get("quote_types", instance.quote_types)
        instance.assembly_type = validated_data.get(
            "assembly_type", instance.assembly_type
        )
        instance.quantity = validated_data.get("quantity", instance.quantity)
        instance.save(
            update_fields=["order", "quote_types", "assembly_type", "quantity"]
        )
        return instance


class RFQStep2Serializer(serializers.Serializer):
    rfq_id = serializers.IntegerField()
    bom_parts = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    components = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    services = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )

    def validate_services(self, value):
        """Validate against known static service keys."""
        valid_keys = {s["key"] for s in RFQ_SERVICES}
        invalid = [v for v in value if v not in valid_keys]
        if invalid:
            raise serializers.ValidationError(
                f"Invalid service(s): {invalid}. "
                f"Valid choices: {sorted(valid_keys)}"
            )
        return value


class RFQStep3Serializer(serializers.Serializer):
    rfq_id = serializers.IntegerField()
    vendor_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        error_messages={"min_length": "At least one vendor must be selected."},
    )
    delivery_date = serializers.DateField()
    delivery_address = serializers.CharField()
    additional_requirements = serializers.CharField(
        required=False, allow_blank=True, default=""
    )

    def validate_vendor_ids(self, value):
        existing = set(Vendor.objects.filter(id__in=value).values_list("id", flat=True))
        missing = set(value) - existing
        if missing:
            raise serializers.ValidationError(
                f"Vendor ID(s) not found: {sorted(missing)}"
            )
        return value


class RFQListSerializer(serializers.ModelSerializer):
    order_reference = serializers.SerializerMethodField()
    device_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()

    vendor_names = serializers.SerializerMethodField()
    bom_parts_count = serializers.SerializerMethodField()
    components_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = RequestForQuote
        fields = [
            "id",
            "order_reference",
            "device_name",
            "customer_name",
            "quantity",
            "quote_types",
            "assembly_type",
            "delivery_date",
            "created_at",
            "status",
            "status_display",
            "vendor_names",
            "bom_parts_count",
            "components_count",
        ]

    def get_order_reference(self, obj):
        return obj.order_reference

    def get_device_name(self, obj):
        mto = getattr(obj.order, "make_to_order", None)
        if mto and mto.product:
            return mto.product.name
        return None

    def get_customer_name(self, obj):
        # Image 1 Order Details Preview: "TechCorp Solutions"
        mto = getattr(obj.order, "make_to_order", None)
        return mto.customer_name if mto else None

    def get_vendor_names(self, obj):
        return list(obj.quotations.values_list("vendor__name", flat=True).distinct())

    def get_bom_parts_count(self, obj):
        return obj.selections.filter(item_type="bom").count()

    def get_components_count(self, obj):
        return obj.selections.filter(item_type="component").count()


class RFQSelectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFQSelection
        fields = ["id", "item_type", "reference"]


class RFQDetailSerializer(serializers.ModelSerializer):
    selections = RFQSelectionSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    order_reference = serializers.SerializerMethodField()
    device_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    order_type = serializers.SerializerMethodField()
    order_status = serializers.SerializerMethodField()

    # Step 2 current selection state
    bom_parts = serializers.SerializerMethodField()
    components = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()

    vendor_names = serializers.SerializerMethodField()

    class Meta:
        model = RequestForQuote
        fields = [
            "id",
            "order_reference",
            "device_name",
            "customer_name",
            "order_type",
            "order_status",
            "quantity",
            "quote_types",
            "assembly_type",
            "delivery_date",
            "delivery_address",
            "additional_requirements",
            "created_at",
            "status",
            "status_display",
            "selections",
            "bom_parts",
            "components",
            "services",
            "vendor_names",
        ]
        read_only_fields = ["id", "created_at", "status", "selections"]

    def get_order_reference(self, obj):
        return obj.order_reference

    def get_device_name(self, obj):
        mto = getattr(obj.order, "make_to_order", None)
        if mto and mto.product:
            return mto.product.name
        return None

    def get_customer_name(self, obj):
        mto = getattr(obj.order, "make_to_order", None)
        return mto.customer_name if mto else None

    def get_order_type(self, obj):
        return (
            obj.order.get_production_type_display()
            if obj.order.production_type
            else None
        )

    def get_order_status(self, obj):
        order = obj.order
        if order.is_step2_complete:
            return "CONFIRMED"
        elif order.is_step1_complete:
            return "IN PROGRESS"
        return "DRAFT"

    def get_bom_parts(self, obj):
        return list(
            obj.selections.filter(item_type="bom").values_list("reference", flat=True)
        )

    def get_components(self, obj):
        return list(
            obj.selections.filter(item_type="component").values_list(
                "reference", flat=True
            )
        )

    def get_services(self, obj):
        return list(
            obj.selections.filter(item_type="service").values_list(
                "reference", flat=True
            )
        )

    def get_vendor_names(self, obj):
        return list(obj.quotations.values_list("vendor__name", flat=True).distinct())


# ------------------ Create Purchase Order STEP 1 ------------------

# ─────────────────────────────────────────────────────────────
# PURCHASE ORDER — STEP 1 DROPDOWNS
# ─────────────────────────────────────────────────────────────
class POOrderIDDropdownSerializer(serializers.ModelSerializer):
    """
    Image 2: Select Order ID dropdown.
    Shows: order_reference, rfq_count (always 1 per RFQ), total_units
    """

    rfq_count = serializers.SerializerMethodField()
    total_units = serializers.IntegerField(source="quantity")
    label = serializers.CharField(source="order_reference")

    class Meta:
        model = RequestForQuote
        fields = ["id", "label", "rfq_count", "total_units"]

    def get_rfq_count(self, obj):
        return 1  


class POSelectRFQDropdownSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    type_badge = serializers.SerializerMethodField()
    total_units = serializers.IntegerField(source="quantity")
    date = serializers.DateField(source="delivery_date")

    class Meta:
        model = RequestForQuote
        fields = ["id", "label", "type_badge", "total_units", "date"]

    def get_label(self, obj):
        # Image 3: "RFQ-MW-2024-002 - Vehicle-Monitor-X"
        return f"{obj.order_reference} - {obj.device_name}"

    def get_type_badge(self, obj):
        # Image 3: "Items + Components" — derived from RFQSelection types
        types = obj.selections.values_list("item_type", flat=True).distinct()
        type_map = {
            "bom": "Items",
            "component": "Components",
            "service": "Services",
        }
        parts = [type_map[t] for t in types if t in type_map]
        return " + ".join(parts) if parts else "Items"


# ─────────────────────────────────────────────────────────────
# PURCHASE ORDER — STEP 1 (UPDATED)
# ─────────────────────────────────────────────────────────────
class PurchaseStep1Serializer(serializers.Serializer):
    buyer_name = serializers.CharField()
    order_id = serializers.CharField()

    # Image 1: "Select RFQs" — at least one required
    rfq_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        error_messages={"min_length": "At least one RFQ is required."},
    )

    assembly_type = serializers.ChoiceField(choices=PurchaseOrder.ASSEMBLY_TYPE_CHOICES)

    order_types = serializers.ListField(
        child=serializers.ChoiceField(choices=["bom", "component", "service"]),
        min_length=1,
    )

    def validate_rfq_ids(self, value):
        """Ensure all submitted RFQ IDs exist and are submitted status."""
        existing = RequestForQuote.objects.filter(
            id__in=value, status="submitted"
        ).values_list("id", flat=True)

        missing = set(value) - set(existing)
        if missing:
            raise serializers.ValidationError(
                f"Invalid or non-submitted RFQ IDs: {sorted(missing)}"
            )
        return value


# ─────────────────────────────────────────────────────────────
# PURCHASE ORDER — STEP 2 GET: RFQ DETAILS
# ─────────────────────────────────────────────────────────────
class VendorQuoteForItemSerializer(serializers.Serializer):
    vendor_id = serializers.IntegerField()
    vendor_name = serializers.CharField()
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    gst_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    delivery_days = serializers.IntegerField()
    is_lowest = serializers.BooleanField()


class RFQBOMItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="reference")
    description = serializers.SerializerMethodField()
    vendor_quotes = serializers.SerializerMethodField()

    class Meta:
        model = RFQSelection
        fields = ["id", "item_name", "description", "item_type", "vendor_quotes"]

    def get_description(self, obj):
        # Image 8: "BOM Part - PCB-002" — constructed from type + reference
        type_label = {
            "bom": "BOM Part",
            "component": "Component",
            "service": "Service",
        }.get(obj.item_type, obj.item_type)
        return f"{type_label} - {obj.reference}"

    def get_vendor_quotes(self, obj):
        """
        Image 8: Multiple vendor quotes per item.
        Derive from RFQQuotation for this RFQ, mark lowest price.
        """
        quotations = obj.rfq.quotations.filter(
            status__in=["quoted", "accepted"]
        ).select_related("vendor")

        if not quotations:
            return []

        quotes = []
        for q in quotations:
            quotes.append(
                {
                    "vendor_id": q.vendor.id,
                    "vendor_name": q.vendor.name,
                    "unit_price": q.quotation_rate,
                    "gst_rate": Decimal("18.00"),  # standard GST shown in images
                    "total_price": (
                        q.quotation_rate * Decimal("1.18")
                        if q.quotation_rate
                        else Decimal("0.00")
                    ),
                    "delivery_days": 0,  # not stored per-item in RFQQuotation
                    "is_lowest": False,
                }
            )

        # Mark lowest price vendor
        valid = [q for q in quotes if q["unit_price"] is not None]
        if valid:
            min_price = min(q["unit_price"] for q in valid)
            for q in quotes:
                if q["unit_price"] == min_price:
                    q["is_lowest"] = True
                    break

        return quotes


class ComponentVendorQuoteSerializer(serializers.Serializer):
    vendor_id = serializers.IntegerField()
    vendor_name = serializers.CharField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    gst = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    delivery_days = serializers.IntegerField()
    is_lowest = serializers.BooleanField()


class DeviceComponentSerializer(serializers.Serializer):
    component_type = (
        serializers.CharField()
    )  # enclosure, wire_harness, battery, accessories
    description = serializers.CharField()
    vendor_quotes = ComponentVendorQuoteSerializer(many=True)


class RFQCardSerializer(serializers.ModelSerializer):
    rfq_id = serializers.CharField(source="order_reference")
    device = serializers.CharField(source="device_name")
    quantity_display = serializers.SerializerMethodField()
    bom_items = serializers.SerializerMethodField()
    device_components = serializers.SerializerMethodField()

    class Meta:
        model = RequestForQuote
        fields = [
            "id",
            "rfq_id",
            "device",
            "quantity",
            "quantity_display",
            "delivery_date",
            "delivery_address",
            "additional_requirements",
            "bom_items",
            "device_components",
        ]

    def get_quantity_display(self, obj):
        return f"{obj.quantity} units"

    def get_bom_items(self, obj):
        """Images 7-8: BOM items from RFQSelection with vendor quotes."""
        selections = obj.selections.filter(item_type="bom")
        return RFQBOMItemSerializer(selections, many=True).data

    def get_device_components(self, obj):
        from .models import Device

        # Find device by name matching rfq.device_name
        try:
            device = (
                Device.objects.select_related("enclosure", "wireharness", "battery")
                .prefetch_related("accessories")
                .filter(info__model__icontains=obj.device_name, status="completed")
                .first()
            )
        except Exception:
            device = None

        if not device:
            return []

        components = []
        vendors = list(
            obj.quotations.filter(status__in=["quoted", "accepted"]).select_related(
                "vendor"
            )
        )

        def make_vendor_quotes(vendor_list):
            """Build vendor quote list and mark lowest."""
            quotes = []
            for q in vendor_list:
                if not q.quotation_rate:
                    continue
                gst = (q.quotation_rate * Decimal("18")) / Decimal("100")
                quotes.append(
                    {
                        "vendor_id": q.vendor.id,
                        "vendor_name": q.vendor.name,
                        "unit_price": q.quotation_rate,
                        "gst": gst.quantize(Decimal("0.01")),
                        "total": (q.quotation_rate + gst).quantize(Decimal("0.01")),
                        "delivery_days": 0,
                        "is_lowest": False,
                    }
                )
            if quotes:
                min_price = min(q["unit_price"] for q in quotes)
                for q in quotes:
                    if q["unit_price"] == min_price:
                        q["is_lowest"] = True
                        break
            return quotes

        # Image 8-9: Enclosure
        if hasattr(device, "enclosure"):
            enc = device.enclosure
            components.append(
                {
                    "component_type": "enclosure",
                    "description": (
                        f"{enc.length}×{enc.breadth}×{enc.height}mm"
                        f" - {enc.material} ({enc.color})"
                    ),
                    "vendor_quotes": make_vendor_quotes(vendors),
                }
            )

        # Image 10: Wire Harness
        if hasattr(device, "wireharness"):
            wh = device.wireharness
            components.append(
                {
                    "component_type": "wire_harness",
                    "description": (f"{wh.number_of_wires} wires - {wh.specification}"),
                    "vendor_quotes": make_vendor_quotes(vendors),
                }
            )

        # Image 10: Battery
        if hasattr(device, "battery"):
            bat = device.battery
            components.append(
                {
                    "component_type": "battery",
                    "description": f"{bat.capacity} (Part: {bat.part_number})",
                    "vendor_quotes": make_vendor_quotes(vendors),
                }
            )

        # Image 10-11: Accessories
        accessories = device.accessories.all()
        if accessories.exists():
            desc = ", ".join([f"{a.name}" for a in accessories]) + " - Complete package"
            components.append(
                {
                    "component_type": "accessories",
                    "description": desc,
                    "vendor_quotes": make_vendor_quotes(vendors),
                }
            )

        return components


class PurchaseStep2GetSerializer(serializers.Serializer):
    selected_order_types = serializers.ListField(child=serializers.CharField())
    rfq_items = RFQCardSerializer(many=True)
    available_vendors = serializers.SerializerMethodField()

    def get_available_vendors(self, obj):
        return obj.get("available_vendors", [])


class AvailableVendorSummarySerializer(serializers.Serializer):
    vendor_id = serializers.IntegerField()
    vendor_name = serializers.CharField()
    vendor_code = serializers.CharField()
    total_price = serializers.DecimalField(max_digits=14, decimal_places=2)


# ─────────────────────────────────────────────────────────────
# PURCHASE ORDER — STEP 2 POST (UPDATED)
# ─────────────────────────────────────────────────────────────
class PurchaseLineSerializer(serializers.Serializer):
    item_code = serializers.CharField()
    item_type = serializers.ChoiceField(choices=["bom", "component", "service"])
    vendor_id = serializers.CharField()
    vendor_name = serializers.CharField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    gst_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    delivery_days = serializers.IntegerField(min_value=1)


# ---------- Create Purchase Order STEP 2 ----------
class PurchaseStep2Serializer(serializers.Serializer):
    wastage_percentage = serializers.IntegerField(min_value=0, max_value=100)
    selected_vendor_id = serializers.CharField()
    delivery_date = serializers.DateField()
    payment_terms = serializers.ChoiceField(
        choices=[c[0] for c in PurchaseOrder.PAYMENT_TERMS_CHOICES]
    )
    items = PurchaseLineSerializer(many=True, min_length=1)


# ---------------- Create Material Receipt Note (MRN) ----------------
class MRNItemSerializer(serializers.Serializer):
    purchase_order_item_id = serializers.IntegerField()
    received_qty = serializers.IntegerField(min_value=1)
    serial_numbers = serializers.CharField(required=False, allow_blank=True)


# ---------------- Create Material Receipt Note (MRN) ----------------
class MRNCreateSerializer(serializers.Serializer):
    purchase_order_id = serializers.IntegerField()
    po_date = serializers.DateField()
    vendor_id = serializers.IntegerField()
    inward_type = serializers.ChoiceField(
        choices=MaterialReceiptNote.INWARD_TYPE_CHOICES
    )
    receipt_date = serializers.DateField()

    invoice_number = serializers.CharField(required=False, allow_blank=True)
    delivery_challan_number = serializers.CharField(required=False, allow_blank=True)
    eway_bill_number = serializers.CharField(required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True)

    items = serializers.CharField()

    def validate_items(self, value):
        try:
            data = json.loads(value)
        except Exception:
            raise serializers.ValidationError("Invalid JSON format for items")

        if not isinstance(data, list) or not data:
            raise serializers.ValidationError("Items must be a non-empty list")

        return data


# ---------------- Dispatch Workflow ----------------
# ---------------- STEP 1 ----------------
class DispatchStep1Serializer(serializers.ModelSerializer):
    class Meta:
        model = Dispatch
        fields = [
            "sales_order",
            "order_type",
        ]


# ---------------- STEP 2 ----------------
class DispatchStep2Serializer(serializers.ModelSerializer):
    class Meta:
        model = Dispatch
        fields = [
            "product",
            "batch",
            "dispatch_quantity",
            "imei_number",
            "serial_number",
            "iccid_number",
        ]

    def validate(self, data):
        batch = data["batch"]
        qty = data["dispatch_quantity"]

        if qty > batch.available_stock:
            raise serializers.ValidationError(
                "Dispatch quantity cannot exceed available stock."
            )

        return data


# ---------------- STEP 3 ----------------
class DispatchStep3Serializer(serializers.ModelSerializer):
    class Meta:
        model = Dispatch
        fields = [
            "dispatch_date",
            "dispatch_remarks",
        ]


# ---------------- STEP 4 ----------------
class DispatchStep4Serializer(serializers.ModelSerializer):
    class Meta:
        model = Dispatch
        fields = [
            "customer_name",
            "customer_contact",
            "customer_email",
            "customer_address",
            "urgent_delivery_required",
            "insurance_required",
        ]


# --------------------------- Header Serializer (Step 2) ---------------------------
class PostDispatchReturnHeaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostDispatchReturn
        fields = [
            "dispatch_id",
            "invoice_no",
            "customer_name",
            "dispatch_total_value",
            "return_type",
            "return_reason",
            "return_date",
            "return_remarks",
        ]


# ---------------------------- Item Serializer (Step 3) ----------------------------
class PostDispatchReturnItemSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    description = serializers.CharField()
    dispatched_qty = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    return_qty = serializers.IntegerField(min_value=1)

    def validate(self, data):
        if data["return_qty"] > data["dispatched_qty"]:
            raise serializers.ValidationError(
                "Return quantity cannot exceed dispatched quantity."
            )
        return data


# -------------------------- Final Submit Serializer --------------------------
class PostDispatchReturnCreateSerializer(serializers.Serializer):
    header = PostDispatchReturnHeaderSerializer()
    items = PostDispatchReturnItemSerializer(many=True)

    def validate(self, data):
        if not data.get("items"):
            raise serializers.ValidationError(
                "At least one item must be selected for return."
            )
        return data


# -------------------- Generic Dropdown Serializer --------------------
class DropdownSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()


# ---------------- Module Management Account Registration ----------------
class AccountRegistrationSerializer(serializers.ModelSerializer):
    aadhar_document = serializers.FileField(validators=[validate_file_size])
    pan_document = serializers.FileField(validators=[validate_file_size])

    class Meta:
        model = AccountRegistration
        fields = [
            "id",
            "account_name",
            "phone_number",
            "email",
            "address",
            "state",
            "district",
            "aadhar_number",
            "aadhar_document",
            "pan_number",
            "pan_document",
        ]

    def validate(self, data):
        # Enforce State → District dependency (visible in UI)
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError(
                {"district": "Selected district does not belong to selected state."}
            )
        return data


# ---------------- Module Management QC Inspector Registration ----------------
class QCInspectorRegistrationSerializer(BaseSerializer):
    class Meta:
        model = QCInspectorRegistration
        fields = [
            "id",
            "qc_inspector_name",
            "phone_number",
            "email",
            "address",
            "state",
            "district",
            "aadhar_number",
            "aadhar_document",
            "pan_number",
            "pan_document",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {
            "aadhar_document": {
                "validators": [validate_file_size],
                "required": False,
            },
            "pan_document": {
                "validators": [validate_file_size],
                "required": False,
            },
        }

    def validate(self, data):
        self._validate_state_district(data)
        return data


# ---------------- Module Management Purchase Department Registration ----------------
class PurchaseDepartmentRegistrationSerializer(serializers.ModelSerializer):
    aadhar_document = serializers.FileField(validators=[validate_file_size])
    pan_document = serializers.FileField(validators=[validate_file_size])

    class Meta:
        model = PurchaseDepartmentRegistration
        fields = [
            "id",
            "purchase_department_name",
            "phone_number",
            "email",
            "address",
            "state",
            "district",
            "aadhar_number",
            "aadhar_document",
            "pan_number",
            "pan_document",
        ]

    def validate(self, data):

        instance = getattr(self, "instance", None)

        state = data.get("state", getattr(instance, "state", None))
        district = data.get("district", getattr(instance, "district", None))

        if state and district and district.state_id != state.id:
            raise serializers.ValidationError(
                {"district": "Selected district does not belong to selected state."}
            )

        return data


# ---------------- Module Management Store Manager Registration ----------------
class StoreManagerRegistrationSerializer(serializers.ModelSerializer):
    aadhar_document = serializers.FileField(validators=[validate_file_size])
    pan_document = serializers.FileField(validators=[validate_file_size])

    class Meta:
        model = StoreManagerRegistration
        fields = [
            "id",
            "store_manager_name",
            "phone_number",
            "email",
            "address",
            "state",
            "district",
            "aadhar_number",
            "aadhar_document",
            "pan_number",
            "pan_document",
        ]

    def validate(self, data):
        instance = getattr(self, "instance", None)
        state = data.get("state", getattr(instance, "state", None))
        district = data.get("district", getattr(instance, "district", None))
        if state and district and district.state_id != state.id:
            raise serializers.ValidationError(
                {"district": "Selected district does not belong to selected state."}
            )
        return data


# ---------------- Module Management Repair Technician Registration ----------------
class RepairTechnicianRegistrationSerializer(serializers.ModelSerializer):
    aadhar_document = serializers.FileField(validators=[validate_file_size])
    pan_document = serializers.FileField(validators=[validate_file_size])

    class Meta:
        model = RepairTechnicianRegistration
        fields = [
            "id",
            "repair_technician_name",
            "phone_number",
            "email",
            "address",
            "state",
            "district",
            "aadhar_number",
            "aadhar_document",
            "pan_number",
            "pan_document",
        ]

    def validate(self, data):
        instance = getattr(self, "instance", None)
        state = data.get("state", getattr(instance, "state", None))
        district = data.get("district", getattr(instance, "district", None))
        if state and district and district.state_id != state.id:
            raise serializers.ValidationError(
                {"district": "Selected district does not belong to selected state."}
            )
        return data


# ---------------- Product Category ----------------
class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["created_at"]


# ---------------- Store Transfer (Inventory Data) ----------------
class StoreTransferListSerializer(serializers.ModelSerializer):
    """List view with all columns for Inventory Data table"""

    product_name = serializers.CharField(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    dispatch_status_display = serializers.CharField(
        source="get_dispatch_status_display", read_only=True
    )

    class Meta:
        model = StoreTransfer
        fields = [
            "id",
            "transfer_id",
            "product_id",
            "product_name",
            "category",
            "category_name",
            "mrn_number",
            "batch_number",
            "vendor",
            "vendor_name",
            "quantity",
            "unit_price",
            "total_value",
            "transfer_date",
            "dispatch_status",
            "dispatch_status_display",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "product_name",
            "vendor_name",
            "dispatch_status_display",
            "created_at",
        ]


# ---------------- Detailed View Serializer ----------------
class StoreTransferDetailSerializer(serializers.ModelSerializer):
    """Detailed view with all information including creator"""

    product_name = serializers.CharField(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    dispatch_status_display = serializers.CharField(
        source="get_dispatch_status_display", read_only=True
    )

    class Meta:
        model = StoreTransfer
        fields = [
            "id",
            "transfer_id",
            "product_id",
            "product_name",
            "category",
            "category_name",
            "mrn_number",
            "batch_number",
            "vendor",
            "vendor_name",
            "quantity",
            "unit_price",
            "total_value",
            "transfer_date",
            "dispatch_status",
            "dispatch_status_display",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_username",
        ]
        read_only_fields = [
            "id",
            "product_name",
            "vendor_name",
            "created_by_username",
            "dispatch_status_display",
            "created_at",
            "updated_at",
        ]


# ------------- Create and Update Serializer -----------------
class StoreTransferCreateUpdateSerializer(serializers.ModelSerializer):
    """Create and update operations"""

    class Meta:
        model = StoreTransfer
        fields = [
            "product",
            "product_name",
            "category",
            "mrn_number",
            "batch_number",
            "vendor",
            "quantity",
            "unit_price",
            "total_value",
            "transfer_date",
            "dispatch_status",
        ]

    def validate(self, data):
        # Validate quantity
        if data.get("quantity", 0) <= 0:
            raise serializers.ValidationError(
                {"quantity": "Quantity must be greater than 0."}
            )

        # Validate unit_price
        if data.get("unit_price", 0) < 0:
            raise serializers.ValidationError(
                {"unit_price": "Unit price cannot be negative."}
            )

        # Validate total_value matches quantity * unit_price
        quantity = data.get("quantity")
        unit_price = data.get("unit_price")
        total_value = data.get("total_value")

        if quantity and unit_price:
            expected_total = Decimal(str(quantity)) * Decimal(str(unit_price))
            if Decimal(str(total_value)) != expected_total:
                raise serializers.ValidationError(
                    {
                        "total_value": f"Total value must equal quantity × unit_price. Expected: {expected_total}"
                    }
                )

        return data


# ------------- DEBIT NOTES & CREDIT NOTES - ACCOUNT MANAGEMENT -----------------
class DebitNoteListSerializer(serializers.ModelSerializer):
    """List view for debit notes with essential fields"""

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = DebitNote
        fields = [
            "id",
            "number",
            "date",
            "vendor",
            "reason",
            "reason_display",
            "amount",
            "status",
            "status_display",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = [
            "number",
            "created_at",
            "created_by_name",
            "reason_display",
            "status_display",
        ]


# ------------- Debit Note Detail Serializer -----------------
class DebitNoteDetailSerializer(serializers.ModelSerializer):
    """Detail view for single debit note"""

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = DebitNote
        fields = [
            "id",
            "number",
            "date",
            "vendor",
            "reason",
            "reason_display",
            "amount",
            "status",
            "status_display",
            "reference_document",
            "remarks",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "number",
            "created_at",
            "updated_at",
            "created_by_name",
            "reason_display",
            "status_display",
        ]


# ------------- Create and Update Serializer -----------------
class DebitNoteCreateUpdateSerializer(serializers.ModelSerializer):
    """Create and update serializer for debit notes"""

    number = serializers.CharField(read_only=True)

    class Meta:
        model = DebitNote
        fields = [
            "number",
            "vendor",
            "reason",
            "amount",
            "reference_document",
            "remarks",
            "status",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value

    def validate_vendor(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Vendor name cannot be empty.")
        return value.strip()


# ------------- CREDIT NOTES - ACCOUNT MANAGEMENT -----------------
class CreditNoteListSerializer(serializers.ModelSerializer):
    """List view for credit notes with essential fields"""

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = CreditNote
        fields = [
            "id",
            "number",
            "date",
            "customer",
            "reason",
            "reason_display",
            "amount",
            "status",
            "status_display",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = [
            "number",
            "created_at",
            "created_by_name",
            "reason_display",
            "status_display",
        ]


# ------------- Credit Note Detail Serializer -----------------
class CreditNoteDetailSerializer(serializers.ModelSerializer):
    """Detail view for single credit note"""

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = CreditNote
        fields = [
            "id",
            "number",
            "date",
            "customer",
            "reason",
            "reason_display",
            "amount",
            "status",
            "status_display",
            "reference_document",
            "remarks",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "number",
            "created_at",
            "updated_at",
            "created_by_name",
            "reason_display",
            "status_display",
        ]


# ------------- Create and Update Serializer -----------------
class CreditNoteCreateUpdateSerializer(serializers.ModelSerializer):
    """Create and update serializer for credit notes"""

    number = serializers.CharField(read_only=True)

    class Meta:
        model = CreditNote
        fields = [
            "number",
            "customer",
            "reason",
            "amount",
            "reference_document",
            "remarks",
            "status",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value

    def validate_customer(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Customer name cannot be empty.")
        return value.strip()


# ============================================================
# RETURN REQUEST SERIALIZERS
# ============================================================
class ReturnRequestSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )

    class Meta:
        model = ReturnRequest
        fields = [
            "id",
            "return_number",
            "date",
            "items",
            "reason",
            "amount",
            "status",
            "created_at",
            "updated_at",
            "created_by_username",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by_username"]

    def validate_date(self, value):
        """Ensure date is not in future"""
        from django.utils import timezone

        if value > timezone.now().date():
            raise serializers.ValidationError("Return date cannot be in the future")
        return value

    def validate_amount(self, value):
        """Ensure amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value


class ReturnRequestListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""

    class Meta:
        model = ReturnRequest
        fields = ["id", "return_number", "date", "items", "reason", "amount", "status"]


class ReturnRequestCountSerializer(serializers.Serializer):
    """Serializer for return request counts by status"""

    pending = serializers.IntegerField()
    accepted = serializers.IntegerField()
    rejected = serializers.IntegerField()


# ============================================================
# REPAIR RECORD SERIALIZERS
# ============================================================
class RepairRecordSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )

    class Meta:
        model = RepairRecord
        fields = [
            "id",
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
            "created_at",
            "updated_at",
            "created_by_username",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by_username"]

    def validate(self, data):
        """Validate repair quantities"""
        if data.get("repaired_qty", 0) + data.get("rejected_qty", 0) > data.get(
            "failed_qty", 0
        ):
            raise serializers.ValidationError(
                "Repaired Qty + Rejected Qty cannot exceed Failed Qty"
            )

        repair_pending = data.get("repair_pending", 0)
        if repair_pending < 0:
            raise serializers.ValidationError("Repair Pending cannot be negative")

        return data


class RepairRecordListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""

    class Meta:
        model = RepairRecord
        fields = [
            "id",
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
        ]


# ============================================================
# REJECTED ITEM SERIALIZERS
# ============================================================
class RejectedItemSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )

    class Meta:
        model = RejectedItem
        fields = [
            "id",
            "product_id",
            "product_name",
            "vendor",
            "mrn_number",
            "rejected_qty",
            "qc_date",
            "created_at",
            "updated_at",
            "created_by_username",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by_username"]

    def validate_qc_date(self, value):
        """Ensure QC date is not in future"""
        from django.utils import timezone

        if value > timezone.now().date():
            raise serializers.ValidationError("QC date cannot be in the future")
        return value

    def validate_rejected_qty(self, value):
        """Ensure rejected quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Rejected Qty must be greater than 0")
        return value


class RejectedItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""

    class Meta:
        model = RejectedItem
        fields = [
            "id",
            "product_id",
            "product_name",
            "vendor",
            "mrn_number",
            "rejected_qty",
            "qc_date",
        ]


# ================== Self Order ==================
class SelfOrderSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source="device.info.model", read_only=True)
    state_name = serializers.CharField(source="supply_state.name", read_only=True)

    class Meta:
        model = SelfOrder
        fields = [
            "id",
            "device",
            "device_name",
            "quantity",
            "supply_state",
            "state_name",
            "rate",
            "gst_rate",
            "gross_amount",
            "delivery_date",
            "delivery_address",
            "purpose_remark",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "device_name",
            "state_name",
            "gross_amount",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", None))
        rate = attrs.get("rate", getattr(self.instance, "rate", None))
        gst_rate = attrs.get("gst_rate", getattr(self.instance, "gst_rate", None))

        if quantity is not None and rate is not None and gst_rate is not None:
            base_amount = quantity * rate
            gst_amount = (base_amount * gst_rate) / Decimal("100")
            attrs["gross_amount"] = (base_amount + gst_amount).quantize(Decimal("0.01"))

        return attrs

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def validate_rate(self, value):
        if value < 0:
            raise serializers.ValidationError("Rate cannot be negative.")
        return value

    def validate_delivery_date(self, value):
        from django.utils import timezone

        if value < timezone.now().date():
            raise serializers.ValidationError("Delivery date cannot be in the past.")
        return value


# --------- Quotation Item Serializer ---------
class QuotationItemSerializer(serializers.ModelSerializer):
    """Serializer for quotation items"""

    class Meta:
        model = QuotationItem
        fields = [
            "id",
            "item_name",
            "description",
            "item_type",
            "quantity",
            "net_unit_price_excl_gst",
            "gst_rate",
            "subtotal_excl_gst",
            "gst_amount",
            "total_incl_gst",
        ]
        read_only_fields = ["gst_amount", "subtotal_excl_gst", "total_incl_gst"]


# --------- Quotation Create Serializer ---------
class QuotationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating quotations from RFQ"""

    items = QuotationItemSerializer(many=True, write_only=True)

    class Meta:
        model = Quotation
        fields = [
            "rfq",
            "vendor",
            "customer_name",
            "valid_until",
            "items",
        ]

    def validate(self, data):
        """Validate quotation data"""
        if not data.get("items"):
            raise serializers.ValidationError(
                "Quotation must contain at least one item."
            )

        rfq = data.get("rfq")
        vendor = data.get("vendor")

        # Check for duplicate quotation for same RFQ and vendor
        existing = Quotation.objects.filter(rfq=rfq, vendor=vendor).exists()
        if existing:
            raise serializers.ValidationError(
                "A quotation already exists for this RFQ and vendor."
            )

        return data

    def create(self, validated_data):
        """Create quotation with items"""
        items_data = validated_data.pop("items")

        # Generate unique quotation number
        from .utils import generate_quotation_number

        quotation_number = generate_quotation_number()

        # Get current user
        user = self.context["request"].user

        # Create quotation
        quotation = Quotation.objects.create(
            quotation_number=quotation_number, created_by=user, **validated_data
        )

        # Create items
        for item_data in items_data:
            quantity = item_data.get("quantity", 1)
            net_unit_price = item_data.get("net_unit_price_excl_gst")
            gst_rate = item_data.get("gst_rate", Decimal("18.00"))

            # Calculate subtotal
            subtotal = quantity * net_unit_price

            # Calculate GST and total before creating item
            gst_amount = subtotal * (gst_rate / Decimal("100"))
            total_incl_gst = subtotal + gst_amount

            item = QuotationItem.objects.create(
                quotation=quotation,
                subtotal_excl_gst=subtotal,
                gst_amount=gst_amount,
                total_incl_gst=total_incl_gst,
                **item_data,
            )

        # Calculate quotation totals
        quotation.calculate_totals()

        return quotation


# --------- Quotation List Serializer ---------
class QuotationListSerializer(serializers.ModelSerializer):
    """Serializer for listing quotations"""

    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    rfq_reference = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Quotation
        fields = [
            "id",
            "quotation_number",
            "customer_name",
            "rfq_reference",
            "vendor_name",
            "item_count",
            "subtotal_excl_gst",
            "total_gst",
            "grand_total_incl_gst",
            "valid_until",
            "status",
            "status_display",
            "created_at",
        ]
        read_only_fields = fields

    def get_rfq_reference(self, obj):
        """Get RFQ reference number"""
        return f"RFQ-{obj.rfq.id}"

    def get_item_count(self, obj):
        """Get count of items in quotation"""
        return obj.items.count()


# --------- Quotation Detail Serializer ---------
class QuotationDetailSerializer(serializers.ModelSerializer):
    """Serializer for quotation details"""

    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    rfq_reference = serializers.SerializerMethodField()
    items = QuotationItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )

    class Meta:
        model = Quotation
        fields = [
            "id",
            "quotation_number",
            "customer_name",
            "rfq_reference",
            "vendor_name",
            "status",
            "status_display",
            "subtotal_excl_gst",
            "total_gst",
            "grand_total_incl_gst",
            "valid_until",
            "items",
            "created_at",
            "created_by_name",
            "updated_at",
        ]
        read_only_fields = fields

    def get_rfq_reference(self, obj):
        """Get RFQ reference number"""
        return f"RFQ-{obj.rfq.id}"


# --------- Quotation Approve/Reject Serializer ---------
class QuotationApproveRejectSerializer(serializers.Serializer):
    """Serializer for approving or rejecting quotations"""

    status = serializers.ChoiceField(choices=["approved", "rejected"])

    def validate_status(self, value):
        """Validate status"""
        if value not in ["approved", "rejected"]:
            raise serializers.ValidationError(
                "Status must be 'approved' or 'rejected'."
            )
        return value


class DeviceInventorySerializer(serializers.ModelSerializer):

    device_name = serializers.CharField(source="device.info.make", read_only=True)
    device_model = serializers.CharField(source="device.info.model", read_only=True)

    class Meta:
        model = DeviceInventory
        fields = [
            "id",
            "device",
            "device_name",
            "device_model",
            "esn",
            "imei",
            "iccid",
            "telecom_provider_1",
            "telecom_provider_2",
            "msisdn_1",
            "msisdn_2",
            "esim_status",
            "esim_validity",
            "stock_status",
            "assigned_to",
            "remarks",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class B2BOrderCreateSerializer(serializers.ModelSerializer):
    """
    Write serializer for B2B Order creation.
    Matches the /b2b-order form fields exactly:
      - purchase_order  (Select PO dropdown)
      - supply_state    (Supply State dropdown)
      - rate            (Rate ₹)
      - gst_rate        (GST Rate dropdown)
      - quantity        (Quantity)
      - gross_amount    (Gross Amount ₹ — validated against backend calculation)
      - delivery_date   (Delivery Date)
      - remarks         (Remarks — optional)
    gross_amount is read_only in response (auto-calculated).
    """

    class Meta:
        model = B2BOrder
        fields = [
            "purchase_order",
            "supply_state",
            "rate",
            "gst_rate",
            "quantity",
            "gross_amount",
            "delivery_date",
            "remarks",
        ]
        read_only_fields = ["gross_amount"]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def validate_rate(self, value):
        if value < 0:
            raise serializers.ValidationError("Rate cannot be negative.")
        return value

    def validate_delivery_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Delivery date cannot be in the past.")
        return value

    def validate(self, attrs):
        """
        Auto-calculate gross_amount from quantity, rate, gst_rate.
        Formula (same as SelfOrder): gross = (qty × rate) + GST amount
        """
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", None))
        rate = attrs.get("rate", getattr(self.instance, "rate", None))
        gst_rate = attrs.get("gst_rate", getattr(self.instance, "gst_rate", None))

        if quantity is not None and rate is not None and gst_rate is not None:
            base_amount = Decimal(quantity) * rate
            gst_amount = (base_amount * gst_rate) / Decimal("100")
            attrs["gross_amount"] = (base_amount + gst_amount).quantize(Decimal("0.01"))

        return attrs


class B2BOrderReadSerializer(serializers.ModelSerializer):
    """
    Read serializer for B2B Order list and detail views.
    Exposes human-readable names alongside FK IDs.
    """

    purchase_order_label = serializers.SerializerMethodField()
    supply_state_name = serializers.CharField(
        source="supply_state.name", read_only=True
    )
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )

    class Meta:
        model = B2BOrder
        fields = [
            "id",
            "purchase_order",
            "purchase_order_label",
            "supply_state",
            "supply_state_name",
            "rate",
            "gst_rate",
            "quantity",
            "gross_amount",
            "delivery_date",
            "remarks",
            "created_by_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_purchase_order_label(self, obj):
        return f"{obj.purchase_order.order_id} ({obj.purchase_order.assembly_type})"
