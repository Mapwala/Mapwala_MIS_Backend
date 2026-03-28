# mapwala_mis/views.py
import uuid
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import models, transaction, IntegrityError
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework_simplejwt.tokens import AccessToken
from openpyxl import Workbook
import csv
from django.http import HttpResponse

# Local Imports
from .utils import generate_note_number, format_order_id
from .mixins import DeleteResponseMixin
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from .models import (
    State,
    SelfOrder,
    District,
    ParentCompany,
    B2CCustomer,
    B2BPartner,
    Vendor,
    Product,
    DeviceInformation,
    StoreTransfer,
    ProductCategory,
    DebitNote,
    CreditNote,
    ReturnRequest,
    RepairRecord,
    RejectedItem,
    Device,
    UserProfile,
    BOM,
    OrderEntry,
    OrderProduct,
    OrderBatch,
    SalesOrder,
    RequestForQuote,
    RFQSelection,
    PurchaseOrder,
    PurchaseOrderType,
    PurchaseOrderItem,
    MaterialReceiptItem,
    Distributor,
    Dealer,
    PostDispatchReturnItem,
    MaterialReceiptNote,
    Dispatch,
    PostDispatchReturn,
    Quotation,
    Manufacturer,
    QCInspectorRegistration,
    PurchaseDepartmentRegistration,
    RepairTechnicianRegistration,
    StoreManagerRegistration,
    DeviceInventory,
    ProductionOrder,
    OrderEntryMakeToOrder,
    B2BOrder,
    RFQQuotation,
    SupplierVendor,
)
from .serializers import (
    UserSerializer,
    LoginSerializer,
    B2CCustomerSerializer,
    B2BPartnerSerializer,
    StateSerializer,
    DistrictSerializer,
    ParentCompanySerializer,
    VendorSerializer,
    ProductCategorySerializer,
    ProductCreateSerializer,
    ProductDropdownSerializer,
    ReturnRequestSerializer,
    RepairRecordSerializer,
    RejectedItemSerializer,
    DistributorRegistrationSerializer,
    DealerRegistrationSerializer,
    ProformaInvoiceCreateSerializer,
    DeviceInformationSerializer,
    BOMSerializer,
    BOMComponentSerializer,
    EnclosureSerializer,
    WireHarnessSerializer,
    BatterySerializer,
    OrderProductSerializer,
    OrderBatchSerializer,
    SalesOrderCreateSerializer,
    ProductionOrderCreateSerializer,
    RFQListSerializer,
    RFQDetailSerializer,
    RFQStep1Serializer,
    RFQStep2Serializer,
    RFQStep3Serializer,
    PurchaseStep1Serializer,
    PurchaseStep2Serializer,
    SOSButtonSerializer,
    StickerSerializer,
    UserManualSerializer,
    AccessorySerializer,
    OrderEntryStep1Serializer,
    OrderEntryStep2MakeToOrderSerializer,
    MRNCreateSerializer,
    DispatchStep1Serializer,
    DispatchStep2Serializer,
    DispatchStep3Serializer,
    DispatchStep4Serializer,
    PostDispatchReturnCreateSerializer,
    AccountRegistrationSerializer,
    QCInspectorRegistrationSerializer,
    PurchaseDepartmentRegistrationSerializer,
    StoreManagerRegistrationSerializer,
    RepairTechnicianRegistrationSerializer,
    StoreTransferDetailSerializer,
    StoreTransferCreateUpdateSerializer,
    StoreTransferListSerializer,
    DebitNoteCreateUpdateSerializer,
    DebitNoteListSerializer,
    DebitNoteDetailSerializer,
    CreditNoteCreateUpdateSerializer,
    CreditNoteListSerializer,
    CreditNoteDetailSerializer,
    ReturnRequestListSerializer,
    RepairRecordListSerializer,
    RejectedItemListSerializer,
    ReturnRequestCountSerializer,
    SelfOrderSerializer,
    QuotationCreateSerializer,
    QuotationDetailSerializer,
    QuotationListSerializer,
    DeviceDetailSerializer,
    DeviceListSerializer,
    QuotationApproveRejectSerializer,
    ManufacturerSerializer,
    LinkedToChoicesSerializer,
    DeviceInventorySerializer,
    SalesOrderReadSerializer,
    ProductionOrderReadSerializer,
    OrderEntryReadSerializer,
    B2BOrderCreateSerializer,
    B2BOrderReadSerializer,
    POOrderIDDropdownSerializer,
    POSelectRFQDropdownSerializer,
    PurchaseStep2GetSerializer,
    AvailableVendorSummarySerializer,
    RFQCardSerializer,
    SupplierVendorSerializer,
)


User = get_user_model()


class LoginAPIView(APIView):
    """Handles user authentication and JWT token generation."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.accepted_terms = True
        profile.accepted_at = timezone.now()
        profile.save()

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


class UserViewSet(
    DeleteResponseMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    queryset = User.objects.select_related("profile").all().order_by("-id")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    delete_object_name = "user"
    delete_display_field = "username"


class StateViewSet(ModelViewSet):
    """Manage states with search and deletion protection for linked districts."""

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

    @action(detail=False, methods=["get"], url_path="dropdown")
    def dropdown(self, request):
        states = State.objects.filter(status="active").order_by("name")

        data = [{"id": state.id, "label": state.name} for state in states]

        return Response(data)


class DistrictViewSet(ModelViewSet):
    """Manage districts with state filtering."""

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

    @action(detail=False, methods=["get"], url_path="dropdown")
    def dropdown(self, request):
        state_id = request.query_params.get("state")

        if not state_id:
            return Response(
                {"error": "state query parameter is required"},
                status=400,
            )

        districts = (
            District.objects.filter(state_id=state_id, status="active")
            .values("id", "name")
            .order_by("name")
        )

        data = [
            {"id": district["id"], "label": district["name"]} for district in districts
        ]
        return Response(data)


class ParentCompanyViewSet(DeleteResponseMixin, ModelViewSet):
    queryset = ParentCompany.objects.all()
    serializer_class = ParentCompanySerializer
    permission_classes = [IsAuthenticated]
    delete_object_name = "parent_company"
    delete_display_field = "name"


class VendorViewSet(DeleteResponseMixin, ModelViewSet):
    queryset = Vendor.objects.select_related("state", "district")
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]
    delete_object_name = "vendor"
    delete_display_field = "name"

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError(
                {"detail": "Vendor with this GST number already exists for this user."}
            )


class B2CCustomerViewSet(DeleteResponseMixin, ModelViewSet):
    queryset = B2CCustomer.objects.select_related("state", "district").all()
    serializer_class = B2CCustomerSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    delete_object_name = "customer"
    delete_display_field = "name"


class B2BPartnerViewSet(DeleteResponseMixin, ModelViewSet):
    queryset = B2BPartner.objects.select_related("state", "district").all()
    serializer_class = B2BPartnerSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    delete_object_name = "partner"
    delete_display_field = "partner_name"


class LinkedToChoicesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = [
            {"value": key, "label": label}
            for key, label in Distributor.LINKED_TO_CHOICES
        ]
        serializer = LinkedToChoicesSerializer(data, many=True)
        return Response(serializer.data)


class DistributorViewSet(DeleteResponseMixin, ModelViewSet):
    queryset = Distributor.objects.select_related(
        "state", "district", "manufacturer"
    ).prefetch_related("authorised_states", "authorised_districts")

    serializer_class = DistributorRegistrationSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    delete_object_name = "distributor"
    delete_display_field = "name"

    # CREATE
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        distributor = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Distributor registered successfully",
                "distributor_id": distributor.id,
                "name": distributor.name,
            },
            status=status.HTTP_201_CREATED,
        )

    # UPDATE (PUT/PATCH safe)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        distributor = serializer.save()
        return Response(
            {
                "success": True,
                "message": "Distributor updated successfully",
                "distributor_id": distributor.id,
                "name": distributor.name,
            }
        )

    # DROPDOWN
    @action(detail=False, methods=["get"], url_path="dropdown")
    def dropdown(self, request):
        distributors = Distributor.objects.only("id", "name").order_by("name")
        data = [{"id": d.id, "label": d.name} for d in distributors]
        return Response(data)


class ManufacturerViewSet(DeleteResponseMixin, ModelViewSet):
    queryset = Manufacturer.objects.all().order_by("-created_at")
    serializer_class = ManufacturerSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    delete_object_name = "manufacturer"
    delete_display_field = "company_name"

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"], url_path="dropdown")
    def dropdown(self, request):
        manufacturers = Manufacturer.objects.only("id", "company_name").order_by(
            "company_name"
        )
        data = [
            {
                "id": m.id,
                "label": m.company_name,
            }
            for m in manufacturers
        ]
        return Response(data)


class DealerViewSet(DeleteResponseMixin, ModelViewSet):
    queryset = Dealer.objects.select_related(
        "state",
        "district",
        "manufacturer",
        "distributor",
    ).prefetch_related(
        "authorised_states",
        "authorised_districts",
    )

    serializer_class = DealerRegistrationSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    delete_object_name = "dealer"
    delete_display_field = "name"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dealer = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Dealer registered successfully.",
                "dealer_id": dealer.id,
                "name": dealer.name,
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        dealer = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Dealer updated successfully.",
                "dealer_id": dealer.id,
                "name": dealer.name,
            }
        )


class ProductCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProductCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "error": "Validation failed",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            with transaction.atomic():
                product = serializer.save()
            return Response(
                {
                    "message": "Product created successfully",
                    "data": ProductCreateSerializer(product).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except IntegrityError:
            # Handles DB-level unique constraint failure
            return Response(
                {
                    "error": "Product already exists",
                    "details": {"product_id": ["Product with this ID already exists."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # Catch unexpected errors
            return Response(
                {
                    "error": "Something went wrong",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProductDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Product.objects.all().order_by("product_id")
        serializer = ProductDropdownSerializer(queryset, many=True)
        return Response(serializer.data)


# PROFORMA INVOICE
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


# DEVICE CREATION WORKFLOW
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unit_of_measure_dropdown(request):
    data = [
        {"value": key, "label": label}
        for key, label in DeviceInformation.UNIT_OF_MEASURE_CHOICES
    ]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def state_of_supply_dropdown(request):
    data = [
        {"value": key, "label": label}
        for key, label in DeviceInformation.STATE_OF_SUPPLY_CHOICES
    ]
    return Response(data)


class DeviceViewSet(DeleteResponseMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["info__make", "info__model"]
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]
    filterset_fields = ["status"]
    delete_object_name = "device"

    def get_display_value(self, instance):
        return f"DEV-{instance.id:04d}"

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
            "sticker_set",
            "accessories",
            "bom__components",
            "wireharness__connectors",
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DeviceDetailSerializer
        if self.action == "list":
            return DeviceListSerializer
        return DeviceDetailSerializer


class DeviceStep1APIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        device = Device.objects.create(created_by=request.user, status="draft")
        serializer = DeviceInformationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)
        return Response(
            {
                "device_id": device.id,
                "message": "Step 1 completed",
            },
            status=status.HTTP_201_CREATED,
        )


class DeviceStep2APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device_id = request.data.get("device_id")
        if not device_id:
            return Response({"error": "device_id is required"}, status=400)
        device = get_object_or_404(Device, id=device_id)
        serializer = BOMSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response({"message": "Step 2 completed"})


class DeviceStep3APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device_id = request.data.get("device_id")
        if not device_id:
            return Response({"error": "device_id is required"}, status=400)
        bom = get_object_or_404(BOM, device_id=device_id)
        components = request.data.get("components")

        if not components:
            return Response({"error": "components list required"}, status=400)

        serializer = BOMComponentSerializer(data=components, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(bom=bom)

        return Response({"message": "Step 3 completed"})


class DeviceStep4APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device_id = request.data.get("device_id")
        if not device_id:
            return Response({"error": "device_id is required"}, status=400)
        device = get_object_or_404(Device, id=device_id)
        serializer = EnclosureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response({"message": "Step 4 completed"})


class DeviceStep5APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device_id = request.data.get("device_id")

        if not device_id:
            return Response({"error": "device_id is required"}, status=400)

        device = get_object_or_404(Device, id=device_id)
        serializer = WireHarnessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response({"message": "Step 5 completed"})


class DeviceStep6APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device_id = request.data.get("device_id")

        if not device_id:
            return Response({"error": "device_id is required"}, status=400)

        device = get_object_or_404(Device, id=device_id)
        serializer = BatterySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response({"message": "Step 6 completed"})


class DeviceStep7APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device_id = request.data.get("device_id")

        if not device_id:
            return Response({"error": "device_id is required"}, status=400)

        device = get_object_or_404(Device, id=device_id)
        serializer = SOSButtonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response({"message": "Step 7 completed"})


# STEP 8 — Sticker Upload — FIXED
class DeviceStep8APIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        device_id = request.data.get("device_id")

        if not device_id:
            return Response(
                {"error": "device_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        device = get_object_or_404(Device, id=device_id)
        stickers_map = defaultdict(dict)

        for key, value in request.data.items():
            if key.startswith("stickers["):
                parts = key.split("[")
                if len(parts) < 3:
                    continue
                index = parts[1].replace("]", "")
                field = parts[2].replace("]", "")
                stickers_map[index][field] = value

        stickers_list = list(stickers_map.values())

        # FIXED: validate that at least one sticker is present
        if not stickers_list:
            return Response(
                {"error": "At least one sticker is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = StickerSerializer(data=stickers_list, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response(
            {"message": "Step 8 completed."},
            status=status.HTTP_200_OK,
        )


# STEP 9 — User Manual Upload — FIXED
class DeviceStep9APIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        device_id = request.data.get("device_id")

        if not device_id:
            return Response(
                {"error": "device_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        device = get_object_or_404(Device, id=device_id)
        serializer = UserManualSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        return Response(
            {"message": "Step 9 completed."},
            status=status.HTTP_200_OK,
        )


class DeviceAccessoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        device_id = request.data.get("device_id")

        if not device_id:
            return Response({"error": "device_id is required"}, status=400)

        device = get_object_or_404(Device, id=device_id)
        accessories = request.data.get("accessories")

        if not accessories:
            return Response({"error": "accessories required"}, status=400)

        serializer = AccessorySerializer(data=accessories, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(device=device)

        device.status = "completed"
        device.save()

        return Response({"message": "Device creation completed"})


# ──────────────────────────────────────────────
# ORDER ENTRY VIEWSET
# ──────────────────────────────────────────────


class OrderEntryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrderEntry.objects.filter(user=self.request.user).order_by("-created_at")

    def get_serializer_class(self):

        if self.action == "step_1":
            return OrderEntryStep1Serializer
        if self.action == "step_2":
            return OrderEntryStep2MakeToOrderSerializer
        if self.action in ("update", "partial_update"):
            return OrderEntryStep1Serializer
        return OrderEntryReadSerializer

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Use POST /order-entries/step-1/ to create an order entry."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=["post"], url_path="step-1")
    def step_1(self, request):
        entry = (
            OrderEntry.objects.filter(user=request.user, is_step2_complete=False)
            .order_by("-created_at")
            .first()
        )
        if entry is None:
            entry = OrderEntry(user=request.user)

        serializer = OrderEntryStep1Serializer(entry, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(is_step1_complete=True)

        return Response({"entry_id": entry.id}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="step-2")
    @transaction.atomic
    def step_2(self, request):
        order_entry = get_object_or_404(
            OrderEntry,
            id=request.data.get("entry_id"),
            user=request.user,
            is_step1_complete=True,
            production_type="make_to_order",
        )

        if hasattr(order_entry, "make_to_order"):
            return Response(
                {"detail": "Step 2 already completed."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = OrderEntryStep2MakeToOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        make_to_order = serializer.save(order_entry=order_entry)

        order_entry.is_step2_complete = True
        order_entry.save(update_fields=["is_step2_complete"])

        return Response(
            {
                "message": "Order Entry completed successfully.",
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


# ──────────────────────────────────────────────
# ORDER PRODUCT VIEWSET
# ──────────────────────────────────────────────


class OrderProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = OrderProduct.objects.all()
    serializer_class = OrderProductSerializer


# ──────────────────────────────────────────────
# ORDER BATCH VIEWSET
# ──────────────────────────────────────────────


class OrderBatchViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderBatchSerializer

    def get_queryset(self):
        qs = OrderBatch.objects.select_related("product").all()
        product_id = self.request.query_params.get("product_id")
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs


# ──────────────────────────────────────────────
# SALES ORDER VIEWSET
# ──────────────────────────────────────────────


class SalesOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = SalesOrder.objects.select_related("product", "batch").order_by(
        "-created_at"
    )

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return SalesOrderReadSerializer
        return SalesOrderCreateSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = SalesOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        batch = OrderBatch.objects.select_for_update().get(id=order.batch.id)
        batch.available_stock -= order.quantity
        batch.save(update_fields=["available_stock"])

        return Response(
            {
                "message": "Sales order created successfully.",
                "order_id": order.id,
                "product": {"id": order.product.id, "name": order.product.name},
                "batch": {"id": batch.id, "batch_number": batch.batch_number},
                "remaining_stock": batch.available_stock,
                "grand_total": float(order.grand_total),
            },
            status=status.HTTP_201_CREATED,
        )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        old_batch = OrderBatch.objects.select_for_update().get(id=instance.batch.id)
        old_batch.available_stock += instance.quantity
        old_batch.save(update_fields=["available_stock"])

        serializer = SalesOrderCreateSerializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        new_batch = OrderBatch.objects.select_for_update().get(id=order.batch.id)
        new_batch.available_stock -= order.quantity
        new_batch.save(update_fields=["available_stock"])

        return Response(
            {
                "message": "Sales order updated successfully.",
                "order_id": order.id,
                "remaining_stock": new_batch.available_stock,
                "grand_total": float(order.grand_total),
            }
        )

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        batch = OrderBatch.objects.select_for_update().get(id=instance.batch.id)
        batch.available_stock += instance.quantity
        batch.save(update_fields=["available_stock"])
        instance.delete()

        return Response(
            {"message": "Sales order deleted and stock restored."},
            status=status.HTTP_200_OK,
        )


class SupplierVendorViewSet(DeleteResponseMixin, ModelViewSet):
    queryset = SupplierVendor.objects.all()
    serializer_class = SupplierVendorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["name"]

    # Mixin configuration
    delete_object_name = "supplier/vendor"
    delete_display_field = "name"

    @action(detail=False, methods=["get"], url_path="dropdown")
    def dropdown(self, request):
        vendors = SupplierVendor.objects.all().order_by("name")
        data = [{"id": v.id, "label": v.name} for v in vendors]
        return Response(data)


# ──────────────────────────────────────────────
# PRODUCTION ORDER VIEWSET
# ──────────────────────────────────────────────


class ProductionOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = ProductionOrder.objects.select_related(
        "product", "batch", "supplier_vendor"
    ).order_by("-created_at")

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return ProductionOrderReadSerializer
        return ProductionOrderCreateSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = ProductionOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        batch = OrderBatch.objects.select_for_update().get(id=order.batch.id)
        batch.available_stock += order.quantity_added
        batch.save(update_fields=["available_stock"])

        return Response(
            {
                "message": "Production order created and stock added successfully.",
                "production_order_id": order.id,
                "product": {"id": order.product.id, "name": order.product.name},
                "batch": {"id": batch.id, "batch_number": batch.batch_number},
                "added_quantity": order.quantity_added,
                "current_stock": batch.available_stock,
                "total_value": float(order.total_value),
            },
            status=status.HTTP_201_CREATED,
        )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        old_batch = OrderBatch.objects.select_for_update().get(id=instance.batch.id)
        if old_batch.available_stock < instance.quantity_added:
            return Response(
                {
                    "detail": (
                        f"Cannot update: only {old_batch.available_stock} units remain "
                        f"but this order originally added {instance.quantity_added}. "
                        "Some stock has already been consumed by sales orders."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_batch.available_stock -= instance.quantity_added
        old_batch.save(update_fields=["available_stock"])

        serializer = ProductionOrderCreateSerializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        new_batch = OrderBatch.objects.select_for_update().get(id=order.batch.id)
        new_batch.available_stock += order.quantity_added
        new_batch.save(update_fields=["available_stock"])

        return Response(
            {
                "message": "Production order updated successfully.",
                "production_order_id": order.id,
                "current_stock": new_batch.available_stock,
                "total_value": float(order.total_value),
            }
        )

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        batch = OrderBatch.objects.select_for_update().get(id=instance.batch.id)
        if batch.available_stock < instance.quantity_added:
            return Response(
                {
                    "detail": (
                        f"Cannot delete: only {batch.available_stock} units remain but "
                        f"this order added {instance.quantity_added}. "
                        "Consumed stock cannot be reversed."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        batch.available_stock -= instance.quantity_added
        batch.save(update_fields=["available_stock"])
        instance.delete()

        return Response(
            {"message": "Production order deleted and stock reversed."},
            status=status.HTTP_200_OK,
        )


class CustomerTypeDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": k, "label": v}
                for k, v in OrderEntryMakeToOrder.CUSTOMER_TYPE_CHOICES
            ]
        )


class ProductCategoryDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": k, "label": v}
                for k, v in ProductionOrder.PRODUCT_CATEGORY_CHOICES
            ]
        )


class PaymentTermsDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": k, "label": v}
                for k, v in OrderEntryMakeToOrder.PAYMENT_TERMS_CHOICES
            ]
        )


class OrderPriorityDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [{"key": k, "label": v} for k, v in OrderEntryMakeToOrder.PRIORITY_CHOICES]
        )


# ─────────────────────────────────────────────────────────────
# RFQ VIEWSET — fully corrected
# ─────────────────────────────────────────────────────────────
class RFQViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return (
            RequestForQuote.objects
            # Correct path: order → OrderEntry → make_to_order → product/customer
            .select_related(
                "order",
                "order__make_to_order",
                "order__make_to_order__product",
                "created_by",
            )
            .prefetch_related("selections", "quotations__vendor")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return RFQListSerializer
        if self.action == "retrieve":
            return RFQDetailSerializer
        if self.action == "step1":
            return RFQStep1Serializer
        if self.action == "step2":
            return RFQStep2Serializer
        if self.action == "step3":
            return RFQStep3Serializer
        if self.action == "step2_data":
            return RFQDetailSerializer
        return RFQDetailSerializer

    # ── LIST ────────────────────────────────────────────────
    def list(self, request):
        queryset = self.get_queryset().filter(status="submitted")

        vendor_filter = request.query_params.get("vendor", "").strip()
        if vendor_filter and vendor_filter != "all":
            queryset = queryset.filter(
                quotations__vendor__name__iexact=vendor_filter
            ).distinct()

        status_filter = request.query_params.get("status", "").strip()
        if status_filter and status_filter != "all":
            if status_filter == "pending":
                queryset = queryset.filter(quotations__isnull=True).distinct()
            elif status_filter in ["quoted", "rejected"]:
                queryset = queryset.filter(quotations__status=status_filter).distinct()

        search_query = request.query_params.get("search", "").strip()
        if search_query:
            # Search by formatted order ID (ORD001) or device/product name
            queryset = queryset.filter(
                Q(order__id__icontains=search_query.lstrip("ORD").lstrip("0") or "0")
                | Q(order__make_to_order__product__name__icontains=search_query)
                | Q(order__make_to_order__customer_name__icontains=search_query)
            )

        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(queryset, request)
        serializer = RFQListSerializer(page, many=True)

        submitted_qs = RequestForQuote.objects.filter(status="submitted")
        return Response(
            {
                "count": paginator.page.paginator.count,
                "total": submitted_qs.count(),
                "pending": submitted_qs.filter(quotations__isnull=True)
                .distinct()
                .count(),
                "quoted": submitted_qs.filter(quotations__status="quoted")
                .distinct()
                .count(),
                "rejected": submitted_qs.filter(quotations__status="rejected")
                .distinct()
                .count(),
                "results": serializer.data,
            }
        )

    # ── RETRIEVE ────────────────────────────────────────────
    def retrieve(self, request, pk=None):
        rfq = get_object_or_404(self.get_queryset(), id=pk)
        return Response(RFQDetailSerializer(rfq).data)

    # ── PARTIAL UPDATE (edit draft) ──────────────────────────
    def partial_update(self, request, pk=None):
        rfq = get_object_or_404(RequestForQuote, id=pk)
        if rfq.status != "draft":
            return Response(
                {"error": "Only draft RFQs can be updated."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = RFQStep1Serializer(rfq, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "RFQ updated successfully.", "rfq_id": rfq.id})

    # ── DESTROY ─────────────────────────────────────────────
    def destroy(self, request, pk=None):
        rfq = get_object_or_404(RequestForQuote, id=pk)
        if rfq.status != "draft":
            return Response(
                {"error": "Submitted RFQs cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        rfq.delete()
        return Response(
            {"message": "RFQ deleted successfully."},
            status=status.HTTP_200_OK,
        )

    # ── STEP 1 — Order Selection (Image 1) ──────────────────
    @action(detail=False, methods=["post"], url_path="step-1")
    def step1(self, request):
        """
        Creates RFQ from a selected OrderEntry.
        Image 1: order dropdown, quote_types multi, assembly_type multi, quantity.
        Returns Order Details Preview data so frontend can display it immediately.
        """
        serializer = RFQStep1Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rfq = serializer.save(created_by=request.user)

        # Build Order Details Preview response (Image 1 bottom section)
        order = rfq.order
        mto = getattr(order, "make_to_order", None)

        order_preview = {
            "customer": mto.customer_name if mto else None,
            "order_type": (
                order.get_production_type_display() if order.production_type else None
            ),
            "status": "CONFIRMED" if order.is_step2_complete else "IN PROGRESS",
            "device": mto.product.name if mto and mto.product else None,
        }

        return Response(
            {
                "rfq_id": rfq.id,
                "message": "Step 1 completed.",
                "order_preview": order_preview,  # Image 1: Order Details Preview
            },
            status=status.HTTP_201_CREATED,
        )

    # ── STEP 2 GET — Populate Component Selection (Image 2) ──
    @action(detail=False, methods=["get"], url_path="step-2/data")
    def step2_data(self, request):
        """
        GET endpoint to populate the Component Selection screen (Image 2).
        Returns: RFQ header, selected quote types, Device Information,
                 available BOM parts, components, services, current selections.
        """
        rfq_id = request.query_params.get("rfq_id")
        if not rfq_id:
            return Response(
                {"error": "rfq_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rfq = get_object_or_404(
            RequestForQuote.objects.select_related(
                "order",
                "order__make_to_order",
                "order__make_to_order__product",
            ).prefetch_related("selections"),
            id=rfq_id,
        )

        order = rfq.order
        mto = getattr(order, "make_to_order", None)

        # ── Device Information (Image 2: Make, Model, Version, Variant, State of Supply)
        device_info_data = None
        bom_parts = []
        components = []

        if mto and mto.product:
            product_name = mto.product.name
            # Find the matching Device by product name
            device = (
                Device.objects.select_related("info")
                .prefetch_related(
                    "bom__components",
                    "enclosure",
                    "wireharness",
                    "battery",
                    "sosbutton",
                    "accessories",
                )
                .filter(
                    info__model__icontains=product_name,
                    status="completed",
                )
                .first()
            )

            if device and hasattr(device, "info"):
                info = device.info
                device_info_data = {
                    "make": info.make,
                    "model": info.model,
                    "version": info.version,
                    "variant": info.variant,
                    # Image 2: "State of Supply: Mumbai" — shows state_of_supply value
                    "state_of_supply": info.state_of_supply,
                }

                # BOM Parts — shown only if "bom" in rfq.quote_types
                if "bom" in rfq.quote_types and hasattr(device, "bom"):
                    bom_parts = [
                        {
                            "id": str(comp.id),
                            "name": comp.description,
                            "part_no": comp.part_no,
                            "designator": comp.designator,
                            "quantity": comp.per_device_quantity,
                        }
                        for comp in device.bom.components.all()
                    ]

                # Components — shown only if "component" in rfq.quote_types
                if "component" in rfq.quote_types:
                    if hasattr(device, "enclosure"):
                        enc = device.enclosure
                        components.append(
                            {
                                "key": "enclosure",
                                "name": "Enclosure",
                                "description": (
                                    f"{enc.length}×{enc.breadth}×{enc.height}mm"
                                    f" - {enc.material} ({enc.color})"
                                ),
                            }
                        )
                    if hasattr(device, "wireharness"):
                        wh = device.wireharness
                        components.append(
                            {
                                "key": "wire_harness",
                                "name": "Wire Harness",
                                "description": (
                                    f"{wh.number_of_wires} wires - {wh.specification}"
                                ),
                            }
                        )
                    if hasattr(device, "battery"):
                        bat = device.battery
                        components.append(
                            {
                                "key": "battery",
                                "name": "Battery",
                                "description": f"{bat.capacity} (Part: {bat.part_number})",
                            }
                        )
                    if hasattr(device, "sosbutton"):
                        sos = device.sosbutton
                        components.append(
                            {
                                "key": "sos_button",
                                "name": "SOS Button",
                                "description": (
                                    f"Length: {sos.total_length}mm, "
                                    f"Qty/set: {sos.quantity_per_set}"
                                ),
                            }
                        )
                    for acc in device.accessories.all():
                        components.append(
                            {
                                "key": f"accessory_{acc.id}",
                                "name": acc.name,
                                "description": acc.description,
                            }
                        )

        # Current saved selections (for re-visiting Step 2)
        selected_bom = list(
            rfq.selections.filter(item_type="bom").values_list("reference", flat=True)
        )
        selected_components = list(
            rfq.selections.filter(item_type="component").values_list(
                "reference", flat=True
            )
        )
        selected_services = list(
            rfq.selections.filter(item_type="service").values_list(
                "reference", flat=True
            )
        )

        # Services — shown only if "service" in rfq.quote_types (Image 2/3)
        services_data = []
        if "service" in rfq.quote_types:
            services_data = [
                {**svc, "selected": svc["key"] in selected_services}
                for svc in RFQ_SERVICES
            ]

        return Response(
            {
                # Image 2 header: "Quote Selection - ORD001 (TechCorp GPS-Tracker-Pro)"
                "rfq_id": rfq.id,
                "order_reference": format_order_id(order),
                "device_name": mto.product.name if mto and mto.product else None,
                "selected_quote_types": rfq.quote_types,
                # Image 2: Device Information section
                "device_information": device_info_data,
                # Image 2: BOM Parts Selection section
                "bom_parts": bom_parts,
                "bom_parts_selected_count": len(selected_bom),
                # Image 2: Components Selection section
                "components": components,
                "components_selected_count": len(selected_components),
                # Image 2/3: Services Selection section
                "services": services_data,
                "services_selected_count": len(selected_services),
                # Current saved state
                "current_selections": {
                    "bom_parts": selected_bom,
                    "components": selected_components,
                    "services": selected_services,
                },
            }
        )

    # ── STEP 2 POST — Save Selections (Image 2) ─────────────
    @action(detail=False, methods=["post"], url_path="step-2")
    @transaction.atomic
    def step2(self, request):
        """
        Saves component selections respecting quote_types filter.
        Only saves selection types that are in rfq.quote_types.
        """
        serializer = RFQStep2Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rfq = get_object_or_404(
            RequestForQuote,
            id=serializer.validated_data["rfq_id"],
            status="draft",
        )

        # Atomically replace all selections
        rfq.selections.all().delete()

        selections_to_create = []

        # Only save bom_parts if "bom" was selected in Step 1 quote_types
        if "bom" in rfq.quote_types:
            for ref in serializer.validated_data.get("bom_parts", []):
                selections_to_create.append(
                    RFQSelection(rfq=rfq, item_type="bom", reference=ref)
                )

        # Only save components if "component" was selected in Step 1 quote_types
        if "component" in rfq.quote_types:
            for ref in serializer.validated_data.get("components", []):
                selections_to_create.append(
                    RFQSelection(rfq=rfq, item_type="component", reference=ref)
                )

        # Only save services if "service" was selected in Step 1 quote_types
        if "service" in rfq.quote_types:
            for ref in serializer.validated_data.get("services", []):
                selections_to_create.append(
                    RFQSelection(rfq=rfq, item_type="service", reference=ref)
                )

        RFQSelection.objects.bulk_create(selections_to_create)

        return Response(
            {
                "message": "Step 2 completed.",
                "rfq_id": rfq.id,
                "bom_parts_count": sum(
                    1 for s in selections_to_create if s.item_type == "bom"
                ),
                "components_count": sum(
                    1 for s in selections_to_create if s.item_type == "component"
                ),
                "services_count": sum(
                    1 for s in selections_to_create if s.item_type == "service"
                ),
            }
        )

    # ── STEP 3 — Quote Details + Submit (Image 3) ────────────
    @action(detail=False, methods=["post"], url_path="step-3")
    @transaction.atomic
    def step3(self, request):
        """
        Image 3: Vendor Names (multi), Delivery Date, Delivery Address,
        Additional Requirements. Button: "Submit Quote Request".
        """
        serializer = RFQStep3Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        rfq = get_object_or_404(
            RequestForQuote,
            id=data["rfq_id"],
            # Only the creator can submit — security check
            created_by=request.user,
            status="draft",
        )

        # Update delivery details on the RFQ
        rfq.delivery_date = data["delivery_date"]
        rfq.delivery_address = data["delivery_address"]
        rfq.additional_requirements = data.get("additional_requirements", "")
        rfq.status = "submitted"
        rfq.save(
            update_fields=[
                "delivery_date",
                "delivery_address",
                "additional_requirements",
                "status",
            ]
        )

        # Create RFQQuotation records for each selected vendor
        # Use get_or_create to avoid duplicate entries on re-submission
        vendor_ids = data["vendor_ids"]
        created_count = 0
        for vendor_id in vendor_ids:
            _, created = RFQQuotation.objects.get_or_create(
                rfq=rfq,
                vendor_id=vendor_id,
                defaults={"status": "pending"},
            )
            if created:
                created_count += 1

        return Response(
            {
                "message": "RFQ submitted successfully.",
                "rfq_id": rfq.id,
                "vendors_notified": vendor_ids,
                "new_quotations_created": created_count,
            },
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────
# ORDER DROPDOWN — Image 1: "Search Order ID or Device Name"
# ─────────────────────────────────────────────────────────────
class RFQOrderDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = (
            OrderEntry.objects.filter(
                production_type="make_to_order",
                is_step2_complete=True,  # Only confirmed orders (Image 1: Status: CONFIRMED)
            )
            .select_related(
                "make_to_order",
                "make_to_order__product",
            )
            .order_by("-id")
        )

        data = []
        for order in orders:
            mto = getattr(order, "make_to_order", None)
            if not mto:
                continue

            order_label = format_order_id(order)
            customer = mto.customer_name
            product = mto.product.name if mto.product else ""

            data.append(
                {
                    "id": order.id,
                    # Image 1 dropdown: "ORD001 - TechCorp Solutions (TechCorp GPS-Tracker-Pro)"
                    "label": f"{order_label} - {customer} ({product})",
                    # Image 1 Order Details Preview section — returned so
                    # frontend can populate the preview without an extra API call
                    "order_preview": {
                        "customer": customer,
                        "order_type": order.get_production_type_display(),
                        "status": "CONFIRMED",
                        "device": product,
                    },
                }
            )

        return Response(data)


# ─────────────────────────────────────────────────────────────
# QUOTE TYPES DROPDOWN
# ─────────────────────────────────────────────────────────────
class QuoteTypeDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": key, "label": label}
                for key, label in RequestForQuote.QUOTE_TYPE_CHOICES
            ]
        )


# ─────────────────────────────────────────────────────────────
# ASSEMBLY TYPES DROPDOWN
# ─────────────────────────────────────────────────────────────
class AssemblyTypeDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": key, "label": label}
                for key, label in RequestForQuote.ASSEMBLY_TYPE_CHOICES
            ]
        )


# ─────────────────────────────────────────────────────────────
# VENDOR DROPDOWN — Image 3: "VND001 - TechCorp Solutions (Mumbai)"
# ─────────────────────────────────────────────────────────────
class VendorDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        vendors = Vendor.objects.select_related("district").order_by("name")
        return Response(
            [
                {
                    "id": v.id,
                    # Dropdown option: "VND001 - TechCorp Solutions (Mumbai)"
                    "label": (
                        f"VND{v.id:03d} - {v.name}"
                        f" ({v.district.name if v.district_id else ''})"
                    ),
                    # Selected chip: "TechCorp Solutions (VND001)"
                    "chip_label": f"{v.name} (VND{v.id:03d})",
                }
                for v in vendors
            ]
        )


# ─────────────────────────────────────────────────────────────
# STEP 1 — DROPDOWNS
# ─────────────────────────────────────────────────────────────
class POOrderIDDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rfqs = RequestForQuote.objects.filter(status="submitted").order_by(
            "order_reference"
        )

        serializer = POOrderIDDropdownSerializer(rfqs, many=True)
        return Response(serializer.data)


class POSelectRFQDropdownAPIView(APIView):
    """
    Image 3: Populate 'Select RFQs' multi-select dropdown.
    Filtered by order_reference when order_id is provided.
    GET /purchase/dropdowns/rfqs/?order_reference=RFQ-MW-2024-001
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        order_reference = request.query_params.get("order_reference")
        rfqs = RequestForQuote.objects.filter(status="submitted").prefetch_related(
            "selections"
        )

        if order_reference:
            rfqs = rfqs.filter(order_reference=order_reference)

        serializer = POSelectRFQDropdownSerializer(rfqs, many=True)
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────────
# STEP 1 — CREATE (UPDATED)
# ─────────────────────────────────────────────────────────────


class Step1APIView(APIView):
    """
    Image 1: Step 1 — Buyer, RFQ selection, Order Types, Assembly Type.
    POST /purchase/step-1/
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = PurchaseStep1Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Store rfq_ids as comma-separated in existing rfq_id CharField
        # (no model change — existing field reused)
        rfq_ids_str = ",".join(str(i) for i in data["rfq_ids"])

        po = PurchaseOrder.objects.create(
            buyer_name=data["buyer_name"],
            order_id=data["order_id"],
            rfq_id=rfq_ids_str,
            assembly_type=data["assembly_type"],
            created_by=request.user,
        )

        # Bulk create order types
        PurchaseOrderType.objects.bulk_create(
            [
                PurchaseOrderType(purchase_order=po, order_type=ot)
                for ot in data["order_types"]
            ]
        )

        return Response(
            {
                "purchase_order_id": po.id,
                "message": "Step 1 completed",
                "rfq_count": len(data["rfq_ids"]),
                "order_types": data["order_types"],
            },
            status=status.HTTP_201_CREATED,
        )


# ─────────────────────────────────────────────────────────────
# STEP 2 — GET (NEW: populate the Step 2 form)
# ─────────────────────────────────────────────────────────────
class Step2GetAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, po_id):
        po = get_object_or_404(
            PurchaseOrder.objects.prefetch_related("order_types"),
            id=po_id,
        )

        # ── Selected Order Types (Image 6) ──────────────────
        order_type_map = {
            "bom": "Items (BOM Parts)",
            "component": "Components (Enclosure, Battery, etc.)",
            "service": "Services (Assembly, Quality Check, etc.)",
        }
        selected_order_types = [
            order_type_map.get(ot.order_type, ot.order_type)
            for ot in po.order_types.all()
        ]

        # ── RFQ IDs stored in po.rfq_id (comma-separated) ──
        rfq_id_list = [
            int(i.strip()) for i in po.rfq_id.split(",") if i.strip().isdigit()
        ]

        rfqs = RequestForQuote.objects.filter(id__in=rfq_id_list).prefetch_related(
            "selections",
            "quotations__vendor",
        )

        # ── Available Vendors summary (Images 11-12) ────────
        # Collect all vendors who have quoted on these RFQs
        vendor_totals = {}
        for rfq in rfqs:
            for q in rfq.quotations.filter(
                status__in=["quoted", "accepted"]
            ).select_related("vendor"):
                if q.quotation_rate is None:
                    continue
                vid = q.vendor.id
                if vid not in vendor_totals:
                    vendor_totals[vid] = {
                        "vendor_id": q.vendor.id,
                        "vendor_name": q.vendor.name,
                        "vendor_code": f"VND{q.vendor.id:03d}",
                        "total_price": Decimal("0.00"),
                    }
                vendor_totals[vid]["total_price"] += q.quotation_rate

        available_vendors = list(vendor_totals.values())

        # ── Build response ───────────────────────────────────
        rfq_items_data = RFQCardSerializer(rfqs, many=True).data

        return Response(
            {
                "purchase_order_id": po.id,
                "buyer_name": po.buyer_name,
                "order_id": po.order_id,
                "assembly_type": po.assembly_type,
                "selected_order_types": selected_order_types,
                "rfq_items_label": f"RFQ Items - {po.buyer_name} ({len(rfq_id_list)} RFQ{'s' if len(rfq_id_list) > 1 else ''})",
                "rfq_items": rfq_items_data,
                "available_vendors": available_vendors,
            }
        )


# ─────────────────────────────────────────────────────────────
# STEP 2 — POST (UPDATED — no model change)
# ─────────────────────────────────────────────────────────────
class Step2APIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        po = get_object_or_404(PurchaseOrder, id=request.data.get("purchase_order_id"))

        serializer = PurchaseStep2Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        po.wastage_percentage = data["wastage_percentage"]
        po.selected_vendor_id = data["selected_vendor_id"]
        po.delivery_date = data["delivery_date"]
        po.payment_terms = data["payment_terms"]
        po.save(
            update_fields=[
                "wastage_percentage",
                "selected_vendor_id",
                "delivery_date",
                "payment_terms",
            ]
        )

        # Replace items
        po.items.all().delete()
        PurchaseOrderItem.objects.bulk_create(
            [PurchaseOrderItem(purchase_order=po, **item) for item in data["items"]],
            batch_size=500,
        )

        return Response(
            {
                "message": "Purchase Order created successfully",
                "purchase_order_id": po.id,
                "items_count": len(data["items"]),
            },
            status=status.HTTP_201_CREATED,
        )


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


class AssemblyTypeDropdown(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": "pcb", "label": "PCB Assembly"},
                {"key": "device", "label": "Device Assembly"},
            ]
        )


class PaymentTermsDropdown(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [{"key": k, "label": v} for k, v in PurchaseOrder.PAYMENT_TERMS_CHOICES]
        )


# MATERIAL RECEIPT NOTE (MRN)
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


class PurchaseOrderItemsAPIView(APIView):
    """Retrieve line items for a purchase order."""

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


# DISPATCH WORKFLOW
class DispatchStep1APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DispatchStep1Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dispatch = Dispatch.objects.create(
            **serializer.validated_data, created_by=request.user
        )

        return Response({"dispatch_id": dispatch.id}, status=status.HTTP_201_CREATED)


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


class DispatchStep3APIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, dispatch_id):
        dispatch = get_object_or_404(Dispatch, id=dispatch_id)

        if not all([dispatch.product, dispatch.batch, dispatch.dispatch_quantity]):
            return Response(
                {"error": "Step-2 (Stock Verification) must be completed first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = DispatchStep3Serializer(dispatch, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Dispatch details saved"})


class DispatchStep4APIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, dispatch_id):
        dispatch = get_object_or_404(Dispatch, id=dispatch_id)

        if not dispatch.dispatch_date:
            return Response(
                {"error": "Step-3 (Dispatch Details) must be completed first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DispatchStep4Serializer(dispatch, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if not dispatch.stock_deducted:
            batch = OrderBatch.objects.select_for_update().get(pk=dispatch.batch_id)
            if dispatch.dispatch_quantity > batch.available_stock:
                return Response(
                    {
                        "error": (
                            f"Insufficient stock. "
                            f"Available: {batch.available_stock}, "
                            f"Requested: {dispatch.dispatch_quantity}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            batch.available_stock -= dispatch.dispatch_quantity
            batch.save(update_fields=["available_stock"])
            dispatch.refresh_from_db()
            dispatch.stock_deducted = True

        dispatch.status = "completed"
        dispatch.save(update_fields=["status", "stock_deducted"])

        return Response(
            {
                "message": "Dispatch completed successfully.",
                "dispatch_id": dispatch.id,
                "remaining_stock": (
                    batch.available_stock if not dispatch.stock_deducted else None
                ),
            },
            status=status.HTTP_200_OK,
        )


class SalesOrderDropdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"id": so.id, "label": f"SO-{so.id}"}
                for so in SalesOrder.objects.all().order_by("-id")
            ]
        )


class DispatchOrderTypeDropdownAPIView(APIView):
    """List dispatch order types."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"key": "distributor", "label": "Distributor"},
                {"key": "dealer", "label": "Dealer"},
                {"key": "b2c", "label": "B2C Customer"},
            ]
        )


class DispatchProductDropdownAPIView(APIView):
    """List order products for dispatch selection."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            [
                {"id": p.id, "label": p.name}
                for p in OrderProduct.objects.all().order_by("name")
            ]
        )


class DispatchBatchDropdownAPIView(APIView):
    """List product batches for dispatch by product."""

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


class ReturnReasonDropdownAPIView(APIView):
    """List return reasons for post-dispatch returns."""

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


class AccountRegistrationCreateAPIView(APIView):
    """Register account management users."""

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


class QCInspectorViewSet(DeleteResponseMixin, ModelViewSet):

    queryset = QCInspectorRegistration.objects.select_related(
        "state", "district"
    ).order_by("-created_at")

    serializer_class = QCInspectorRegistrationSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    delete_object_name = "qc_inspector"
    delete_display_field = "qc_inspector_name"

    # CREATE
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inspector = serializer.save()
        return Response(
            {
                "success": True,
                "message": "QC Inspector registered successfully",
                "qc_inspector_id": inspector.id,
                "name": inspector.qc_inspector_name,
            },
            status=status.HTTP_201_CREATED,
        )

    # UPDATE (PUT / PATCH safe)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        inspector = serializer.save()
        return Response(
            {
                "success": True,
                "message": "QC Inspector updated successfully",
                "qc_inspector_id": inspector.id,
                "name": inspector.qc_inspector_name,
            }
        )


class PurchaseDepartmentViewSet(DeleteResponseMixin, ModelViewSet):
    queryset = PurchaseDepartmentRegistration.objects.select_related(
        "state", "district"
    ).order_by("-created_at")

    serializer_class = PurchaseDepartmentRegistrationSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    delete_object_name = "purchase_department"
    delete_display_field = "purchase_department_name"

    # CREATE
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        department = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Purchase Department registered successfully",
                "purchase_department_id": department.id,
                "name": department.purchase_department_name,
            },
            status=status.HTTP_201_CREATED,
        )

    # UPDATE (PUT / PATCH safe)
    def update(self, request, *args, **kwargs):

        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(raise_exception=True)

        department = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Purchase Department updated successfully",
                "purchase_department_id": department.id,
                "name": department.purchase_department_name,
            }
        )


class StoreManagerViewSet(DeleteResponseMixin, ModelViewSet):

    queryset = StoreManagerRegistration.objects.select_related(
        "state", "district"
    ).order_by("-created_at")

    serializer_class = StoreManagerRegistrationSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    delete_object_name = "store_manager"
    delete_display_field = "store_manager_name"

    # CREATE
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        manager = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Store Manager registered successfully",
                "store_manager_id": manager.id,
                "name": manager.store_manager_name,
            },
            status=status.HTTP_201_CREATED,
        )

    # UPDATE (PUT / PATCH)
    def update(self, request, *args, **kwargs):

        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        serializer.is_valid(raise_exception=True)

        manager = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Store Manager updated successfully",
                "store_manager_id": manager.id,
                "name": manager.store_manager_name,
            }
        )


class RepairTechnicianViewSet(DeleteResponseMixin, ModelViewSet):

    queryset = RepairTechnicianRegistration.objects.select_related(
        "state", "district"
    ).order_by("-created_at")

    serializer_class = RepairTechnicianRegistrationSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    delete_object_name = "repair_technician"
    delete_display_field = "repair_technician_name"

    # CREATE
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        technician = serializer.save()

        return Response(
            {
                "success": True,
                "message": "Repair Technician registered successfully",
                "repair_technician_id": technician.id,
                "name": technician.repair_technician_name,
            },
            status=status.HTTP_201_CREATED,
        )

    # UPDATE (PUT / PATCH)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        technician = serializer.save()
        return Response(
            {
                "success": True,
                "message": "Repair Technician updated successfully",
                "repair_technician_id": technician.id,
                "name": technician.repair_technician_name,
            }
        )


# STORE TRANSFERS
class StoreTransferViewSet(ModelViewSet):
    """Manage store transfers with filtering and search capabilities."""

    queryset = StoreTransfer.objects.select_related(
        "product", "category", "vendor", "created_by"
    ).all()
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = [
        "product_name",
        "batch_number",
        "vendor__name",
        "category__name",
        "transfer_id",
        "mrn_number",
    ]
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return StoreTransferDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return StoreTransferCreateUpdateSerializer
        return StoreTransferListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        dispatch_status = self.request.query_params.get("dispatch_status")
        if dispatch_status:
            queryset = queryset.filter(dispatch_status=dispatch_status)

        category_id = self.request.query_params.get("category_id")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        transfer_date_from = self.request.query_params.get("transfer_date_from")
        if transfer_date_from:
            queryset = queryset.filter(transfer_date__gte=transfer_date_from)

        transfer_date_to = self.request.query_params.get("transfer_date_to")
        if transfer_date_to:
            queryset = queryset.filter(transfer_date__lte=transfer_date_to)

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"])
    def filter_options(self, request):
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


class ProductCategoryViewSet(ModelViewSet):
    """Manage product categories."""

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


class CreditNoteViewSet(ModelViewSet):
    """Manage credit notes with status filtering and summary."""

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


# ACCOUNT MANAGEMENT


class AccountManagementDashboardAPIView(APIView):
    """Dashboard for account management with debit and credit note summaries."""

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


class DebitNoteReasonsAPIView(APIView):
    """List available debit note reasons."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        reasons = [
            {"key": choice[0], "label": choice[1]}
            for choice in DebitNote.REASON_CHOICES
        ]
        return Response(reasons)


class CreditNoteReasonsAPIView(APIView):
    """List available credit note reasons."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        reasons = [
            {"key": choice[0], "label": choice[1]}
            for choice in CreditNote.REASON_CHOICES
        ]
        return Response(reasons)


class NoteStatusChoicesAPIView(APIView):
    """List available note status choices."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        statuses = [
            {"key": choice[0], "label": choice[1]}
            for choice in DebitNote.STATUS_CHOICES
        ]
        return Response(statuses)


# VENDOR MANAGEMENT
class ReturnRequestViewSet(viewsets.ModelViewSet):
    """Manage return requests with filtering, search, and status tracking."""

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
        queryset = self.get_queryset()
        totals = queryset.aggregate(
            total_failed=Sum("failed_qty"),
            total_repaired=Sum("repaired_qty"),
            total_rejected=Sum("rejected_qty"),
            total_pending=Sum("repair_pending"),
        )

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
        repair_record = self.get_object()

        repaired_qty = request.data.get("repaired_qty", repair_record.repaired_qty)
        rejected_qty = request.data.get("rejected_qty", repair_record.rejected_qty)
        repair_pending = request.data.get(
            "repair_pending", repair_record.repair_pending
        )

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


class RejectedItemViewSet(viewsets.ModelViewSet):
    """Manage rejected items with statistics and vendor grouping."""

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


# SELF ORDERS
class SelfOrderCreateAPIView(APIView):
    """Create a self order for the authenticated user."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SelfOrderSerializer(data=request.data)

        if serializer.is_valid():
            try:
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
    """List all self orders for the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
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


# ======================= QUOTATION APIs ==================================
# ----------- Quotation Create API -----------
class QuotationCreateAPIView(APIView):
    """Create a quotation from an RFQ."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = QuotationCreateSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            quotation = serializer.save()
            return Response(
                {
                    "message": "Quotation created successfully.",
                    "quotation_id": quotation.id,
                    "quotation_number": quotation.quotation_number,
                    "data": QuotationDetailSerializer(quotation).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class QuotationListAPIView(APIView):
    """List quotations with search and status filtering."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Quotation.objects.all()

        search_query = request.query_params.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(vendor__name__icontains=search_query)
                | Q(quotation_number__icontains=search_query)
                | Q(customer_name__icontains=search_query)
            )

        status_filter = request.query_params.get("status", "").strip()
        if status_filter and status_filter != "all":
            queryset = queryset.filter(status=status_filter)

        total_count = Quotation.objects.count()
        pending_count = Quotation.objects.filter(status="pending").count()
        approved_count = Quotation.objects.filter(status="approved").count()
        rejected_count = Quotation.objects.filter(status="rejected").count()

        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))
        start = (page - 1) * limit
        end = start + limit

        quotations = queryset[start:end]

        return Response(
            {
                "count": {
                    "total": total_count,
                    "found": queryset.count(),
                    "pending": pending_count,
                    "approved": approved_count,
                    "rejected": rejected_count,
                },
                "data": QuotationListSerializer(quotations, many=True).data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_pages": (queryset.count() + limit - 1) // limit,
                },
            },
            status=status.HTTP_200_OK,
        )


class QuotationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, quotation_id):
        try:
            quotation = Quotation.objects.get(id=quotation_id)
        except Quotation.DoesNotExist:
            return Response(
                {"error": "Quotation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            QuotationDetailSerializer(quotation).data,
            status=status.HTTP_200_OK,
        )


class QuotationApproveRejectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, quotation_id):
        try:
            quotation = Quotation.objects.get(id=quotation_id)
        except Quotation.DoesNotExist:
            return Response(
                {"error": "Quotation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if quotation.status != "pending":
            return Response(
                {"error": f"Cannot change status of a {quotation.status} quotation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = QuotationApproveRejectSerializer(data=request.data)

        if serializer.is_valid():
            new_status = serializer.validated_data["status"]
            quotation.status = new_status
            quotation.save()

            return Response(
                {
                    "message": f"Quotation {new_status} successfully.",
                    "data": QuotationDetailSerializer(quotation).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class DeviceInventoryViewSet(DeleteResponseMixin, ModelViewSet):
    serializer_class = DeviceInventorySerializer
    permission_classes = [IsAuthenticated]
    delete_object_name = "device"
    delete_display_field = "esn"
    queryset = DeviceInventory.objects.select_related(
        "device", "device__info"
    ).order_by("-created_at")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    search_fields = [
        "esn",
        "imei",
        "iccid",
        "device__info__make",
        "device__info__model",
    ]

    ordering_fields = [
        "created_at",
        "esn",
        "imei",
    ]

    filterset_fields = [
        "stock_status",
        "esim_status",
    ]

    @action(detail=False, methods=["get"], url_path="export/csv")
    def export_csv(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="device_report.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Device Name",
                "Device Model",
                "ESN",
                "IMEI",
                "ICCID",
                "Telecom Provider 1",
                "Telecom Provider 2",
                "MSISDN 1",
                "MSISDN 2",
                "eSIM Status",
                "eSIM Validity",
                "Stock Status",
                "Assigned To",
                "Remarks",
                "Created At",
            ]
        )

        for obj in queryset:
            info = getattr(obj.device, "info", None)
            writer.writerow(
                [
                    getattr(info, "make", ""),
                    getattr(info, "model", ""),
                    obj.esn,
                    obj.imei,
                    obj.iccid,
                    obj.telecom_provider_1,
                    obj.telecom_provider_2,
                    obj.msisdn_1,
                    obj.msisdn_2,
                    obj.esim_status,
                    obj.esim_validity,
                    obj.stock_status,
                    obj.assigned_to,
                    obj.remarks,
                    obj.created_at.strftime("%Y-%m-%d"),
                ]
            )

        return response

    @action(detail=False, methods=["get"], url_path="export/excel")
    def export_excel(self, request):

        queryset = self.filter_queryset(self.get_queryset())

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Device Report"

        headers = [
            "Device Name",
            "Device Model",
            "ESN",
            "IMEI",
            "ICCID",
            "Telecom Provider 1",
            "Telecom Provider 2",
            "MSISDN 1",
            "MSISDN 2",
            "eSIM Status",
            "eSIM Validity",
            "Stock Status",
            "Assigned To",
            "Remarks",
            "Created At",
        ]

        sheet.append(headers)

        for obj in queryset:

            info = getattr(obj.device, "info", None)

            sheet.append(
                [
                    getattr(info, "make", ""),
                    getattr(info, "model", ""),
                    obj.esn,
                    obj.imei,
                    obj.iccid,
                    obj.telecom_provider_1,
                    obj.telecom_provider_2,
                    obj.msisdn_1,
                    obj.msisdn_2,
                    obj.esim_status,
                    str(obj.esim_validity) if obj.esim_validity else "",
                    obj.stock_status,
                    obj.assigned_to,
                    obj.remarks,
                    obj.created_at.strftime("%Y-%m-%d"),
                ]
            )

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        response["Content-Disposition"] = 'attachment; filename="device_report.xlsx"'

        workbook.save(response)

        return response


class B2BOrderViewSet(DeleteResponseMixin, ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = B2BOrder.objects.select_related(
        "purchase_order",
        "supply_state",
        "created_by",
    ).order_by("-created_at")

    # Required by DeleteResponseMixin
    delete_object_name = "b2b_order"
    delete_display_field = None

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return B2BOrderReadSerializer
        return B2BOrderCreateSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    def get_display_value(self, instance):
        return f"B2BOrder-{instance.id}"
