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

from .serializers import *
from .models import *



# ---------------- Login API ----------------
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

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



