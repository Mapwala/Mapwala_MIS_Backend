from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework import serializers
from decimal import Decimal
from .models import *
import json


# ---------------- File Size Validator ----------------
def validate_file_size(file):
    max_size = settings.FILE_UPLOAD_MAX_MEMORY_SIZE

    if file.size > max_size:
        raise serializers.ValidationError(
            f"File size must be less than or equal to {max_size // (1024 * 1024)} MB."
        )


# ---------------- Login ----------------
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    accepted_terms = serializers.BooleanField()

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
        fields = "__all__"

    def validate(self, data):
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError(
                "Selected district does not belong to the selected state."
            )
        return data


# ---------------- Registrations ----------------
class B2CCustomerRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = B2CCustomer
        fields = ["name","phone_number","email","address","state","district","bank_name","account_holder_name","account_number","ifsc_code","gst_number","gst_document","tan_number","tan_document","pan_number","pan_document",]

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
        fields = ["partner_name","phone_number","email","address","state","district","bank_name","account_holder_name","account_number","ifsc_code","gst_number","gst_document","tan_number","tan_document","pan_number","pan_document",]

    def validate(self, data):
        state = data.get("state")
        district = data.get("district")

        if district.state_id != state.id:
            raise serializers.ValidationError({
                "district": "Selected district does not belong to selected state."
            })

        return data


# ---------------- Distributor Registration ----------------
class DistributorRegistrationSerializer(serializers.ModelSerializer):
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
        model = Distributor
        fields = ["name","phone_number","email","address","state","district","bank_name","account_holder_name","account_number","ifsc_code","gst_number","gst_document","tan_number","tan_document","pan_number","pan_document","linked_to","manufacturer","authorised_states","authorised_districts",
        ]

    def validate(self, data):
        # 1️ Address validation
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError({
                "district": "District does not belong to selected state."
            })

        # 2️ Linked-to validation
        if data["linked_to"] == "manufacturer" and not data.get("manufacturer"):
            raise serializers.ValidationError({
                "manufacturer": "Manufacturer is required when Linked To is Manufacturer."
            })

        # 3️ Authorised area validation (MULTI)
        authorised_states = data["authorised_states"]
        authorised_districts = data["authorised_districts"]

        state_ids = {state.id for state in authorised_states}

        for district in authorised_districts:
            if district.state_id not in state_ids:
                raise serializers.ValidationError({
                    "authorised_districts": (
                        f"District '{district.name}' does not belong "
                        f"to selected authorised states."
                    )
                })

        return data


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
        fields = ["name","phone_number","email","address","state","district","bank_name","account_holder_name","account_number","ifsc_code","gst_number","gst_document","tan_number","tan_document","pan_number","pan_document","linked_to","manufacturer","distributor","authorised_states","authorised_districts",
        ]

    def validate(self, data):
        # 1️ Address check
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError({
                "district": "District does not belong to selected state."
            })

        linked_to = data["linked_to"]
        manufacturer = data.get("manufacturer")
        distributor = data.get("distributor")

        # 2️ Linking logic
        if linked_to == "manufacturer":
            if not manufacturer:
                raise serializers.ValidationError({
                    "manufacturer": "Manufacturer is required when Linked To is Manufacturer."
                })
            if distributor:
                raise serializers.ValidationError({
                    "distributor": "Distributor must be empty when linked to Manufacturer."
                })

        if linked_to == "distributor":
            if not distributor:
                raise serializers.ValidationError({
                    "distributor": "Distributor is required when Linked To is Distributor."
                })
            if manufacturer:
                raise serializers.ValidationError({
                    "manufacturer": "Manufacturer must be empty when linked to Distributor."
                })

        # 3️ Authorised area validation (MULTI)
        state_ids = {s.id for s in data["authorised_states"]}

        for district in data["authorised_districts"]:
            if district.state_id not in state_ids:
                raise serializers.ValidationError({
                    "authorised_districts": (
                        f"District '{district.name}' does not belong "
                        f"to selected authorised states."
                    )
                })

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
            raise serializers.ValidationError({
                "party": f"{party_type.upper()} must be selected"
            })

        # ✅ Ensure only ONE party is filled
        for key, value in party_fields.items():
            if key != party_type and value:
                raise serializers.ValidationError({
                    key: "This field must be empty"
                })

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
            raise serializers.ValidationError({
                "bom_file": "Excel file required for bulk upload"
            })

        if upload_type == "individual" and bom_file:
            raise serializers.ValidationError({
                "bom_file": "Do not upload Excel file for individual entry"
            })

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
            raise serializers.ValidationError({"production_type": "Required for production order"})
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

    product_device_model = serializers.CharField(
        write_only=True,
        required=True
    )
    batch = serializers.CharField(
        write_only=True,
        required=True
    )

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
            raise serializers.ValidationError({
                "product-device_model": "Invalid product / device model."
            })

        # 2️ Resolve batch (must belong to product)
        try:
            batch = OrderBatch.objects.get(
                product=product,
                batch_number=batch_number
            )
        except OrderBatch.DoesNotExist:
            raise serializers.ValidationError({
                "batch": "Invalid batch for selected product."
            })

        data["product"] = product
        data["batch"] = batch

        # 3️ Stock validation
        if data["quantity"] > batch.available_stock:
            raise serializers.ValidationError({
                "quantity": f"Only {batch.available_stock} units available."
            })

        # 4️ Grand total validation
        calculated = SalesOrder(**data).calculate_grand_total()
        if calculated != data["grand_total"]:
            raise serializers.ValidationError({
                "grand_total": "Grand total mismatch with backend calculation."
            })

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
            product = OrderProduct.objects.get(
                name=data.pop("product_device_model")
            )
        except OrderProduct.DoesNotExist:
            raise serializers.ValidationError({
                "product_device_model": "Invalid product/device model."
            })

        # Resolve supplier
        try:
            supplier = SupplierVendor.objects.get(
                id=data.pop("supplier_vendor_id")
            )
        except SupplierVendor.DoesNotExist:
            raise serializers.ValidationError({
                "supplier_vendor": "Invalid supplier/vendor."
            })

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
        calculated = (
            data["quantity_added"] * data["unit_price"]
        )
        if calculated != data["total_value"]:
            raise serializers.ValidationError({
                "total_value": "Total value mismatch with backend calculation."
            })

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
            product = OrderProduct.objects.get(
                name=data.pop("product_device_model")
            )
        except OrderProduct.DoesNotExist:
            raise serializers.ValidationError({
                "product_device_model": "Invalid Product / Device Model"
            })

        data["product"] = product

        # 2. Backend grand total calculation
        base = data["quantity"] * data["unit_price"]
        discount = (base * data["discount_percent"]) / Decimal("100")
        taxable = base - discount
        gst = (taxable * data["gst_percent"]) / Decimal("100")
        calculated_total = taxable + gst + data["shipping_charges"]

        if calculated_total != data["grand_total"]:
            raise serializers.ValidationError({
                "grand_total": "Grand total mismatch with backend calculation"
            })
            
        # 3. Advance payment check
        if data["advance_payment"] > data["grand_total"]:
            raise serializers.ValidationError({
                "advance_payment": "Advance payment cannot exceed grand total"
            })

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
    bom_parts = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    components = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    services = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


# -------------------------- Request For Quote (RFQ) Step 3 --------------------------
class RFQStep3Serializer(serializers.Serializer):
    vendor_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    srn_no = serializers.ChoiceField(
        choices=RequestForQuote.SRN_CHOICES
    )
    delivery_date = serializers.DateField()
    delivery_address = serializers.CharField()
    additional_requirements = serializers.CharField(
        required=False, allow_blank=True
    )


# ------------------ Create Purchase Order STEP 1 ------------------
class PurchaseStep1Serializer(serializers.Serializer):
    buyer_name = serializers.CharField()
    order_id = serializers.CharField()
    rfq_id = serializers.CharField()

    assembly_type = serializers.ChoiceField(
        choices=PurchaseOrder.ASSEMBLY_TYPE_CHOICES
    )

    order_types = serializers.ListField(
        child=serializers.ChoiceField(
            choices=["bom", "component", "service"]
        ),
        min_length=1
    )


# ---------- Create Purchase Order STEP 2 ----------
class PurchaseLineSerializer(serializers.Serializer):
    item_code = serializers.CharField()
    item_type = serializers.ChoiceField(
        choices=["bom", "component", "service"]
    )
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
    unit_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )
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
        fields = ["id", "account_name", "phone_number", "email", "address", "state", "district", "aadhar_number", "aadhar_document", "pan_number", "pan_document" ]

    def validate(self, data):
        # Enforce State → District dependency (visible in UI)
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError({
                "district": "Selected district does not belong to selected state."
            })
        return data


# ---------------- Module Management QC Inspector Registration ----------------
class QCInspectorRegistrationSerializer(serializers.ModelSerializer):
    aadhar_document = serializers.FileField(validators=[validate_file_size])
    pan_document = serializers.FileField(validators=[validate_file_size])

    class Meta:
        model = QCInspectorRegistration
        fields = ["id","qc_inspector_name","phone_number","email","address","state","district","aadhar_number","aadhar_document","pan_number","pan_document"]

    def validate(self, data):
        # State → District dependency (implied by dropdown behavior)
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError({
                "district": "Selected district does not belong to selected state."
            })
        return data


# ---------------- Module Management Purchase Department Registration ----------------
class PurchaseDepartmentRegistrationSerializer(serializers.ModelSerializer):
    aadhar_document = serializers.FileField(validators=[validate_file_size])
    pan_document = serializers.FileField(validators=[validate_file_size])
    class Meta:
        model = PurchaseDepartmentRegistration
        fields = ["id","purchase_department_name","phone_number","email","address","state","district","aadhar_number","aadhar_document","pan_number","pan_document"]
        
    def validate(self, data):
        # Enforce State → District dependency (visible in UI)
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError({
                "district": "Selected district does not belong to selected state."
            })
        return data


# ---------------- Module Management Store Manager Registration ----------------
class StoreManagerRegistrationSerializer(serializers.ModelSerializer):
    aadhar_document = serializers.FileField(validators=[validate_file_size])
    pan_document = serializers.FileField(validators=[validate_file_size])
    class Meta:
        model = StoreManagerRegistration
        fields = ["id","store_manager_name","phone_number","email","address","state","district","aadhar_number","aadhar_document","pan_number","pan_document"]
        
    def validate(self, data):
        # Enforce State → District dependency (visible in UI)
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError({
                "district": "Selected district does not belong to selected state."
            })
        return data


# ---------------- Module Management Repair Technician Registration ----------------
class RepairTechnicianRegistrationSerializer(serializers.ModelSerializer):
    aadhar_document = serializers.FileField(validators=[validate_file_size])
    pan_document = serializers.FileField(validators=[validate_file_size])
    class Meta:
        model = RepairTechnicianRegistration
        fields = ["id","repair_technician_name","phone_number","email","address","state","district","aadhar_number","aadhar_document","pan_number","pan_document"]
        
    def validate(self, data):
        # Enforce State → District dependency (visible in UI)
        if data["district"].state_id != data["state"].id:
            raise serializers.ValidationError({
                "district": "Selected district does not belong to selected state."
            })
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
    dispatch_status_display = serializers.CharField(source="get_dispatch_status_display", read_only=True)
    
    class Meta:
        model = StoreTransfer
        fields = ["id","transfer_id","product_id","product_name","category","category_name","mrn_number","batch_number","vendor","vendor_name","quantity","unit_price","total_value","transfer_date","dispatch_status","dispatch_status_display","created_at"]
        read_only_fields = ["id","product_name","vendor_name","dispatch_status_display","created_at"]


# ---------------- Detailed View Serializer ----------------
class StoreTransferDetailSerializer(serializers.ModelSerializer):
    """Detailed view with all information including creator"""
    product_name = serializers.CharField(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    dispatch_status_display = serializers.CharField(source="get_dispatch_status_display", read_only=True)
    
    class Meta:
        model = StoreTransfer
        fields = ["id","transfer_id","product_id","product_name","category","category_name","mrn_number","batch_number","vendor","vendor_name","quantity","unit_price","total_value","transfer_date","dispatch_status","dispatch_status_display","created_at","updated_at","created_by","created_by_username"]
        read_only_fields = ["id","product_name","vendor_name","created_by_username","dispatch_status_display","created_at","updated_at"]


# ------------- Create and Update Serializer -----------------
class StoreTransferCreateUpdateSerializer(serializers.ModelSerializer):
    """Create and update operations"""
    
    class Meta:
        model = StoreTransfer
        fields = ["product","product_name","category","mrn_number","batch_number","vendor","quantity","unit_price","total_value","transfer_date","dispatch_status"]
    
    def validate(self, data):
        # Validate quantity
        if data.get("quantity", 0) <= 0:
            raise serializers.ValidationError({
                "quantity": "Quantity must be greater than 0."
            })
        
        # Validate unit_price
        if data.get("unit_price", 0) < 0:
            raise serializers.ValidationError({
                "unit_price": "Unit price cannot be negative."
            })
        
        # Validate total_value matches quantity * unit_price
        quantity = data.get("quantity")
        unit_price = data.get("unit_price")
        total_value = data.get("total_value")
        
        if quantity and unit_price:
            expected_total = Decimal(str(quantity)) * Decimal(str(unit_price))
            if Decimal(str(total_value)) != expected_total:
                raise serializers.ValidationError({
                    "total_value": f"Total value must equal quantity × unit_price. Expected: {expected_total}"
                })
        
        return data


# ------------- DEBIT NOTES & CREDIT NOTES - ACCOUNT MANAGEMENT -----------------
class DebitNoteListSerializer(serializers.ModelSerializer):
    """List view for debit notes with essential fields"""
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    
    class Meta:
        model = DebitNote
        fields = ["id","number","date","vendor","reason","reason_display","amount","status","status_display","created_by_name","created_at"]
        read_only_fields = ["number", "created_at", "created_by_name", "reason_display", "status_display"]


# ------------- Debit Note Detail Serializer -----------------
class DebitNoteDetailSerializer(serializers.ModelSerializer):
    """Detail view for single debit note"""
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    
    class Meta:
        model = DebitNote
        fields = ["id","number","date","vendor","reason","reason_display","amount","status","status_display","reference_document","remarks","created_by_name","created_at","updated_at"]
        read_only_fields = ["number", "created_at", "updated_at", "created_by_name", "reason_display", "status_display"]


# ------------- Create and Update Serializer -----------------
class DebitNoteCreateUpdateSerializer(serializers.ModelSerializer):
    """Create and update serializer for debit notes"""
    number = serializers.CharField(read_only=True)
    
    class Meta:
        model = DebitNote
        fields = ["number","vendor","reason","amount","reference_document","remarks","status"]
    
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
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    
    class Meta:
        model = CreditNote
        fields = ["id","number","date","customer","reason","reason_display","amount","status","status_display","created_by_name","created_at"]
        read_only_fields = ["number", "created_at", "created_by_name", "reason_display", "status_display"]


# ------------- Credit Note Detail Serializer -----------------
class CreditNoteDetailSerializer(serializers.ModelSerializer):
    """Detail view for single credit note"""
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    
    class Meta:
        model = CreditNote
        fields = ["id","number","date","customer","reason","reason_display","amount","status","status_display","reference_document","remarks","created_by_name","created_at","updated_at"]
        read_only_fields = ["number", "created_at", "updated_at", "created_by_name", "reason_display", "status_display"]


# ------------- Create and Update Serializer -----------------
class CreditNoteCreateUpdateSerializer(serializers.ModelSerializer):
    """Create and update serializer for credit notes"""
    number = serializers.CharField(read_only=True)
    
    class Meta:
        model = CreditNote
        fields = ["number","customer","reason","amount","reference_document","remarks","status"]
    
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
        source='created_by.username',
        read_only=True
    )

    class Meta:
        model = ReturnRequest
        fields = ['id','return_number','date','items','reason','amount','status','created_at','updated_at','created_by_username']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_username']

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
        fields = ['id','return_number','date','items','reason','amount','status']


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
        source='created_by.username',
        read_only=True
    )

    class Meta:
        model = RepairRecord
        fields = ['id','product_id','product_name','vendor','mrn_number','failed_qty','repaired_qty','rejected_qty','repair_pending','repair_type','repair_center','status','created_at','updated_at','created_by_username']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_username']

    def validate(self, data):
        """Validate repair quantities"""
        if data.get('repaired_qty', 0) + data.get('rejected_qty', 0) > data.get('failed_qty', 0):
            raise serializers.ValidationError(
                "Repaired Qty + Rejected Qty cannot exceed Failed Qty"
            )
        
        repair_pending = data.get('repair_pending', 0)
        if repair_pending < 0:
            raise serializers.ValidationError("Repair Pending cannot be negative")
        
        return data


class RepairRecordListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    class Meta:
        model = RepairRecord
        fields = ['id','product_id','product_name','vendor','mrn_number','failed_qty','repaired_qty','rejected_qty','repair_pending','repair_type','repair_center','status']


# ============================================================
# REJECTED ITEM SERIALIZERS
# ============================================================
class RejectedItemSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True
    )

    class Meta:
        model = RejectedItem
        fields = ['id','product_id','product_name','vendor','mrn_number','rejected_qty','qc_date','created_at','updated_at','created_by_username']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_username']

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
        fields = ['id','product_id','product_name','vendor','mrn_number','rejected_qty','qc_date']


