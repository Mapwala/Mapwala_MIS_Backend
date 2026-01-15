from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import AccessToken
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db import transaction
from collections import defaultdict
from rest_framework.throttling import ScopedRateThrottle
from decimal import Decimal

from .serializers import *
from .models import *



# ---------------- Login API ----------------
class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]  # ← ADD THIS
    throttle_scope = "login" 

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        # Save terms acceptance
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.accepted_terms = True
        profile.accepted_at = timezone.now()
        profile.save()

        # Generate JWT tokens
        access_token = AccessToken.for_user(user)

        return Response(
            {
                "message": "Login successful",
                "access_token": str(access_token),
                "expires_in_hours": 24,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                },
            },
            status=status.HTTP_200_OK,
        )


# ---------------- State ViewSet ----------------
class StateViewSet(ModelViewSet):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["name"]

    @action(detail=False, methods=["get"])
    def active(self, request):
        queryset = self.get_queryset().filter(status="active")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        state = self.get_object()
        state_name = state.name

        # Prevent deletion if districts exist
        if state.districts.exists():
            return Response(
                {
                    "success": False,
                    "message": f"State '{state_name}' cannot be deleted because it has linked districts."
                },
                status=status.HTTP_409_CONFLICT,
            )

        self.perform_destroy(state)

        return Response(
            {
                "success": True,
                "message": f"State '{state_name}' deleted successfully."
            },
            status=status.HTTP_200_OK,
        )


#   ---------------- District ViewSet ----------------
class DistrictViewSet(ModelViewSet):
    queryset = District.objects.select_related("state").all()
    serializer_class = DistrictSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["name", "code"]

    def get_queryset(self):
        queryset = super().get_queryset()
        state_id = self.request.query_params.get("state")
        if state_id:
            queryset = queryset.filter(state_id=state_id)
        return queryset


# ---------------- Parent Company ViewSet ----------------
class ParentCompanyViewSet(ModelViewSet):
    queryset = ParentCompany.objects.all()
    serializer_class = ParentCompanySerializer
    permission_classes = [IsAuthenticated]


# ---------------- Vendor ViewSet ----------------
class VendorViewSet(ModelViewSet):
    queryset = Vendor.objects.select_related("state", "district").all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]

# ---------------- Registrations ----------------
class B2CCustomerRegistrationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = B2CCustomerRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()

        return Response(
            {
                "message": "B2C Customer registered successfully",
                "customer_id": customer.id,
                "name": customer.name,
                "email": customer.email,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- B2B Partner Registration ----------------
class B2BPartnerRegistrationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = B2BPartnerRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        partner = serializer.save()

        return Response(
            {
                "message": "B2B Partner registered successfully",
                "partner_id": partner.id,
                "partner_name": partner.partner_name,
                "email": partner.email,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- Distributor Registration ----------------
class DistributorRegistrationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = DistributorRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        authorised_states = serializer.validated_data.pop("authorised_states")
        authorised_districts = serializer.validated_data.pop("authorised_districts")

        distributor = Distributor.objects.create(**serializer.validated_data)

        distributor.authorised_states.set(authorised_states)
        distributor.authorised_districts.set(authorised_districts)

        return Response(
            {
                "message": "Distributor registered successfully",
                "distributor_id": distributor.id,
                "name": distributor.name,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- Distributor Registration ----------------
class DealerRegistrationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = DealerRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        authorised_states = serializer.validated_data.pop("authorised_states")
        authorised_districts = serializer.validated_data.pop("authorised_districts")

        dealer = Dealer.objects.create(**serializer.validated_data)

        dealer.authorised_states.set(authorised_states)
        dealer.authorised_districts.set(authorised_districts)

        return Response(
            {
                "message": "Dealer registered successfully",
                "dealer_id": dealer.id,
                "name": dealer.name,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- Proforma Invoice Create ----------------
class ProformaInvoiceCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProformaInvoiceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pi = serializer.save()

        return Response(
            {
                "message": "Proforma Invoice created successfully",
                "pi_id": pi.id,
                "grand_total": pi.grand_total,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- STEP 1 ----------------
class DeviceStep1APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device = Device.objects.create(created_by=request.user)
        serializer = DeviceInformationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response({
            "device_id": device.id,
            "message": "Step 1 completed"
        }, status=201)


# ---------------- STEP 2 ----------------
class DeviceStep2APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device = get_object_or_404(Device, id=request.data["device_id"])
        serializer = BOMSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response({"message": "Step 2 completed"})


# ---------------- STEP 3 ----------------
class DeviceStep3APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        bom = get_object_or_404(BOM, device_id=request.data["device_id"])
        serializer = BOMComponentSerializer(
            data=request.data["components"],
            many=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(bom=bom)

        return Response({"message": "Step 3 completed"})


# ---------------- STEP 4 ----------------

class DeviceStep4APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device = get_object_or_404(Device, id=request.data["device_id"])
        serializer = EnclosureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response({"message": "Step 4 completed"})


# ---------------- STEP 5 ----------------

class DeviceStep5APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device = get_object_or_404(Device, id=request.data["device_id"])
        serializer = WireHarnessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response({"message": "Step 5 completed"})


# ---------------- STEP 6 ----------------
class DeviceStep6APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device = get_object_or_404(Device, id=request.data["device_id"])
        serializer = BatterySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response({"message": "Step 6 completed"})


# ---------------- STEP 7 ----------------
class DeviceStep7APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device = get_object_or_404(Device, id=request.data["device_id"])
        serializer = SOSButtonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response({"message": "Step 7 completed"})


# ---------------- STEP 8 ----------------
class DeviceStep8APIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        device = Device.objects.get(id=request.data["device_id"])

        # 🔹 Rebuild stickers array from multipart keys
        stickers_map = defaultdict(dict)

        for key, value in request.data.items():
            if key.startswith("stickers["):
                # Example key: stickers[0][name]
                index = key.split("[")[1].split("]")[0]
                field = key.split("[")[2].replace("]", "")
                stickers_map[index][field] = value

        stickers_list = list(stickers_map.values())

        serializer = StickerSerializer(data=stickers_list, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response({"message": "Step 8 completed"})



# ---------------- STEP 9 ----------------
class DeviceStep9APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device = get_object_or_404(Device, id=request.data["device_id"])
        serializer = UserManualSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response({"message": "Step 9 completed"})


# ---------------- STEP 10 ----------------
class DeviceAccessoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device = get_object_or_404(Device, id=request.data["device_id"])
        serializer = AccessorySerializer(
            data=request.data["accessories"],
            many=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        device.status = "completed"
        device.save()

        return Response({"message": "Device creation completed"})


# ---------------- Order Entry Step 1 ----------------
class OrderEntryStep1APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        entry, _ = OrderEntry.objects.get_or_create(
            user=request.user,
            is_step2_complete=False
        )


        serializer = OrderEntryStep1Serializer(entry, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(is_step1_complete=True)

        return Response(
            {"entry_id": entry.id},
            status=status.HTTP_200_OK
        )


# ---------------- Order Products, Batches, Sales Order ----------------
class OrderProductListAPIView(APIView):
    """
    UI: Product / Device Model dropdown
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = OrderProduct.objects.all()
        return Response(OrderProductSerializer(products, many=True).data)


# ---------------- Order Batches ----------------
class OrderBatchListAPIView(APIView):
    """
    UI: Batch dropdown depends on selected product
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        product_id = request.query_params.get("product_id")

        if not product_id:
            return Response(
                {"product_id": "product_id query param is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        batches = OrderBatch.objects.filter(product_id=product_id)
        return Response(OrderBatchSerializer(batches, many=True).data)


# ---------------- Sales Order Create ----------------
class SalesOrderCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = SalesOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = serializer.save()
        batch = OrderBatch.objects.select_for_update().get(id=order.batch.id)


        batch.available_stock -= order.quantity
        batch.save(update_fields=["available_stock"])

        return Response(
            {
                "message": "Sales order created successfully",
                "order_id": order.id,

                "product": {
                    "id": order.product.id,
                    "name": order.product.name,
                },

                "batch": {
                    "id": order.batch.id,
                    "batch_number": order.batch.batch_number,
                },

                "remaining_stock": batch.available_stock,
                "grand_total": float(order.grand_total),
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- Production Order - Add to Stock  Step 2 of Order Entry ----------------
class ProductionOrderCreateAPIView(APIView):
    """
    Production Order – Add to Stock
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = ProductionOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = serializer.save()

        # Increase stock safely
        batch = OrderBatch.objects.select_for_update().get(
            id=order.batch.id
        )
        batch.available_stock += order.quantity_added
        batch.save(update_fields=["available_stock"])

        return Response(
            {
                "message": "Production order created and stock added successfully",
                "production_order_id": order.id,
                "product": {
                    "id": order.product.id,
                    "name": order.product.name,
                },
                "batch": {
                    "id": batch.id,
                    "batch_number": batch.batch_number,
                },
                "added_quantity": order.quantity_added,
                "current_stock": batch.available_stock,
                "total_value": float(order.total_value),
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- ProductDropdown APIView ----------------
class ProductDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"id": p.id, "name": p.name}
            for p in OrderProduct.objects.all()
        ])


# ---------------- SupplierVendor Dropdown APIView ----------------
class SupplierVendorDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"id": v.id, "name": v.name}
            for v in SupplierVendor.objects.all()
        ])

# ---------------- ProductCategory Dropdown APIView ----------------
class ProductCategoryDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": "gps_devices", "label": "GPS Devices"},
            {"key": "tracking_devices", "label": "Tracking Devices"},
            {"key": "iot_devices", "label": "IoT Devices"},
            {"key": "accessories", "label": "Accessories"},
            {"key": "components", "label": "Components"},
        ])


# ---------------- Order Entry Step 2 (Make To Order) ----------------
class OrderEntryStep2APIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        order_entry = get_object_or_404(
            OrderEntry,
            id=request.data.get("entry_id"),
            user=request.user,
            is_step1_complete=True,
            production_type="make_to_order"
        )

        if hasattr(order_entry, "make_to_order"):
            return Response(
                {"detail": "Step 2 already completed"},
                status=status.HTTP_409_CONFLICT
            )

        serializer = OrderEntryStep2MakeToOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        make_to_order = serializer.save(order_entry=order_entry)

        order_entry.is_step2_complete = True
        order_entry.save(update_fields=["is_step2_complete"])

        return Response(
            {
                "message": "Order Entry completed successfully",

                "order_entry": {
                    "id": order_entry.id,
                    "order_type": order_entry.order_type,
                    "production_type": order_entry.production_type,
                    "assembly_type": order_entry.assembly_type,
                    "is_step1_complete": order_entry.is_step1_complete,
                    "is_step2_complete": order_entry.is_step2_complete,
                    "created_at": order_entry.created_at,
                },

                "customer": {
                    "name": make_to_order.customer_name,
                    "type": make_to_order.customer_type,
                    "contact_person": make_to_order.contact_person,
                    "mobile_no": make_to_order.mobile_no,
                },

                "product": {
                    "id": make_to_order.product.id,
                    "name": make_to_order.product.name,
                },

                "order_summary": {
                    "quantity": make_to_order.quantity,
                    "unit_price": float(make_to_order.unit_price),
                    "discount_percent": float(make_to_order.discount_percent),
                    "gst_percent": float(make_to_order.gst_percent),
                    "shipping_charges": float(make_to_order.shipping_charges),
                    "grand_total": float(make_to_order.grand_total),
                    "advance_payment": float(make_to_order.advance_payment),
                },

                "delivery": {
                    "expected_delivery_date": make_to_order.expected_delivery_date,
                    "priority": make_to_order.order_priority,
                }
            },
            status=status.HTTP_201_CREATED
        )


# ---------------- CustomerType Dropdown APIView ----------------
class CustomerTypeDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": "b2b", "label": "B2B Partner"},
            {"key": "b2c", "label": "B2C Customer"},
            {"key": "distributor", "label": "Distributor"},
            {"key": "dealer", "label": "Dealer"},
        ])


# ---------------- Payment Terms Dropdown APIView ----------------
class PaymentTermsDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": "100_advance", "label": "100% Advance"},
            {"key": "50_50", "label": "50% Advance, 50% on Delivery"},
            {"key": "30_70", "label": "30% Advance, 70% on Delivery"},
            {"key": "net_30", "label": "Net 30 Days"},
            {"key": "net_60", "label": "Net 60 Days"},
            {"key": "custom", "label": "Custom Terms"},
        ])

# ---------------- Order Priority Dropdown APIView ----------------
class OrderPriorityDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": "low", "label": "Low"},
            {"key": "medium", "label": "Medium"},
            {"key": "high", "label": "High"},
            {"key": "urgent", "label": "Urgent"},
        ])


# ---------------- RFQ Step 1 ----------------
class RFQStep1APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RFQStep1Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rfq = serializer.save(created_by=request.user)

        return Response(
            {"rfq_id": rfq.id, "message": "Step 1 completed"},
            status=201
        )

# ---------------- RFQ Step 2 ----------------
class RFQStep2APIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        rfq = get_object_or_404(
            RequestForQuote,
            id=request.data.get("rfq_id"),
            status="draft"
        )

        serializer = RFQStep2Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rfq.selections.all().delete()

        for ref in serializer.validated_data.get("bom_parts", []):
            RFQSelection.objects.create(
                rfq=rfq,
                item_type="bom",
                reference=ref
            )

        for ref in serializer.validated_data.get("components", []):
            RFQSelection.objects.create(
                rfq=rfq,
                item_type="component",
                reference=ref
            )

        for ref in serializer.validated_data.get("services", []):
            RFQSelection.objects.create(
                rfq=rfq,
                item_type="service",
                reference=ref
            )

        return Response({"message": "Step 2 completed"})


# ---------------- RFQ STEP-3 API (FINAL SUBMIT) ----------------
class RFQStep3APIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        rfq = get_object_or_404(
            RequestForQuote,
            id=request.data.get("rfq_id"),
            status="draft"
        )

        serializer = RFQStep3Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rfq.srn_no = serializer.validated_data["srn_no"]
        rfq.delivery_date = serializer.validated_data["delivery_date"]
        rfq.delivery_address = serializer.validated_data["delivery_address"]
        rfq.additional_requirements = serializer.validated_data.get(
            "additional_requirements", ""
        )
        rfq.status = "submitted"
        rfq.save()

        return Response(
            {"message": "RFQ submitted successfully"},
            status=201
        )

class QuoteTypeDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": "components", "label": "Components"},
            {"key": "bom", "label": "Items (BOM Parts)"},
            {"key": "services", "label": "Services"},
        ])

class AssemblyTypeDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": "pcb_assembly", "label": "PCB Assembly"},
            {"key": "device_assembly", "label": "Device Assembly"},
        ])

class SRNDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": k, "label": v}
            for k, v in RequestForQuote.SRN_CHOICES
        ])

class VendorDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {
                "id": v.id,
                "label": f"{v.name} ({v.city})" if hasattr(v, "city") else v.name
            }
            for v in Vendor.objects.all()
        ])

# _____________________________________________________________________________



# ---------------- Create Purchase Order STEP 1 ----------------
class Step1APIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = PurchaseStep1Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        po = PurchaseOrder.objects.create(
            buyer_name=serializer.validated_data["buyer_name"],
            order_id=serializer.validated_data["order_id"],
            rfq_id=serializer.validated_data["rfq_id"],
            assembly_type=serializer.validated_data["assembly_type"],
            created_by=request.user
        )

        for ot in serializer.validated_data["order_types"]:
            PurchaseOrderType.objects.create(
                purchase_order=po,
                order_type=ot
            )

        return Response(
            {
                "purchase_order_id": po.id,
                "message": "Step 1 completed"
            },
            status=201
        )


# ---------------- Create Purchase Order STEP 2 ----------------
class Step2APIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        po = get_object_or_404(
            PurchaseOrder,
            id=request.data.get("purchase_order_id")
        )

        serializer = PurchaseStep2Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        po.wastage_percentage = serializer.validated_data["wastage_percentage"]
        po.selected_vendor_id = serializer.validated_data["selected_vendor_id"]
        po.delivery_date = serializer.validated_data["delivery_date"]
        po.payment_terms = serializer.validated_data["payment_terms"]
        po.save()

        po.items.all().delete()

        for item in serializer.validated_data["items"]:
            PurchaseOrderItem.objects.create(
                purchase_order=po,
                **item
            )

        return Response(
            {"message": "Purchase Order created successfully"},
            status=201
        )


# ---------------- Dropdowns for Purchase Order ----------------
class OrderTypeDropdown(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": "bom", "label": "Items (BOM Parts)"},
            {"key": "component", "label": "Components (Enclosure, Battery, etc.)"},
            {"key": "service", "label": "Services (Assembly, Quality Check, etc.)"},
        ])


class AssemblyTypeDropdown(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": "pcb", "label": "PCB Assembly"},
            {"key": "device", "label": "Device Assembly"},
        ])


class PaymentTermsDropdown(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": k, "label": v}
            for k, v in PurchaseOrder.PAYMENT_TERMS_CHOICES
        ])


# ---------------- Create Material Receipt Note (MRN) ----------------
from datetime import datetime

class MRNCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = MRNCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purchase_order = get_object_or_404(PurchaseOrder,id=serializer.validated_data["purchase_order_id"])
        vendor = get_object_or_404(Vendor,id=serializer.validated_data["vendor_id"])
        batch_number = f"MRN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        mrn = MaterialReceiptNote.objects.create(
            purchase_order=purchase_order,
            po_date=serializer.validated_data["po_date"],
            vendor=vendor,
            inward_type=serializer.validated_data["inward_type"],
            receipt_date=serializer.validated_data["receipt_date"],
            batch_number=batch_number,
            invoice_number=serializer.validated_data.get("invoice_number", ""),
            delivery_challan_number=serializer.validated_data.get("delivery_challan_number", ""),
            eway_bill_number=serializer.validated_data.get("eway_bill_number", ""),
            remarks=serializer.validated_data.get("remarks", ""),
            created_by=request.user,
            invoice_file=request.FILES.get("invoice_file"),
            challan_file=request.FILES.get("challan_file"),
            eway_bill_file=request.FILES.get("eway_bill_file"),
        )

        for item in serializer.validated_data["items"]:
            po_item = get_object_or_404(
                PurchaseOrderItem,
                id=item["purchase_order_item_id"],
                purchase_order=purchase_order
            )
            MaterialReceiptItem.objects.create(
                mrn=mrn,
                purchase_order_item=po_item,
                received_qty=item["received_qty"],
                serial_numbers=item.get("serial_numbers", "")
            )

        return Response(
            {
                "mrn_id": mrn.id,
                "batch_number": mrn.batch_number,
                "message": "Material Receipt Note created successfully"
            },
            status=201
        )


class PurchaseOrderDropdown(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {
                "id": po.id,
                "label": f"{po.order_id} ({po.assembly_type.replace('_', ' ').title()})"
            }
            for po in PurchaseOrder.objects.all()
        ])


class InwardTypeDropdown(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": "bom_items", "label": "BOM Items"},
            {"key": "materials", "label": "Materials"},
            {"key": "assembled_pcb", "label": "Assembled PCB"},
            {"key": "assembled_device", "label": "Assembled Device"},
        ])


class PurchaseOrderItemsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, po_id):
        po = get_object_or_404(PurchaseOrder, id=po_id)

        return Response([
            {
                "id": item.id,
                "product_id": item.item_code,
                "item_type": item.item_type,
                "vendor_name": item.vendor_name,
                "unit_price": str(item.unit_price),
                "delivery_days": item.delivery_days
            }
            for item in po.items.all()
        ])


# ---------------- Dispatch Workflow APIs ----------------
# ---------------- STEP 1 ----------------
class DispatchStep1APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DispatchStep1Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dispatch = Dispatch.objects.create(
            **serializer.validated_data,
            created_by=request.user
        )

        return Response(
            {"dispatch_id": dispatch.id},
            status=status.HTTP_201_CREATED
        )


# ---------------- STEP 2 ----------------
class DispatchStep2APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, dispatch_id):
        dispatch = get_object_or_404(Dispatch, id=dispatch_id)

        serializer = DispatchStep2Serializer(
            dispatch,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        remaining_stock = (
            dispatch.batch.available_stock - dispatch.dispatch_quantity
        )

        return Response(
            {
                "message": "Stock verified",
                "remaining_stock": remaining_stock
            }
        )


# ---------------- STEP 3 ----------------
class DispatchStep3APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, dispatch_id):
        dispatch = get_object_or_404(Dispatch, id=dispatch_id)

        # 🚫 Block if Step-2 not completed
        if not all([
            dispatch.product,
            dispatch.batch,
            dispatch.dispatch_quantity
        ]):
            return Response(
                {
                    "error": "Step-2 (Stock Verification) must be completed first."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = DispatchStep3Serializer(
            dispatch,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Dispatch details saved"})



# ---------------- STEP 4 ----------------
class DispatchStep4APIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, dispatch_id):
        dispatch = get_object_or_404(Dispatch, id=dispatch_id)

        # 🚫 Block if Step-3 not completed
        if not dispatch.dispatch_date:
            return Response(
                {
                    "error": "Step-3 (Dispatch Details) must be completed first."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = DispatchStep4Serializer(
            dispatch,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 🔐 Prevent double stock deduction
        if not dispatch.stock_deducted:
            batch = dispatch.batch

            if dispatch.dispatch_quantity > batch.available_stock:
                return Response(
                    {
                        "error": "Insufficient stock at final dispatch."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            batch.available_stock -= dispatch.dispatch_quantity
            batch.save(update_fields=["available_stock"])

            dispatch.stock_deducted = True

        # ✅ Mark workflow completed
        dispatch.status = "completed"
        dispatch.save(update_fields=["status", "stock_deducted"])

        return Response(
            {
                "message": "Dispatch completed successfully",
                "dispatch_id": dispatch.id
            },
            status=status.HTTP_200_OK
        )


# ---------------- Dropdown APIs for Dispatch Workflow ----------------
class SalesOrderDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"id": so.id, "label": f"SO-{so.id}"}
            for so in SalesOrder.objects.all().order_by("-id")
        ])


class DispatchOrderTypeDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": "distributor", "label": "Distributor"},
            {"key": "dealer", "label": "Dealer"},
            {"key": "b2c", "label": "B2C Customer"},
        ])


class DispatchProductDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"id": p.id, "label": p.name}
            for p in OrderProduct.objects.all().order_by("name")
        ])


class DispatchBatchDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        product_id = request.query_params.get("product_id")

        if not product_id:
            return Response(
                {"error": "product_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response([
            {
                "id": b.id,
                "label": b.batch_number,
                "available_stock": b.available_stock
            }
            for b in OrderBatch.objects.filter(product_id=product_id)
        ])


# ----------------------------------
# Create Post Dispatch Return API
# ----------------------------------
class PostDispatchReturnCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = PostDispatchReturnCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        header_data = serializer.validated_data["header"]
        items_data = serializer.validated_data["items"]

        # Create main return record
        return_obj = PostDispatchReturn.objects.create(
            **header_data,
            created_by=request.user
        )

        total_amount = Decimal("0.00")

        # Create item records
        for item in items_data:
            item_amount = (
                Decimal(item["return_qty"]) * item["unit_price"]
            )

            total_amount += item_amount

            PostDispatchReturnItem.objects.create(
                post_dispatch_return=return_obj,
                product_id=item["product_id"],
                description=item["description"],
                dispatched_qty=item["dispatched_qty"],
                unit_price=item["unit_price"],
                return_qty=item["return_qty"],
                return_amount=item_amount,
            )

        # Update calculated total
        return_obj.total_return_amount = total_amount
        return_obj.save(update_fields=["total_return_amount"])

        return Response(
            {
                "return_id": return_obj.id,
                "total_return_amount": total_amount,
                "message": "Return created and credit note initiated"
            },
            status=status.HTTP_201_CREATED
        )


# ----------------------------------
# Return Type Dropdown API
# ----------------------------------
class ReturnTypeDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": "full", "label": "Full Return (All Items)"},
            {"key": "partial", "label": "Partial Return (Some Items)"},
            {"key": "replacement", "label": "Return for Replacement"},
        ])


# ----------------------------------
# Return Reason Dropdown API
# ----------------------------------
class ReturnReasonDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {"key": "damaged", "label": "Damaged in Transit"},
            {"key": "defective", "label": "Defective Product"},
            {"key": "wrong_item", "label": "Wrong Item Delivered"},
            {"key": "rejected", "label": "Customer Rejection"},
            {"key": "quality", "label": "Quality Issues"},
            {"key": "spec_mismatch", "label": "Specification Mismatch"},
            {"key": "other", "label": "Other"},
        ])


