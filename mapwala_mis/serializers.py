from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import *


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


