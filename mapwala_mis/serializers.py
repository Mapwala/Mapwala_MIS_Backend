# mapwala_mis/serializers.py
import re
from django.core.validators import RegexValidator
import json
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import serializers
from django.db import transaction
from .models import (
    State,
    District,
    ProductCategory,
    SupplierVendor,
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
    ProformaInvoice,Manufacturer
)


# ---------------- File Size Validator ----------------
def validate_file_size(file):
    max_size = settings.FILE_UPLOAD_MAX_MEMORY_SIZE

    if file.size > max_size:
        raise serializers.ValidationError(
            f"File size must be less than or equal to {max_size // (1024 * 1024)} MB."
        )


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
class ParentCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentCompany
        fields = "__all__"

    def validate(self, data):
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError(
                "Selected district does not belong to selected state."
            )
        return data


# ---------------- Vendor ----------------
class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        exclude = ("user",)

    def validate(self, data):
        request = self.context["request"]
        user = request.user

        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError(
                {"district": "Selected district does not belong to the selected state."}
            )

        if Vendor.objects.filter(user=user, gst_number=data["gst_number"]).exists():
            raise serializers.ValidationError(
                {
                    "gst_number": "Vendor with this GST number already exists for this user."
                }
            )

        return data


# ---------------- Registrations ----------------
class B2CCustomerRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = B2CCustomer
        fields = [
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
        ]

    def validate(self, data):
        state = data.get("state")
        district = data.get("district")

        if district.state_id != state.id:
            raise serializers.ValidationError(
                {"district": "Selected district does not belong to selected state."}
            )

        return data


# ---------------- B2B Partner Registration ----------------
class B2BPartnerRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = B2BPartner
        fields = [
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
        ]

    def validate(self, data):
        state = data.get("state")
        district = data.get("district")

        if district.state_id != state.id:
            raise serializers.ValidationError(
                {"district": "Selected district does not belong to selected state."}
            )

        return data


class LinkedToChoicesSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ["id", "name"]


# ---------------- Distributor Registration ----------------
class DistributorRegistrationSerializer(serializers.ModelSerializer):
    authorised_states = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.all(), many=True
    )
    authorised_districts = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(), many=True
    )

    class Meta:
        model = Distributor
        fields = [
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
            "authorised_states",
            "authorised_districts",
        ]

    def validate(self, data):
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError(
                {"district": "District does not belong to selected state."}
            )

        if data["linked_to"] == "manufacturer" and not data.get("manufacturer"):
            raise serializers.ValidationError(
                {"manufacturer": "Manufacturer is required."}
            )

        state_ids = {s.id for s in data["authorised_states"]}
        for d in data["authorised_districts"]:
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


# ---------------- Dealer Registration ----------------
class DealerRegistrationSerializer(serializers.ModelSerializer):
    authorised_states = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.all(),
        many=True,
        required=True,
    )

    authorised_districts = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(),
        many=True,
        required=True,
    )

    class Meta:
        model = Dealer
        fields = [
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
        ]

    def validate(self, data):
        # 1️ Address check
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError(
                {"district": "District does not belong to selected state."}
            )

        linked_to = data["linked_to"]
        manufacturer = data.get("manufacturer")
        distributor = data.get("distributor")

        # 2️ Linking logic
        if linked_to == "manufacturer":
            if not manufacturer:
                raise serializers.ValidationError(
                    {
                        "manufacturer": "Manufacturer is required when Linked To is Manufacturer."
                    }
                )
            if distributor:
                raise serializers.ValidationError(
                    {
                        "distributor": "Distributor must be empty when linked to Manufacturer."
                    }
                )

        if linked_to == "distributor":
            if not distributor:
                raise serializers.ValidationError(
                    {
                        "distributor": "Distributor is required when Linked To is Distributor."
                    }
                )
            if manufacturer:
                raise serializers.ValidationError(
                    {
                        "manufacturer": "Manufacturer must be empty when linked to Distributor."
                    }
                )

        # 3️ Authorised area validation (MULTI)
        state_ids = {s.id for s in data["authorised_states"]}

        for district in data["authorised_districts"]:
            if district.state_id not in state_ids:
                raise serializers.ValidationError(
                    {
                        "authorised_districts": (
                            f"District '{district.name}' does not belong "
                            f"to selected authorised states."
                        )
                    }
                )

        return data


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
        harness = WireHarness.objects.create(**validated_data)
        for c in connectors:
            WireConnector.objects.create(wire_harness=harness, **c)
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
class StickerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sticker
        exclude = ["device"]


# ---------------- STEP 9 ----------------
class UserManualSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserManual
        exclude = ["device"]


# ---------------- STEP 10 ----------------
class AccessorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Accessory
        exclude = ["device"]


# ---------------- Order Entry ----------------
class OrderEntryStep1Serializer(serializers.ModelSerializer):
    class Meta:
        model = OrderEntry
        fields = ["order_type", "production_type", "assembly_type"]

    def validate(self, data):
        if data["order_type"] == "production" and not data.get("production_type"):
            raise serializers.ValidationError(
                {"production_type": "Required for production order"}
            )
        return data


# ---------------- Order Product ----------------
class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = ["id", "name"]


# ---------------- Order Batch ----------------
class OrderBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderBatch
        fields = ["id", "batch_number", "available_stock"]


# ---------------- Sales Order ----------------
class SalesOrderCreateSerializer(serializers.ModelSerializer):
    """
    Accepts:
    - product-device_model (string)
    - batch (string: batch_number)
    """

    product_device_model = serializers.CharField(write_only=True, required=True)
    batch = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = SalesOrder
        exclude = ("product", "batch")

    def validate(self, data):
        product_name = data.pop("product_device_model")
        batch_number = data.pop("batch")

        # 1️ Resolve product
        try:
            product = OrderProduct.objects.get(name=product_name)
        except OrderProduct.DoesNotExist:
            raise serializers.ValidationError(
                {"product-device_model": "Invalid product / device model."}
            )

        # 2️ Resolve batch (must belong to product)
        try:
            batch = OrderBatch.objects.get(product=product, batch_number=batch_number)
        except OrderBatch.DoesNotExist:
            raise serializers.ValidationError(
                {"batch": "Invalid batch for selected product."}
            )

        data["product"] = product
        data["batch"] = batch

        # 3️ Stock validation
        if data["quantity"] > batch.available_stock:
            raise serializers.ValidationError(
                {"quantity": f"Only {batch.available_stock} units available."}
            )

        # 4️ Grand total validation
        calculated = SalesOrder(**data).calculate_grand_total()
        if calculated != data["grand_total"]:
            raise serializers.ValidationError(
                {"grand_total": "Grand total mismatch with backend calculation."}
            )

        return data


# ---------------- Production Order ----------------
class ProductionOrderCreateSerializer(serializers.ModelSerializer):
    product_device_model = serializers.CharField(write_only=True)
    batch_number = serializers.CharField(write_only=True)
    supplier_vendor_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ProductionOrder
        exclude = ("product", "batch", "supplier_vendor")

    def validate(self, data):
        # Resolve product
        try:
            product = OrderProduct.objects.get(name=data.pop("product_device_model"))
        except OrderProduct.DoesNotExist:
            raise serializers.ValidationError(
                {"product_device_model": "Invalid product/device model."}
            )

        # Resolve supplier
        try:
            supplier = SupplierVendor.objects.get(id=data.pop("supplier_vendor_id"))
        except SupplierVendor.DoesNotExist:
            raise serializers.ValidationError(
                {"supplier_vendor": "Invalid supplier/vendor."}
            )

        # Resolve or create batch per product
        batch, _ = OrderBatch.objects.get_or_create(
            product=product,
            batch_number=data.pop("batch_number"),
            defaults={"available_stock": 0},
        )

        data["product"] = product
        data["supplier_vendor"] = supplier
        data["batch"] = batch

        # Validate total value
        calculated = data["quantity_added"] * data["unit_price"]
        if calculated != data["total_value"]:
            raise serializers.ValidationError(
                {"total_value": "Total value mismatch with backend calculation."}
            )

        return data


# ---------------- Step-2 (Make To Order) ----------------
class OrderEntryStep2MakeToOrderSerializer(serializers.ModelSerializer):
    product_device_model = serializers.CharField(write_only=True)

    class Meta:
        model = OrderEntryMakeToOrder
        exclude = ("order_entry", "product")

    def validate(self, data):
        # 1. Resolve product from UI value
        try:
            product = OrderProduct.objects.get(name=data.pop("product_device_model"))
        except OrderProduct.DoesNotExist:
            raise serializers.ValidationError(
                {"product_device_model": "Invalid Product / Device Model"}
            )

        data["product"] = product

        # 2. Backend grand total calculation
        base = data["quantity"] * data["unit_price"]
        discount = (base * data["discount_percent"]) / Decimal("100")
        taxable = base - discount
        gst = (taxable * data["gst_percent"]) / Decimal("100")
        calculated_total = taxable + gst + data["shipping_charges"]

        if calculated_total != data["grand_total"]:
            raise serializers.ValidationError(
                {"grand_total": "Grand total mismatch with backend calculation"}
            )

        # 3. Advance payment check
        if data["advance_payment"] > data["grand_total"]:
            raise serializers.ValidationError(
                {"advance_payment": "Advance payment cannot exceed grand total"}
            )

        return data


# ------------------------- Request For Quote (RFQ) Step 1 --------------------------
# Step-1 Serializer
class RFQStep1Serializer(serializers.ModelSerializer):
    class Meta:
        model = RequestForQuote
        fields = [
            "order_reference",
            "device_name",
            "assembly_type",
            "quantity",
        ]


# -------------------------- Request For Quote (RFQ) Step 2 --------------------------
class RFQStep2Serializer(serializers.Serializer):
    bom_parts = serializers.ListField(child=serializers.CharField(), required=False)
    components = serializers.ListField(child=serializers.CharField(), required=False)
    services = serializers.ListField(child=serializers.CharField(), required=False)


# -------------------------- Request For Quote (RFQ) Step 3 --------------------------
class RFQStep3Serializer(serializers.Serializer):
    vendor_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    srn_no = serializers.ChoiceField(choices=RequestForQuote.SRN_CHOICES)
    delivery_date = serializers.DateField()
    delivery_address = serializers.CharField()
    additional_requirements = serializers.CharField(required=False, allow_blank=True)


# ------------------ Create Purchase Order STEP 1 ------------------
class PurchaseStep1Serializer(serializers.Serializer):
    buyer_name = serializers.CharField()
    order_id = serializers.CharField()
    rfq_id = serializers.CharField()

    assembly_type = serializers.ChoiceField(choices=PurchaseOrder.ASSEMBLY_TYPE_CHOICES)

    order_types = serializers.ListField(
        child=serializers.ChoiceField(choices=["bom", "component", "service"]),
        min_length=1,
    )


# ---------- Create Purchase Order STEP 2 ----------
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
class QCInspectorRegistrationSerializer(serializers.ModelSerializer):
    aadhar_document = serializers.FileField(validators=[validate_file_size])
    pan_document = serializers.FileField(validators=[validate_file_size])

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
        ]

    def validate(self, data):
        # State → District dependency (implied by dropdown behavior)
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError(
                {"district": "Selected district does not belong to selected state."}
            )
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
        # Enforce State → District dependency (visible in UI)
        if data["district"].state_id != data["state"].id:
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
        # Enforce State → District dependency (visible in UI)
        if data["district"].state_id != data["state"].id:
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
        # Enforce State → District dependency (visible in UI)
        if data["district"].state_id != data["state"].id:
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

    class Meta:
        model = Sticker
        fields = [
            "name",
            "dimensions",
            "quantity",
            "file_name",
        ]
        read_only_fields = fields

    def get_dimensions(self, obj):
        return f"{obj.length} × {obj.breadth} mm"

    def get_file_name(self, obj):
        if obj.file:
            return obj.file.name.split("/")[-1]
        return None


class BOMComponentDetailSerializer(serializers.ModelSerializer):
    """BOM component/item details"""

    class Meta:
        model = BOMComponent
        fields = ["identification_mark", "description", "per_device_quantity"]
        read_only_fields = fields


class BOMDetailSerializer(serializers.ModelSerializer):
    """BOM with components for device view"""

    items = serializers.SerializerMethodField()

    class Meta:
        model = BOM
        fields = ["upload_type", "items", "bom_file"]
        read_only_fields = fields

    def get_items(self, obj):
        """Return BOM components as items list"""
        components = obj.components.all()

        # Map components to item types based on upload_type
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
    """User manual details"""

    file_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = UserManual
        fields = ["file_name", "file_url"]
        read_only_fields = fields

    def get_file_name(self, obj):
        """Extract filename from file field"""
        if obj.file:
            return obj.file.name.split("/")[-1]
        return None

    def get_file_url(self, obj):
        """Return file URL"""
        if obj.file:
            return self.context.get("request").build_absolute_uri(obj.file.url)
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


# ----------------------- RFQ List Serializer -----------------------
class RFQListSerializer(serializers.ModelSerializer):
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
            "quantity",
            "assembly_type",
            "delivery_date",
            "created_at",
            "status",
            "status_display",
            "vendor_names",
            "bom_parts_count",
            "components_count",
        ]

    def get_vendor_names(self, obj):
        """Extract unique vendor names from RFQ quotations"""
        vendor_names = list(
            obj.quotations.values_list("vendor__name", flat=True).distinct()
        )
        return vendor_names

    def get_bom_parts_count(self, obj):
        """Count BOM parts in selections"""
        return obj.selections.filter(item_type="bom").count()

    def get_components_count(self, obj):
        """Count components in selections"""
        return obj.selections.filter(item_type="component").count()


# ----------------------- RFQ Selection Serializer -----------------------
class RFQSelectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFQSelection
        fields = ["id", "item_type", "reference"]


# ----------------------- RFQ Detail Serializer -----------------------
class RFQDetailSerializer(serializers.ModelSerializer):
    selections = RFQSelectionSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    assembly_type_display = serializers.CharField(
        source="get_assembly_type_display", read_only=True
    )
    bom_parts = serializers.SerializerMethodField()
    other_components = serializers.SerializerMethodField()
    vendor_names = serializers.SerializerMethodField()

    class Meta:
        model = RequestForQuote
        fields = [
            "id",
            "order_reference",
            "device_name",
            "quantity",
            "assembly_type",
            "assembly_type_display",
            "delivery_date",
            "delivery_address",
            "additional_requirements",
            "created_at",
            "status",
            "status_display",
            "selections",
            "bom_parts",
            "other_components",
            "vendor_names",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "status",
            "selections",
        ]

    def get_bom_parts(self, obj):
        """Extract BOM part references"""
        return list(
            obj.selections.filter(item_type="bom").values_list("reference", flat=True)
        )

    def get_other_components(self, obj):
        """Extract component references"""
        return list(
            obj.selections.filter(item_type="component").values_list(
                "reference", flat=True
            )
        )

    def get_vendor_names(self, obj):
        """Extract vendor names from RFQ quotations"""
        vendor_names = list(
            obj.quotations.values_list("vendor__name", flat=True).distinct()
        )
        return vendor_names


# ----------------------- RFQ Quotation Serializer -----------------------
# class RFQQuotationCreateSerializer(serializers.ModelSerializer):
#     """Serializer for creating/updating quotation rates"""

#     class Meta:
#         model = RFQQuotation
#         fields = ["id", "rfq", "vendor", "quotation_rate", "status"]
#         read_only_fields = ["id"]

#     def validate_quotation_rate(self, value):
#         if value is not None and value < 0:
#             raise serializers.ValidationError("Quotation rate cannot be negative.")
#         return value


# class RFQQuotationSerializer(serializers.ModelSerializer):
#     """Serializer for reading quotation details"""
#     vendor_name = serializers.CharField(source="vendor.name", read_only=True)
#     status_display = serializers.CharField(source="get_status_display", read_only=True)

#     class Meta:
#         model = RFQQuotation
#         fields = [
#             "id",
#             "rfq",
#             "vendor",
#             "vendor_name",
#             "quotation_rate",
#             "status",
#             "status_display",
#             "quotation_date",
#             "created_at",
#             "updated_at",
#         ]
#         read_only_fields = ["id", "created_at", "updated_at"]


# ============================================================================
# ======================= QUOTATION SERIALIZERS =============================
# ============================================================================


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
