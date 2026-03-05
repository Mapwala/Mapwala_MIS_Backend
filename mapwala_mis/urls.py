# mapwala_mis/urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    LoginAPIView,
    B2CCustomerRegistrationAPIView,
    B2BPartnerRegistrationAPIView,
    DistributorRegistrationAPIView,
    DealerRegistrationAPIView,
    AccountManagementDashboardAPIView,
    DebitNoteReasonsAPIView,
    CreditNoteReasonsAPIView,
    NoteStatusChoicesAPIView,
    DeviceStep1APIView,
    DeviceStep2APIView,
    DeviceStep3APIView,
    DeviceStep4APIView,
    DeviceStep5APIView,
    DeviceStep6APIView,
    DeviceStep7APIView,
    DeviceStep8APIView,
    DeviceStep9APIView,
    DeviceAccessoryAPIView,
    ProformaInvoiceCreateAPIView,
    OrderEntryStep1APIView,
    OrderEntryStep2APIView,
    OrderProductListAPIView,
    OrderBatchListAPIView,
    SalesOrderCreateAPIView,
    ProductionOrderCreateAPIView,
    ProductDropdownAPIView,
    ProductCreateAPIView,
    OrderProductDropdownAPIView,
    SupplierVendorDropdownAPIView,
    ProductCategoryDropdownAPIView,
    CustomerTypeDropdownAPIView,
    PaymentTermsDropdownAPIView,
    OrderPriorityDropdownAPIView,
    RFQListAPIView,
    RFQDetailAPIView,
    RFQStep1APIView,
    RFQStep2APIView,
    RFQStep3APIView,
    QuoteTypeDropdownAPIView,
    AssemblyTypeDropdownAPIView,
    SRNDropdownAPIView,
    VendorDropdownAPIView,
    Step1APIView,
    Step2APIView,
    MRNCreateAPIView,
    PurchaseOrderDropdown,
    InwardTypeDropdown,
    PurchaseOrderItemsAPIView,
    PostDispatchReturnCreateAPIView,
    ReturnTypeDropdownAPIView,
    ReturnReasonDropdownAPIView,
    DispatchStep1APIView,
    DispatchStep2APIView,
    DispatchStep3APIView,
    DispatchStep4APIView,
    SalesOrderDropdownAPIView,
    DispatchOrderTypeDropdownAPIView,
    DispatchProductDropdownAPIView,
    DispatchBatchDropdownAPIView,
    StateDropdownAPIView,
    DistrictDropdownAPIView,
    AccountRegistrationCreateAPIView,
    QCInspectorRegistrationCreateAPIView,
    PurchaseDepartmentRegistrationCreateAPIView,
    StoreManagerRegistrationCreateAPIView,
    RepairTechnicianRegistrationCreateAPIView,
    SelfOrderCreateAPIView,
    SelfOrderListAPIView,
    SelfOrderDetailAPIView,
    SelfOrderDeviceDropdownAPIView,
    GSTRateDropdownAPIView,
    QuotationCreateAPIView,
    QuotationListAPIView,
    QuotationDetailAPIView,
    QuotationApproveRejectAPIView,
    state_of_supply_dropdown,
    unit_of_measure_dropdown,
    StateViewSet,
    DistrictViewSet,
    ParentCompanyViewSet,
    VendorViewSet,
    StoreTransferViewSet,
    ProductCategoryViewSet,
    DebitNoteViewSet,
    CreditNoteViewSet,
    ReturnRequestViewSet,
    RepairRecordViewSet,
    RejectedItemViewSet,
    DeviceViewSet,
    ManufacturerViewSet,
    LinkedToChoicesAPIView,
)


router = DefaultRouter()

# Master data
router.register("states", StateViewSet, basename="states")
router.register("districts", DistrictViewSet, basename="districts")
router.register("parent-companies", ParentCompanyViewSet, basename="parent-companies")
router.register("vendors", VendorViewSet, basename="vendors")
router.register("store-transfers", StoreTransferViewSet, basename="store-transfers")
router.register("product-categories", ProductCategoryViewSet, basename="product-categories")

router.register("manufacturers", ManufacturerViewSet, basename="manufacturers")

# Notes
router.register("debit-notes", DebitNoteViewSet, basename="debit-notes")
router.register("credit-notes", CreditNoteViewSet, basename="credit-notes")

# Quality & returns
router.register("return-requests", ReturnRequestViewSet, basename="return-request")
router.register("repair-records", RepairRecordViewSet, basename="repair-record")
router.register("rejected-items", RejectedItemViewSet, basename="rejected-item")

# Devices
router.register("devices", DeviceViewSet, basename="devices")


urlpatterns = [
    # Auth & registration
    path("auth/login/", LoginAPIView.as_view(), name="login"),
    path("b2c/register/", B2CCustomerRegistrationAPIView.as_view()),
    path("b2b/register/", B2BPartnerRegistrationAPIView.as_view()),
    path("dropdowns/linked-to/", LinkedToChoicesAPIView.as_view()),
    path("distributor/register/", DistributorRegistrationAPIView.as_view()),
    path("dealer/register/", DealerRegistrationAPIView.as_view()),
    # Product Dropdowns
    path("dropdowns/products/",ProductDropdownAPIView.as_view(),name="product-dropdown"),
    path("products/", ProductCreateAPIView.as_view(), name="product-create"),
    # Account management
    path("account-management/dashboard/", AccountManagementDashboardAPIView.as_view()),
    path("debit-notes/reasons/", DebitNoteReasonsAPIView.as_view()),
    path("credit-notes/reasons/", CreditNoteReasonsAPIView.as_view()),
    path("notes/statuses/", NoteStatusChoicesAPIView.as_view()),
    # Device creation (steps)
    path("devices/dropdowns/unit-of-measure/",unit_of_measure_dropdown,name="unit-of-measure-dropdown"),
    path("devices/dropdowns/state-of-supply/",state_of_supply_dropdown,name="state-of-supply-dropdown"),
    path("devices/step-1/", DeviceStep1APIView.as_view()),
    path("devices/step-2/", DeviceStep2APIView.as_view()),
    path("devices/step-3/", DeviceStep3APIView.as_view()),
    path("devices/step-4/", DeviceStep4APIView.as_view()),
    path("devices/step-5/", DeviceStep5APIView.as_view()),
    path("devices/step-6/", DeviceStep6APIView.as_view()),
    path("devices/step-7/", DeviceStep7APIView.as_view()),
    path("devices/step-8/", DeviceStep8APIView.as_view()),
    path("devices/step-9/", DeviceStep9APIView.as_view()),
    path("devices/step-10/", DeviceAccessoryAPIView.as_view()),
    # Proforma invoice
    path("pi/create/", ProformaInvoiceCreateAPIView.as_view()),
    # Order entry
    path("order-entry/step-1/", OrderEntryStep1APIView.as_view()),
    path("order-entry/step-2/", OrderEntryStep2APIView.as_view()),
    path("order-products/", OrderProductListAPIView.as_view()),
    path("order-batches/", OrderBatchListAPIView.as_view()),
    path("sales-orders/create/", SalesOrderCreateAPIView.as_view()),
    path("production-orders/add-to-stock/", ProductionOrderCreateAPIView.as_view()),
    # Dropdowns
    path("dropdowns/order-products/",OrderProductDropdownAPIView.as_view(),name="order-product-dropdown"),
    path("dropdowns/suppliers/", SupplierVendorDropdownAPIView.as_view()),
    path("dropdowns/product-categories/", ProductCategoryDropdownAPIView.as_view()),
    path("dropdowns/customer-types/", CustomerTypeDropdownAPIView.as_view()),
    path("dropdowns/payment-terms/", PaymentTermsDropdownAPIView.as_view()),
    path("dropdowns/order-priority/", OrderPriorityDropdownAPIView.as_view()),
    # RFQ
    path("rfq/", RFQListAPIView.as_view()),
    path("rfq/<int:rfq_id>/", RFQDetailAPIView.as_view()),
    path("rfq/step-1/", RFQStep1APIView.as_view()),
    path("rfq/step-2/", RFQStep2APIView.as_view()),
    path("rfq/step-3/", RFQStep3APIView.as_view()),
    path("dropdowns/quote-types/", QuoteTypeDropdownAPIView.as_view()),
    path("dropdowns/assembly-types/", AssemblyTypeDropdownAPIView.as_view()),
    path("dropdowns/srn/", SRNDropdownAPIView.as_view()),
    path("dropdowns/vendors/", VendorDropdownAPIView.as_view()),
    # Purchase & MRN
    path("purchase/step-1/", Step1APIView.as_view()),
    path("purchase/step-2/", Step2APIView.as_view()),
    path("mrn/create/", MRNCreateAPIView.as_view()),
    path("dropdowns/purchase-orders/", PurchaseOrderDropdown.as_view()),
    path("dropdowns/inward-types/", InwardTypeDropdown.as_view()),
    path("purchase/<int:po_id>/items/", PurchaseOrderItemsAPIView.as_view()),
    # Post-dispatch returns
    path("returns/post-dispatch/create/", PostDispatchReturnCreateAPIView.as_view()),
    path("dropdowns/return-types/", ReturnTypeDropdownAPIView.as_view()),
    path("dropdowns/return-reasons/", ReturnReasonDropdownAPIView.as_view()),
    # Dispatch
    path("dispatch/step-1/", DispatchStep1APIView.as_view()),
    path("dispatch/step-2/<int:dispatch_id>/", DispatchStep2APIView.as_view()),
    path("dispatch/step-3/<int:dispatch_id>/", DispatchStep3APIView.as_view()),
    path("dispatch/step-4/<int:dispatch_id>/", DispatchStep4APIView.as_view()),
    path("dropdowns/sales-orders/", SalesOrderDropdownAPIView.as_view()),
    path("dropdowns/dispatch-order-types/", DispatchOrderTypeDropdownAPIView.as_view()),
    path("dropdowns/dispatch-products/", DispatchProductDropdownAPIView.as_view()),
    path("dropdowns/dispatch-batches/", DispatchBatchDropdownAPIView.as_view()),
    # Module registrations
    path("dropdowns/states/", StateDropdownAPIView.as_view()),
    path("dropdowns/districts/", DistrictDropdownAPIView.as_view()),
    path("account/register/", AccountRegistrationCreateAPIView.as_view()),
    path("qc-inspectors/register/", QCInspectorRegistrationCreateAPIView.as_view()),
    path(
        "purchase-departments/register/",
        PurchaseDepartmentRegistrationCreateAPIView.as_view(),
    ),
    path("store-managers/register/", StoreManagerRegistrationCreateAPIView.as_view()),
    path(
        "repair-technicians/register/",
        RepairTechnicianRegistrationCreateAPIView.as_view(),
    ),
    # Self orders
    path("self-orders/create/", SelfOrderCreateAPIView.as_view()),
    path("self-orders/", SelfOrderListAPIView.as_view()),
    path("self-orders/<int:pk>/", SelfOrderDetailAPIView.as_view()),
    path("self-orders/devices/", SelfOrderDeviceDropdownAPIView.as_view()),
    path("self-orders/gst-rates/", GSTRateDropdownAPIView.as_view()),
    # Quotations
    path("quotations/create/", QuotationCreateAPIView.as_view()),
    path("quotations/", QuotationListAPIView.as_view()),
    path("quotations/<int:quotation_id>/", QuotationDetailAPIView.as_view()),
    path(
        "quotations/<int:quotation_id>/approve-reject/",
        QuotationApproveRejectAPIView.as_view(),
    ),
]

urlpatterns += router.urls
