from datetime import datetime
from decimal import Decimal
from collections import defaultdict

from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError
import uuid

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.tokens import AccessToken

from .models import *
from .serializers import *
from .utils import generate_note_number


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


# ======================================================================
# ============================ Settings APIs ===========================
# ======================================================================


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
                    "message": f"State '{state_name}' cannot be deleted because it has linked districts.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        self.perform_destroy(state)

        return Response(
            {"success": True, "message": f"State '{state_name}' deleted successfully."},
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
    queryset = Vendor.objects.select_related("state", "district")
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError(
                {"detail": "Vendor with this GST number already exists for this user."}
            )


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


# ======================================================================
# ====================== Sales & Production APIs =======================
# ======================================================================


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


# ================================= Order Entry APIs ==================================
# ---------------- STEP 1 ----------------
class DeviceStep1APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device = Device.objects.create(created_by=request.user)
        serializer = DeviceInformationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response(
            {"device_id": device.id, "message": "Step 1 completed"}, status=201
        )


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
        serializer = BOMComponentSerializer(data=request.data["components"], many=True)
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
        serializer = AccessorySerializer(data=request.data["accessories"], many=True)
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
            user=request.user, is_step2_complete=False
        )

        serializer = OrderEntryStep1Serializer(entry, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(is_step1_complete=True)

        return Response({"entry_id": entry.id}, status=status.HTTP_200_OK)


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
                status=status.HTTP_400_BAD_REQUEST,
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
        batch = OrderBatch.objects.select_for_update().get(id=order.batch.id)
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
        return Response(
            [{"id": p.id, "name": p.name} for p in OrderProduct.objects.all()]
        )


# ---------------- SupplierVendor Dropdown APIView ----------------
class SupplierVendorDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [{"id": v.id, "name": v.name} for v in SupplierVendor.objects.all()]
        )



# ======================== RFQ LIST & DETAIL APIS ==========================
# ----------- RFQ List API with Filtering & Search -----------
class RFQListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):
        """
        List all RFQs with filtering by status and vendor search
        Query params: status, vendor, search, page
        """
        queryset = RequestForQuote.objects.filter(
            status="submitted"
        ).order_by("-created_at")

        # Status Filter
        status_filter = request.query_params.get("status")
        if status_filter and status_filter != "all":
            queryset = queryset.filter(status=status_filter)

        # Search Filter (by vendor, RFQ No, customer, device, product ID)
        search_query = request.query_params.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(order_reference__icontains=search_query)
                | Q(device_name__icontains=search_query)
            )

        # Count statistics
        total_count = RequestForQuote.objects.filter(status="submitted").count()
        pending_count = queryset.filter(status="submitted").count()
        # Note: QUOTED and REJECTED would come from quotation model

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = RFQListSerializer(paginated_queryset, many=True)

        return Response(
            {
                "count": paginator.page.paginator.count,
                "total": total_count,
                "pending": pending_count,
                "quoted": 0,
                "rejected": 0,
                "results": serializer.data,
            }
        )


# ----------- RFQ Detail API -----------
class RFQDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, rfq_id):
        """
        Fetch complete RFQ details including selections and requirements
        """
        rfq = get_object_or_404(RequestForQuote, id=rfq_id)

        serializer = RFQDetailSerializer(rfq)

        return Response(serializer.data, status=status.HTTP_200_OK)


# ----------- Create Quotation API -----------
class CreateQuotationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, rfq_id):
        """
        Create or update quotation rate for an RFQ by vendor
        Request body: { "vendor_id": int, "quotation_rate": decimal }
        """
        rfq = get_object_or_404(RequestForQuote, id=rfq_id)
        
        vendor_id = request.data.get("vendor_id")
        quotation_rate = request.data.get("quotation_rate")

        if not vendor_id:
            return Response(
                {"error": "vendor_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quotation_rate is None:
            return Response(
                {"error": "quotation_rate is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response(
                {"error": "Vendor not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create or update quotation
        quotation, created = RFQQuotation.objects.update_or_create(
            rfq=rfq,
            vendor=vendor,
            defaults={
                "quotation_rate": quotation_rate,
                "status": "quoted",
                "quotation_date": timezone.now(),
            },
        )

        serializer = RFQQuotationSerializer(quotation)

        return Response(
            {
                "message": "Quotation created successfully" if created else "Quotation updated successfully",
                "quotation": serializer.data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )



# ---------------- ProductCategory Dropdown APIView ----------------
class ProductCategoryDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": "gps_devices", "label": "GPS Devices"},
                {"key": "tracking_devices", "label": "Tracking Devices"},
                {"key": "iot_devices", "label": "IoT Devices"},
                {"key": "accessories", "label": "Accessories"},
                {"key": "components", "label": "Components"},
            ]
        )


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
            production_type="make_to_order",
        )

        if hasattr(order_entry, "make_to_order"):
            return Response(
                {"detail": "Step 2 already completed"}, status=status.HTTP_409_CONFLICT
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
                },
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- CustomerType Dropdown APIView ----------------
class CustomerTypeDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": "b2b", "label": "B2B Partner"},
                {"key": "b2c", "label": "B2C Customer"},
                {"key": "distributor", "label": "Distributor"},
                {"key": "dealer", "label": "Dealer"},
            ]
        )


# ---------------- Payment Terms Dropdown APIView ----------------
class PaymentTermsDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": "100_advance", "label": "100% Advance"},
                {"key": "50_50", "label": "50% Advance, 50% on Delivery"},
                {"key": "30_70", "label": "30% Advance, 70% on Delivery"},
                {"key": "net_30", "label": "Net 30 Days"},
                {"key": "net_60", "label": "Net 60 Days"},
                {"key": "custom", "label": "Custom Terms"},
            ]
        )


# ---------------- Order Priority Dropdown APIView ----------------
class OrderPriorityDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": "low", "label": "Low"},
                {"key": "medium", "label": "Medium"},
                {"key": "high", "label": "High"},
                {"key": "urgent", "label": "Urgent"},
            ]
        )


# ========================= Request for Quote =============================
# ---------------- RFQ Step 1 ----------------
class RFQStep1APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RFQStep1Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rfq = serializer.save(created_by=request.user)

        return Response({"rfq_id": rfq.id, "message": "Step 1 completed"}, status=201)


# ---------------- RFQ Step 2 ----------------
class RFQStep2APIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        rfq = get_object_or_404(
            RequestForQuote, id=request.data.get("rfq_id"), status="draft"
        )

        serializer = RFQStep2Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rfq.selections.all().delete()

        for ref in serializer.validated_data.get("bom_parts", []):
            RFQSelection.objects.create(rfq=rfq, item_type="bom", reference=ref)

        for ref in serializer.validated_data.get("components", []):
            RFQSelection.objects.create(rfq=rfq, item_type="component", reference=ref)

        for ref in serializer.validated_data.get("services", []):
            RFQSelection.objects.create(rfq=rfq, item_type="service", reference=ref)

        return Response({"message": "Step 2 completed"})


# ---------------- RFQ STEP-3 API (FINAL SUBMIT) ----------------
class RFQStep3APIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        rfq = get_object_or_404(
            RequestForQuote, id=request.data.get("rfq_id"), status="draft"
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

        return Response({"message": "RFQ submitted successfully"}, status=201)


# ---------------- Dropdowns for RFQ ----------------
class QuoteTypeDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": "components", "label": "Components"},
                {"key": "bom", "label": "Items (BOM Parts)"},
                {"key": "services", "label": "Services"},
            ]
        )


# ---------------- Assembly Type Dropdown APIView ----------------
class AssemblyTypeDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": "pcb_assembly", "label": "PCB Assembly"},
                {"key": "device_assembly", "label": "Device Assembly"},
            ]
        )


# ---------------- SRN Dropdown APIView ----------------
class SRNDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [{"key": k, "label": v} for k, v in RequestForQuote.SRN_CHOICES]
        )


# ---------------- Vendor Dropdown APIView ----------------
class VendorDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {
                    "id": v.id,
                    "label": f"{v.name} ({v.city})" if hasattr(v, "city") else v.name,
                }
                for v in Vendor.objects.all()
            ]
        )


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
            created_by=request.user,
        )

        for ot in serializer.validated_data["order_types"]:
            PurchaseOrderType.objects.create(purchase_order=po, order_type=ot)

        return Response(
            {"purchase_order_id": po.id, "message": "Step 1 completed"}, status=201
        )


# =========================== Create Purchase Order ==========================
# ---------------- Create Purchase Order STEP 2 ----------------
class Step2APIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        po = get_object_or_404(PurchaseOrder, id=request.data.get("purchase_order_id"))

        serializer = PurchaseStep2Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        po.wastage_percentage = serializer.validated_data["wastage_percentage"]
        po.selected_vendor_id = serializer.validated_data["selected_vendor_id"]
        po.delivery_date = serializer.validated_data["delivery_date"]
        po.payment_terms = serializer.validated_data["payment_terms"]
        po.save()

        po.items.all().delete()

        items_list = [
            PurchaseOrderItem(purchase_order=po, **item)
            for item in serializer.validated_data["items"]
        ]
        PurchaseOrderItem.objects.bulk_create(items_list, batch_size=500)

        return Response({"message": "Purchase Order created successfully"}, status=201)


# ---------------- Dropdowns for Purchase Order ----------------
class OrderTypeDropdown(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": "bom", "label": "Items (BOM Parts)"},
                {"key": "component", "label": "Components (Enclosure, Battery, etc.)"},
                {"key": "service", "label": "Services (Assembly, Quality Check, etc.)"},
            ]
        )


# ---------------- Assembly Type Dropdown APIView ----------------
class AssemblyTypeDropdown(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": "pcb", "label": "PCB Assembly"},
                {"key": "device", "label": "Device Assembly"},
            ]
        )


# ---------------- Payment Terms Dropdown APIView ----------------
class PaymentTermsDropdown(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [{"key": k, "label": v} for k, v in PurchaseOrder.PAYMENT_TERMS_CHOICES]
        )


# ============================== MRN =================================
# ---------------- Create Material Receipt Note (MRN) ----------------
class MRNCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = MRNCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purchase_order = get_object_or_404(
            PurchaseOrder, id=serializer.validated_data["purchase_order_id"]
        )
        vendor = get_object_or_404(Vendor, id=serializer.validated_data["vendor_id"])
        batch_number = f"MRN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        mrn = MaterialReceiptNote.objects.create(
            purchase_order=purchase_order,
            po_date=serializer.validated_data["po_date"],
            vendor=vendor,
            inward_type=serializer.validated_data["inward_type"],
            receipt_date=serializer.validated_data["receipt_date"],
            batch_number=batch_number,
            invoice_number=serializer.validated_data.get("invoice_number", ""),
            delivery_challan_number=serializer.validated_data.get(
                "delivery_challan_number", ""
            ),
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
                purchase_order=purchase_order,
            )
            MaterialReceiptItem.objects.create(
                mrn=mrn,
                purchase_order_item=po_item,
                received_qty=item["received_qty"],
                serial_numbers=item.get("serial_numbers", ""),
            )

        return Response(
            {
                "mrn_id": mrn.id,
                "batch_number": mrn.batch_number,
                "message": "Material Receipt Note created successfully",
            },
            status=201,
        )


# ---------------- Dropdown APIs for MRN ----------------
class PurchaseOrderDropdown(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {
                    "id": po.id,
                    "label": f"{po.order_id} ({po.assembly_type.replace('_', ' ').title()})",
                }
                for po in PurchaseOrder.objects.all()
            ]
        )


# ---------------- Inward Type Dropdown APIView ----------------
class InwardTypeDropdown(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": "bom_items", "label": "BOM Items"},
                {"key": "materials", "label": "Materials"},
                {"key": "assembled_pcb", "label": "Assembled PCB"},
                {"key": "assembled_device", "label": "Assembled Device"},
            ]
        )


# ---------------- Purchase Order Items APIView ----------------
class PurchaseOrderItemsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, po_id):
        po = get_object_or_404(PurchaseOrder, id=po_id)

        return Response(
            [
                {
                    "id": item.id,
                    "product_id": item.item_code,
                    "item_type": item.item_type,
                    "vendor_name": item.vendor_name,
                    "unit_price": str(item.unit_price),
                    "delivery_days": item.delivery_days,
                }
                for item in po.items.all()
            ]
        )


# ===================================== Dispatch Workflow APIs ========================================
# ---------------- STEP 1 ----------------
class DispatchStep1APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DispatchStep1Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dispatch = Dispatch.objects.create(
            **serializer.validated_data, created_by=request.user
        )

        return Response({"dispatch_id": dispatch.id}, status=status.HTTP_201_CREATED)


# ---------------- STEP 2 ----------------
class DispatchStep2APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, dispatch_id):
        dispatch = get_object_or_404(Dispatch, id=dispatch_id)

        serializer = DispatchStep2Serializer(dispatch, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        remaining_stock = dispatch.batch.available_stock - dispatch.dispatch_quantity

        return Response(
            {"message": "Stock verified", "remaining_stock": remaining_stock}
        )


# ---------------- STEP 3 ----------------
class DispatchStep3APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, dispatch_id):
        dispatch = get_object_or_404(Dispatch, id=dispatch_id)

        # Block if Step-2 not completed
        if not all([dispatch.product, dispatch.batch, dispatch.dispatch_quantity]):
            return Response(
                {"error": "Step-2 (Stock Verification) must be completed first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DispatchStep3Serializer(dispatch, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Dispatch details saved"})


# ---------------- STEP 4 ----------------
class DispatchStep4APIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, dispatch_id):
        dispatch = get_object_or_404(Dispatch, id=dispatch_id)

        # Block if Step-3 not completed
        if not dispatch.dispatch_date:
            return Response(
                {"error": "Step-3 (Dispatch Details) must be completed first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DispatchStep4Serializer(dispatch, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Prevent double stock deduction
        if not dispatch.stock_deducted:
            batch = dispatch.batch

            if dispatch.dispatch_quantity > batch.available_stock:
                return Response(
                    {"error": "Insufficient stock at final dispatch."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            batch.available_stock -= dispatch.dispatch_quantity
            batch.save(update_fields=["available_stock"])

            dispatch.stock_deducted = True

        # Mark workflow completed
        dispatch.status = "completed"
        dispatch.save(update_fields=["status", "stock_deducted"])

        return Response(
            {"message": "Dispatch completed successfully", "dispatch_id": dispatch.id},
            status=status.HTTP_200_OK,
        )


# ---------------- Dropdown APIs for Dispatch Workflow ----------------
class SalesOrderDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"id": so.id, "label": f"SO-{so.id}"}
                for so in SalesOrder.objects.all().order_by("-id")
            ]
        )


# ---------------- Dispatch Order Type Dropdown APIView ----------------
class DispatchOrderTypeDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": "distributor", "label": "Distributor"},
                {"key": "dealer", "label": "Dealer"},
                {"key": "b2c", "label": "B2C Customer"},
            ]
        )


# ---------------- Dispatch Product Dropdown APIView ----------------
class DispatchProductDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"id": p.id, "label": p.name}
                for p in OrderProduct.objects.all().order_by("name")
            ]
        )


# ---------------- Dispatch Batch Dropdown APIView ----------------
class DispatchBatchDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        product_id = request.query_params.get("product_id")

        if not product_id:
            return Response(
                {"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            [
                {
                    "id": b.id,
                    "label": b.batch_number,
                    "available_stock": b.available_stock,
                }
                for b in OrderBatch.objects.filter(product_id=product_id)
            ]
        )


# ======================================= Post-Dispatch Returns APIs =========================================
# --------------------- Create Post Dispatch Return API ---------------------
class PostDispatchReturnCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = PostDispatchReturnCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        header_data = serializer.validated_data["header"]
        items_data = serializer.validated_data["items"]

        # Create main return record
        return_obj = PostDispatchReturn.objects.create(
            **header_data, created_by=request.user
        )

        total_amount = Decimal("0.00")

        # Create item records
        for item in items_data:
            item_amount = Decimal(item["return_qty"]) * item["unit_price"]

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
                "message": "Return created and credit note initiated",
            },
            status=status.HTTP_201_CREATED,
        )


# ------------------------ Return Type Dropdown APIView ----------------
class ReturnTypeDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": "full", "label": "Full Return (All Items)"},
                {"key": "partial", "label": "Partial Return (Some Items)"},
                {"key": "replacement", "label": "Return for Replacement"},
            ]
        )


# ---------------------- Return Reason Dropdown API View ----------------
class ReturnReasonDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": "damaged", "label": "Damaged in Transit"},
                {"key": "defective", "label": "Defective Product"},
                {"key": "wrong_item", "label": "Wrong Item Delivered"},
                {"key": "rejected", "label": "Customer Rejection"},
                {"key": "quality", "label": "Quality Issues"},
                {"key": "spec_mismatch", "label": "Specification Mismatch"},
                {"key": "other", "label": "Other"},
            ]
        )


# ---------------- State Dropdown APIView ----------------
class StateDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        states = State.objects.filter(status="active").order_by("name")
        return Response(
            [{"id": state.id, "label": state.name} for state in states], status=200
        )


# ---------------- District Dropdown APIView ----------------
class DistrictDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        state_id = request.query_params.get("state_id")

        if not state_id:
            return Response(
                {"state_id": "state_id query param is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        districts = District.objects.filter(
            state_id=state_id, status="active"
        ).order_by("name")

        return Response(
            [{"id": district.id, "label": district.name} for district in districts],
            status=200,
        )


# ---------------- Module Management Account Registration ----------------
class AccountRegistrationCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = AccountRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()

        return Response(
            {"message": "Account created successfully", "account_id": account.id},
            status=status.HTTP_201_CREATED,
        )


# ---------------- Module Management QC Inspector Registration ----------------
class QCInspectorRegistrationCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = QCInspectorRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        qc_inspector = serializer.save()

        return Response(
            {
                "message": "QC Inspector registered successfully",
                "qc_inspector_id": qc_inspector.id,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- Module Management Purchase Department Registration ----------------
class PurchaseDepartmentRegistrationCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = PurchaseDepartmentRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purchase_department = serializer.save()

        return Response(
            {
                "message": "Purchase Department registered successfully",
                "purchase_department_id": purchase_department.id,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- Module Management Store Manager Registration ----------------
class StoreManagerRegistrationCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = StoreManagerRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        store_manager = serializer.save()

        return Response(
            {
                "message": "Store Manager registered successfully",
                "store_manager_id": store_manager.id,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- Module Management Repair Technician Registration --------------
class RepairTechnicianRegistrationCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = RepairTechnicianRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        repair_technician = serializer.save()

        return Response(
            {
                "message": "Repair Technician registered successfully",
                "repair_technician_id": repair_technician.id,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- Store Transfer ViewSet ----------------
class StoreTransferViewSet(ModelViewSet):
    queryset = StoreTransfer.objects.select_related(
        "product", "category", "vendor", "created_by"
    ).all()
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = [
        "product_name",  # Search by product name
        "batch_number",  # Search by batch number
        "vendor__name",  # Search by vendor name
        "category__name",  # Search by category name
        "transfer_id",  # Search by transfer ID
        "mrn_number",  # Search by MRN number
    ]
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        """Choose serializer based on action"""
        if self.action == "retrieve":
            return StoreTransferDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return StoreTransferCreateUpdateSerializer
        return StoreTransferListSerializer

    def get_queryset(self):
        """Filter by dispatch_status if provided in query params"""
        queryset = super().get_queryset()

        # Filter by dispatch status if provided
        dispatch_status = self.request.query_params.get("dispatch_status")
        if dispatch_status:
            queryset = queryset.filter(dispatch_status=dispatch_status)

        # Filter by category if provided
        category_id = self.request.query_params.get("category_id")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Filter by date range if provided
        transfer_date_from = self.request.query_params.get("transfer_date_from")
        if transfer_date_from:
            queryset = queryset.filter(transfer_date__gte=transfer_date_from)

        transfer_date_to = self.request.query_params.get("transfer_date_to")
        if transfer_date_to:
            queryset = queryset.filter(transfer_date__lte=transfer_date_to)

        return queryset

    def perform_create(self, serializer):
        """Set the created_by field to the current user"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"])
    def filter_options(self, request):
        """Get available filter options for the UI"""
        dispatch_statuses = StoreTransfer.DISPATCH_STATUS_CHOICES
        categories = ProductCategory.objects.all()

        return Response(
            {
                "dispatch_statuses": [
                    {"value": choice[0], "label": choice[1]}
                    for choice in dispatch_statuses
                ],
                "categories": ProductCategorySerializer(categories, many=True).data,
            }
        )


# ---------------- Product Category ViewSet ----------------
class ProductCategoryViewSet(ModelViewSet):
    """ViewSet for Product Categories"""

    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["name", "description"]


# ============================================================
# ===================== ACCOUNT MANAGEMENT ===================
# ============================================================


# ---------------- Debit Note ViewSet ----------------
class DebitNoteViewSet(ModelViewSet):
    """
    ViewSet for managing Debit Notes.

    Supports:
    - LIST: Get all debit notes with search and status filtering
    - RETRIEVE: Get detailed information about a specific debit note
    - CREATE: Create a new debit note
    - UPDATE/PARTIAL_UPDATE: Update debit note information
    - DESTROY: Delete a debit note
    - SUMMARY: Get dashboard summary (pending amount, total amount)
    """

    queryset = DebitNote.objects.select_related("created_by").all()
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["number", "vendor", "reference_document"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DebitNoteDetailSerializer
        elif self.action == "list":
            return DebitNoteListSerializer
        return DebitNoteCreateUpdateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status if provided
        status = self.request.query_params.get("status")
        if status and status != "all":
            queryset = queryset.filter(status=status)

        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        number = generate_note_number("debit")

        serializer.save(
            created_by=self.request.user,
            number=number,
            date=timezone.now().date(),
        )

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get dashboard summary for debit notes"""
        all_notes = self.get_queryset()

        pending_amount = all_notes.filter(status="pending").aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0")

        total_amount = all_notes.aggregate(total=models.Sum("amount"))[
            "total"
        ] or Decimal("0")

        return Response(
            {
                "pending_amount": float(pending_amount),
                "total_amount": float(total_amount),
                "pending_count": all_notes.filter(status="pending").count(),
                "total_count": all_notes.count(),
            }
        )


# ---------------- Credit Note ViewSet ----------------
class CreditNoteViewSet(ModelViewSet):
    """
    ViewSet for managing Credit Notes.

    Supports:
    - LIST: Get all credit notes with search and status filtering
    - RETRIEVE: Get detailed information about a specific credit note
    - CREATE: Create a new credit note
    - UPDATE/PARTIAL_UPDATE: Update credit note information
    - DESTROY: Delete a credit note
    - SUMMARY: Get dashboard summary (pending amount, total amount)
    """

    queryset = CreditNote.objects.select_related("created_by").all()
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["number", "customer", "reference_document"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CreditNoteDetailSerializer
        elif self.action == "list":
            return CreditNoteListSerializer
        return CreditNoteCreateUpdateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status if provided
        status = self.request.query_params.get("status")
        if status and status != "all":
            queryset = queryset.filter(status=status)

        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        number = generate_note_number("credit")

        serializer.save(
            created_by=self.request.user,
            number=number,
            date=timezone.now().date(),
        )

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get dashboard summary for credit notes"""
        all_notes = self.get_queryset()

        pending_amount = all_notes.filter(status="pending").aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0")

        total_amount = all_notes.aggregate(total=models.Sum("amount"))[
            "total"
        ] or Decimal("0")

        return Response(
            {
                "pending_amount": float(pending_amount),
                "total_amount": float(total_amount),
                "pending_count": all_notes.filter(status="pending").count(),
                "total_count": all_notes.count(),
            }
        )


# ---------------- Account Management Dashboard API ----------------
class AccountManagementDashboardAPIView(APIView):
    """
    Dashboard view for Account Management.
    Returns summary of debit notes and credit notes.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        debit_summary = DebitNote.objects.aggregate(
            pending=models.Sum("amount", filter=models.Q(status="pending")),
            total=models.Sum("amount"),
        )

        credit_summary = CreditNote.objects.aggregate(
            pending=models.Sum("amount", filter=models.Q(status="pending")),
            total=models.Sum("amount"),
        )

        return Response(
            {
                "debit_notes": {
                    "pending_amount": float(debit_summary["pending"] or 0),
                    "total_amount": float(debit_summary["total"] or 0),
                },
                "credit_notes": {
                    "pending_amount": float(credit_summary["pending"] or 0),
                    "total_amount": float(credit_summary["total"] or 0),
                },
            }
        )


# ---------------- Dropdown APIs for Debit/Credit Notes ----------------
class DebitNoteReasonsAPIView(APIView):
    """Get available debit note reason choices"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        reasons = [
            {"key": choice[0], "label": choice[1]}
            for choice in DebitNote.REASON_CHOICES
        ]
        return Response(reasons)


# ---------------- Dropdown APIs for Debit/Credit Notes ----------------
class CreditNoteReasonsAPIView(APIView):
    """Get available credit note reason choices"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        reasons = [
            {"key": choice[0], "label": choice[1]}
            for choice in CreditNote.REASON_CHOICES
        ]
        return Response(reasons)


# ---------------- Dropdown APIs for Debit/Credit Notes ----------------
class NoteStatusChoicesAPIView(APIView):
    """Get available note status choices"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        statuses = [
            {"key": choice[0], "label": choice[1]}
            for choice in DebitNote.STATUS_CHOICES
        ]
        return Response(statuses)


# ==================================================================================
# ====================================== Vendor ====================================
# ==================================================================================
# ----------------------------- RETURN REQUEST VIEWSET -----------------------------
class ReturnRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Return Requests

    Features:
    - List all return requests with pagination
    - Filter by status (pending, accepted, rejected)
    - Search by return number or reason
    - Get count of returns by status
    - Retrieve specific return request details
    - Create new return request
    - Update return request status
    - Delete return request
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["return_number", "reason", "items"]
    ordering_fields = ["date", "amount", "status", "created_at"]
    ordering = ["-date"]
    filterset_fields = ["status"]

    def get_queryset(self):
        return ReturnRequest.objects.select_related("created_by")

    def get_serializer_class(self):
        if self.action == "list":
            return ReturnRequestListSerializer
        elif self.action == "counts":
            return ReturnRequestCountSerializer
        return ReturnRequestSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=["get"])
    def counts(self, request):
        """
        Get count of returns by status

        Returns:
        {
            "pending": 5,
            "accepted": 3,
            "rejected": 2
        }
        """
        queryset = self.get_queryset()
        counts = {
            "pending": queryset.filter(status="pending").count(),
            "accepted": queryset.filter(status="accepted").count(),
            "rejected": queryset.filter(status="rejected").count(),
        }
        # serializer = self.get_serializer(counts)
        serializer = ReturnRequestCountSerializer(counts)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def recent(self, request):
        """
        Get recent return requests (last 10 by date)
        """
        queryset = self.get_queryset()[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"])
    def change_status(self, request, pk=None):
        """
        Change return request status

        Request:
        {
            "status": "accepted"  // or "rejected"
        }
        """
        return_request = self.get_object()
        new_status = request.data.get("status")

        if new_status not in ["pending", "accepted", "rejected"]:
            return Response(
                {"error": "Invalid status. Must be pending, accepted, or rejected"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return_request.status = new_status
        return_request.save()

        serializer = self.get_serializer(return_request)
        return Response(
            {
                "message": f"Return status updated to {new_status}",
                "return_request": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ------------------------------ REPAIR RECORD VIEWSET -------------------------------
class RepairRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = [
        "product_id",
        "product_name",
        "vendor",
        "mrn_number",
        "repair_type",
        "repair_center",
    ]
    ordering_fields = ["created_at", "product_name", "status"]
    ordering = ["-created_at"]
    filterset_fields = ["status", "repair_type"]

    def get_queryset(self):
        return RepairRecord.objects.select_related("created_by")

    def get_serializer_class(self):
        if self.action == "list":
            return RepairRecordListSerializer
        return RepairRecordSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """
        Get repair statistics

        Returns:
        {
            "total_failed": 100,
            "total_repaired": 85,
            "total_rejected": 10,
            "total_pending": 5,
            "by_status": {
                "pending": 10,
                "in_progress": 20,
                "completed": 60,
                "failed": 10
            }
        }
        """
        queryset = self.get_queryset()
        totals = queryset.aggregate(
            total_failed=Sum("failed_qty"),
            total_repaired=Sum("repaired_qty"),
            total_rejected=Sum("rejected_qty"),
            total_pending=Sum("repair_pending"),
        )

        # Replace None with 0 (important when table is empty)
        totals = {k: v or 0 for k, v in totals.items()}

        by_status = queryset.aggregate(
            pending=Count("id", filter=Q(status="pending")),
            in_progress=Count("id", filter=Q(status="in_progress")),
            completed=Count("id", filter=Q(status="completed")),
            failed=Count("id", filter=Q(status="failed")),
        )

        return Response({**totals, "by_status": by_status})

    @action(detail=True, methods=["patch"])
    def update_quantities(self, request, pk=None):
        """
        Update repair quantities

        Request:
        {
            "repaired_qty": 10,
            "rejected_qty": 2,
            "repair_pending": 3
        }
        """
        repair_record = self.get_object()

        repaired_qty = request.data.get("repaired_qty", repair_record.repaired_qty)
        rejected_qty = request.data.get("rejected_qty", repair_record.rejected_qty)
        repair_pending = request.data.get(
            "repair_pending", repair_record.repair_pending
        )

        # Validate quantities
        if repaired_qty + rejected_qty > repair_record.failed_qty:
            return Response(
                {"error": "Repaired Qty + Rejected Qty cannot exceed Failed Qty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        repair_record.repaired_qty = repaired_qty
        repair_record.rejected_qty = rejected_qty
        repair_record.repair_pending = repair_pending
        repair_record.save()

        serializer = self.get_serializer(repair_record)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ------------------------------- REJECTED ITEM VIEWSET -------------------------------
class RejectedItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Rejected Items

    Features:
    - List all rejected items with search and filter
    - Search by product ID, product name, vendor, MRN number, or reason
    - Filter by vendor or date range
    - Get rejected items statistics
    - Create new rejected item record
    - Update rejected item
    - Delete rejected item
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = [
        "product_id",
        "product_name",
        "vendor",
        "mrn_number",
    ]
    ordering_fields = ["qc_date", "product_name", "rejected_qty"]
    ordering = ["-qc_date"]
    filterset_fields = ["vendor", "qc_date"]

    def get_queryset(self):
        return RejectedItem.objects.select_related("created_by")

    def get_serializer_class(self):
        if self.action == "list":
            return RejectedItemListSerializer
        return RejectedItemSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """
        Get rejected items statistics

        Returns:
        {
            "total_rejected_items": 50,
            "total_rejected_qty": 250,
            "by_vendor": {
                "Vendor A": 100,
                "Vendor B": 150
            }
        }
        """
        queryset = self.get_queryset()

        total_rejected_qty = queryset.aggregate(total=Sum("rejected_qty"))["total"] or 0

        vendor_stats = (
            queryset.values("vendor")
            .annotate(total=Sum("rejected_qty"))
            .order_by("-total")
        )

        by_vendor = {row["vendor"]: row["total"] for row in vendor_stats}

        return Response(
            {
                "total_rejected_items": queryset.count(),
                "total_rejected_qty": total_rejected_qty,
                "by_vendor": by_vendor,
            }
        )

    @action(detail=False, methods=["get"])
    def by_vendor(self, request):
        """
        Get rejected items grouped by vendor
        """
        vendor = request.query_params.get("vendor")

        if not vendor:
            return Response(
                {"error": "vendor parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset().filter(vendor=vendor)

        total_rejected_qty = queryset.aggregate(total=Sum("rejected_qty"))["total"] or 0

        serializer = self.get_serializer(queryset, many=True)

        return Response(
            {
                "vendor": vendor,
                "total_rejected_qty": total_rejected_qty,
                "items": serializer.data,
            }
        )


# ============================================================
# DEVICE MANAGEMENT APIs
# ============================================================


class DeviceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing devices

    Features:
    - LIST: Get all devices (ALL DEVICES table)
    - RETRIEVE: Get device details (VIEW DEVICE page)
    - FILTER by status
    - SEARCH by name/model
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["info__make", "info__model"]
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]
    filterset_fields = ["status"]

    def get_queryset(self):
        return Device.objects.select_related(
            "created_by",
            "info",
            "bom",
            "enclosure",
            "wireharness",
            "battery",
            "sosbutton",
            "usermanual",
        ).prefetch_related(
            "sticker_set", "accessories", "bom__components", "wireharness__connectors"
        )

    def get_serializer_class(self):
        """
        Choose serializer based on action:
        - LIST: DeviceListSerializer (minimal fields)
        - RETRIEVE: DeviceDetailSerializer (all fields)
        """
        if self.action == "retrieve":
            return DeviceDetailSerializer
        return DeviceListSerializer

    def get_serializer_context(self):
        """Add request to serializer context for URL generation"""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


# ================== Self Order API ==================
class SelfOrderCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create a new self order"""
        serializer = SelfOrderSerializer(data=request.data)

        if serializer.is_valid():
            try:
                # Set the user to the authenticated user
                serializer.save(user=request.user)
                return Response(
                    {
                        "message": "Self order created successfully",
                        "data": serializer.data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    {
                        "error": "Failed to create self order",
                        "details": str(e),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(
            {
                "error": "Invalid data provided",
                "details": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class SelfOrderListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all self orders for the authenticated user"""
        try:
            self_orders = (
                SelfOrder.objects.filter(user=request.user)
                .select_related("device", "supply_state")
                .prefetch_related("device__info")
            )

            serializer = SelfOrderSerializer(self_orders, many=True)

            return Response(
                {
                    "message": "Self orders retrieved successfully",
                    "count": self_orders.count(),
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {
                    "error": "Failed to retrieve self orders",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SelfOrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get details of a specific self order"""
        try:
            self_order = get_object_or_404(SelfOrder, pk=pk, user=request.user)
            serializer = SelfOrderSerializer(self_order)

            return Response(
                {
                    "message": "Self order retrieved successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {
                    "error": "Failed to retrieve self order",
                    "details": str(e),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    def put(self, request, pk):
        """Update a self order"""
        try:
            self_order = get_object_or_404(SelfOrder, pk=pk, user=request.user)
            serializer = SelfOrderSerializer(
                self_order, data=request.data, partial=True
            )

            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "Self order updated successfully",
                        "data": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(
                {
                    "error": "Invalid data provided",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "error": "Failed to update self order",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        """Delete a self order"""
        try:
            self_order = get_object_or_404(SelfOrder, pk=pk, user=request.user)
            self_order.delete()

            return Response(
                {
                    "message": "Self order deleted successfully",
                },
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                {
                    "error": "Failed to delete self order",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SelfOrderDeviceDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        devices = Device.objects.filter(status="completed").select_related("info")
        data = [
            {"id": d.id, "name": d.info.make, "model": d.info.model} for d in devices
        ]
        return Response(data, status=200)


class GSTRateDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"value": "0.00", "label": "0%"},
                {"value": "5.00", "label": "5%"},
                {"value": "12.00", "label": "12%"},
                {"value": "18.00", "label": "18%"},
                {"value": "28.00", "label": "28%"},
            ],
            status=200,
        )



